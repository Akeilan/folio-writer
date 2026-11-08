//! 3-D models in the document (W4-01): a glTF binary kept as its own part with a picture of the
//! model's current view beside it, written the way Word 2019 writes one — an mc:AlternateContent
//! whose Choice holds am3d:model3d and whose Fallback holds the picture. Word opens it as a model
//! that can be turned; everything else, Page included, draws the picture.
//!
//! Reading and turning the model itself is Python's job (app/folio/model3d.py, shared with Show);
//! this module is only the part, the relationships and the XML.

use super::{Editor, Pos};
use crate::xml::{NodeId, XmlDoc};

const NS_WP: &str = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing";
const NS_A: &str = "http://schemas.openxmlformats.org/drawingml/2006/main";
const NS_PIC: &str = "http://schemas.openxmlformats.org/drawingml/2006/picture";
const NS_R: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const NS_MC: &str = "http://schemas.openxmlformats.org/markup-compatibility/2006";
pub const NS_AM3D: &str = "http://schemas.microsoft.com/office/drawing/2017/model3d";
const REL_MODEL: &str = "http://schemas.microsoft.com/office/2017/06/relationships/model3d";
const REL_IMAGE: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image";
const CT_GLB: &str = "model/gltf-binary";

fn emu(pt: f64) -> String {
    ((pt * 12700.0).round() as i64).to_string()
}

/// 60000ths of a degree, as DrawingML counts angles.
fn deg(v: f64) -> i64 {
    (v * 60000.0).round() as i64
}

impl Editor {
    /// Insert a 3-D model in line at the caret: `glb` the glTF binary, `png` a picture of it
    /// turned `rot` degrees, `w` x `h` points. Returns the model's part name.
    pub fn insert_model3d(&mut self, glb: &[u8], png: &[u8], w: f64, h: f64, rot: (f64, f64, f64), name: &str) -> Option<String> {
        if glb.len() < 12 || &glb[..4] != b"glTF" || png.is_empty() {
            return None;
        }
        let main = self.doc.main.clone();
        let mut n = 1;
        while self.doc.pkg.has(&format!("word/media/model{n}.glb")) {
            n += 1;
        }
        let part = format!("word/media/model{n}.glb");
        self.doc.pkg.put_raw(&part, glb.to_vec());
        self.doc.pkg.ensure_default("glb", CT_GLB);
        let target = crate::package::Package::relative_target(&main, &part);
        let rid_m = self.doc.pkg.add_rel(&main, REL_MODEL, &target);
        self.doc.images.insert(rid_m.clone(), crate::pictures::ImageData { part: part.clone(), bytes: std::sync::Arc::new(glb.to_vec()) });
        // the picture of the model as it now stands
        let mut k = 1;
        while self.doc.pkg.has(&format!("word/media/image{k}.png")) {
            k += 1;
        }
        let img = format!("word/media/image{k}.png");
        self.doc.pkg.put_raw(&img, png.to_vec());
        self.doc.pkg.ensure_default("png", "image/png");
        let itarget = crate::package::Package::relative_target(&main, &img);
        let rid_i = self.doc.pkg.add_rel(&main, REL_IMAGE, &itarget);
        self.doc.images.insert(rid_i.clone(), crate::pictures::ImageData { part: img, bytes: std::sync::Arc::new(png.to_vec()) });
        let id = self.next_docpr_id();
        let descr = crate::xml::attr_escaped(name);
        let xml = model_xml(id, &descr, &rid_m, &rid_i, w, h, rot);
        let Ok(tmp) = XmlDoc::parse(xml.as_bytes()) else { return None };
        // the parsed root may be the element itself or a document holding it
        let src = if tmp.is(tmp.root, "mc:AlternateContent") {
            tmp.root
        } else {
            tmp.elements(tmp.root).find(|n| tmp.is(*n, "mc:AlternateContent")).unwrap_or(tmp.root)
        };
        self.begin();
        self.delete_selection();
        let p = self.caret.para;
        let off = self.caret.off;
        let (parent, idx, like) = self.split_runs_at(p, off);
        let run = self.new_run(p, like, &[]);
        let alt = self.doc.dom.import_node(&tmp, src);
        self.doc.dom.append(run, alt);
        self.doc.dom.insert(parent, idx, run);
        self.caret = Pos { para: p, off: off + 1 };
        self.anchor = self.caret;
        self.commit("Insert 3D Model", false);
        // the drawing the document shows is the Choice's: that is the object now selected
        self.sel_obj = self.doc.dom.child(alt, "mc:Choice").and_then(|c| self.doc.dom.child(c, "w:drawing")).or(Some(alt));
        Some(part)
    }

    /// For the selected object: (the model's part, its rotation in degrees), or None if the
    /// selection is not a 3-D model.
    pub fn selected_model3d(&mut self) -> Option<(String, (f64, f64, f64))> {
        let obj = self.sel_obj?;
        let (rid, rot) = {
            let dom = &self.doc.dom;
            let m = find_model(dom, alt_of(dom, obj))?;
            let rid = dom.attr(m, "r:embed")?.to_string();
            let rot = dom.child(m, "am3d:trans").and_then(|t| dom.child(t, "am3d:rot")).map(|r| {
                let g = |k: &str| dom.attr(r, k).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) / 60000.0;
                (g("ax"), g("ay"), g("az"))
            });
            (rid, rot.unwrap_or((0.0, 0.0, 0.0)))
        };
        let part = self.rel_part(&rid)?;
        Some((part, rot))
    }

    /// The part an r:embed on the main document points at. A model is not related as an image, so
    /// it is not in the loaded pictures: the relationship is the way to it.
    fn rel_part(&mut self, rid: &str) -> Option<String> {
        if let Some(d) = self.doc.images.get(rid) {
            return Some(d.part.clone());
        }
        let main = self.doc.main.clone();
        let target = self.doc.pkg.rels(&main).into_iter().find(|r| r.id == rid)?.target;
        if target.starts_with("http") || target.contains("://") {
            return None;
        }
        Some(crate::package::Package::resolve(&main, &target))
    }

    /// The selected model's glTF binary, so it can be drawn again from a different angle after
    /// the document has been closed and opened.
    pub fn model3d_glb(&mut self) -> Option<Vec<u8>> {
        let obj = self.sel_obj?;
        let rid = {
            let dom = &self.doc.dom;
            let m = find_model(dom, alt_of(dom, obj))?;
            dom.attr(m, "r:embed")?.to_string()
        };
        if let Some(d) = self.doc.images.get(&rid) {
            if d.bytes.len() >= 12 && &d.bytes[..4] == b"glTF" {
                return Some(d.bytes.to_vec());
            }
        }
        let part = self.rel_part(&rid)?;
        self.doc.pkg.raw(&part).map(|b| b.to_vec())
    }

    /// Turn the selected model: a new picture of it, and the rotation to record. The picture goes
    /// into both branches, so Word and every other reader show the same view.
    pub fn set_model3d(&mut self, png: &[u8], rot: (f64, f64, f64)) -> bool {
        let Some(obj) = self.sel_obj else { return false };
        if find_model(&self.doc.dom, alt_of(&self.doc.dom, obj)).is_none() {
            return false;
        }
        let rid = if png.is_empty() {
            None
        } else {
            let main = self.doc.main.clone();
            let mut n = 1;
            while self.doc.pkg.has(&format!("word/media/image{n}.png")) {
                n += 1;
            }
            let part = format!("word/media/image{n}.png");
            self.doc.pkg.put_raw(&part, png.to_vec());
            self.doc.pkg.ensure_default("png", "image/png");
            let target = crate::package::Package::relative_target(&main, &part);
            let r = self.doc.pkg.add_rel(&main, REL_IMAGE, &target);
            self.doc.images.insert(r.clone(), crate::pictures::ImageData { part, bytes: std::sync::Arc::new(png.to_vec()) });
            Some(r)
        };
        // the drawing holds the model in one branch and the plain picture in the other: both show
        // the same view, so both blips move to the new picture
        let blips: Vec<NodeId> = {
            let dom = &self.doc.dom;
            let mut out = Vec::new();
            fn walk(dom: &XmlDoc, n: NodeId, depth: usize, out: &mut Vec<NodeId>) {
                if depth > 16 {
                    return;
                }
                if dom.is(n, "am3d:blip") || dom.is(n, "a:blip") {
                    out.push(n);
                }
                for &c in dom.children(n) {
                    walk(dom, c, depth + 1, out);
                }
            }
            walk(dom, alt_of(dom, obj), 0, &mut out);
            out
        };
        let rots: Vec<NodeId> = {
            let dom = &self.doc.dom;
            let mut out = Vec::new();
            fn walk(dom: &XmlDoc, n: NodeId, depth: usize, out: &mut Vec<NodeId>) {
                if depth > 16 {
                    return;
                }
                if dom.is(n, "am3d:rot") {
                    out.push(n);
                }
                for &c in dom.children(n) {
                    walk(dom, c, depth + 1, out);
                }
            }
            walk(dom, alt_of(dom, obj), 0, &mut out);
            out
        };
        self.begin();
        if let Some(r) = &rid {
            for b in blips {
                self.doc.dom.set_attr(b, "r:embed", r);
            }
        }
        for n in rots {
            for (k, v) in [("ax", rot.0), ("ay", rot.1), ("az", rot.2)] {
                self.doc.dom.set_attr(n, k, &deg(v).to_string());
            }
        }
        self.commit("Rotate 3D Model", false);
        true
    }
}

/// The mc:AlternateContent holding both branches of this drawing, or the drawing itself.
fn alt_of(dom: &XmlDoc, obj: NodeId) -> NodeId {
    let mut n = obj;
    for _ in 0..3 {
        match dom.parent(n) {
            Some(p) if dom.is(p, "mc:Choice") || dom.is(p, "mc:Fallback") => n = p,
            Some(p) if dom.is(p, "mc:AlternateContent") => return p,
            _ => break,
        }
    }
    obj
}

fn find_model(dom: &XmlDoc, obj: NodeId) -> Option<NodeId> {
    fn walk(dom: &XmlDoc, n: NodeId, depth: usize) -> Option<NodeId> {
        if depth > 12 {
            return None;
        }
        if dom.is(n, "am3d:model3d") {
            return Some(n);
        }
        for &c in dom.children(n) {
            if let Some(f) = walk(dom, c, depth + 1) {
                return Some(f);
            }
        }
        None
    }
    walk(dom, obj, 0)
}

/// A 3-D model as Word 2019 writes one: an mc:AlternateContent in the run, its Choice a drawing
/// of the model and its Fallback a drawing of the picture, so a reader takes whichever it knows.
#[allow(clippy::too_many_arguments)]
fn model_xml(id: u32, descr: &str, rid_m: &str, rid_i: &str, w: f64, h: f64, rot: (f64, f64, f64)) -> String {
    let (cx, cy) = (emu(w), emu(h));
    let xf = format!("<a:off x=\"0\" y=\"0\"/><a:ext cx=\"{cx}\" cy=\"{cy}\"/>");
    let head = format!(
        "<wp:extent cx=\"{cx}\" cy=\"{cy}\"/><wp:effectExtent l=\"0\" t=\"0\" r=\"0\" b=\"0\"/>\
         <wp:docPr id=\"{id}\" name=\"3D Model {id}\" descr=\"{descr}\"/>\
         <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect=\"1\"/></wp:cNvGraphicFramePr>");
    let model = format!(
        "<w:drawing><wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">{head}\
         <a:graphic><a:graphicData uri=\"{am3d}\">\
         <am3d:model3d r:embed=\"{rid_m}\"><am3d:spPr><a:xfrm>{xf}</a:xfrm>\
         <a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></am3d:spPr>\
         <am3d:camera><am3d:pos x=\"0\" y=\"0\" z=\"51581090\"/><am3d:up dx=\"0\" dy=\"36000000\" dz=\"0\"/>\
         <am3d:lookAt x=\"0\" y=\"0\" z=\"0\"/><am3d:perspective fov=\"2700000\"/></am3d:camera>\
         <am3d:trans><am3d:meterPerModelUnit n=\"1\" d=\"1\"/><am3d:preTrans dx=\"0\" dy=\"0\" dz=\"0\"/>\
         <am3d:scale><am3d:sx n=\"1000000\" d=\"1000000\"/><am3d:sy n=\"1000000\" d=\"1000000\"/>\
         <am3d:sz n=\"1000000\" d=\"1000000\"/></am3d:scale>\
         <am3d:rot ax=\"{ax}\" ay=\"{ay}\" az=\"{az}\"/><am3d:postTrans dx=\"0\" dy=\"0\" dz=\"0\"/></am3d:trans>\
         <am3d:raster rName=\"Office3DRenderer\" rVer=\"16.0.8326\"><am3d:blip r:embed=\"{rid_i}\"/></am3d:raster>\
         <am3d:objViewport viewportSz=\"{vp}\"/><am3d:ambientLight><am3d:clr><a:scrgbClr r=\"50000\" g=\"50000\" b=\"50000\"/></am3d:clr>\
         <am3d:illuminance n=\"500000\" d=\"1000000\"/></am3d:ambientLight></am3d:model3d>\
         </a:graphicData></a:graphic></wp:inline></w:drawing>",
        head = head, am3d = NS_AM3D, rid_m = rid_m, rid_i = rid_i, xf = xf,
        ax = deg(rot.0), ay = deg(rot.1), az = deg(rot.2), vp = emu(w.max(h)));
    let picture = format!(
        "<w:drawing><wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">{head}\
         <a:graphic><a:graphicData uri=\"{pic}\"><pic:pic>\
         <pic:nvPicPr><pic:cNvPr id=\"{id}\" name=\"3D Model {id}\" descr=\"{descr}\"/><pic:cNvPicPr/></pic:nvPicPr>\
         <pic:blipFill><a:blip r:embed=\"{rid_i}\"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>\
         <pic:spPr><a:xfrm>{xf}</a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></pic:spPr>\
         </pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>",
        head = head, id = id, descr = descr, pic = NS_PIC, rid_i = rid_i, xf = xf);
    format!(
        "<mc:AlternateContent xmlns:mc=\"{mc}\" xmlns:w=\"{w}\" xmlns:wp=\"{wp}\" xmlns:a=\"{a}\" \
         xmlns:pic=\"{pic}\" xmlns:r=\"{r}\">\
         <mc:Choice xmlns:am3d=\"{am3d}\" Requires=\"am3d\">{model}</mc:Choice>\
         <mc:Fallback>{picture}</mc:Fallback></mc:AlternateContent>",
        mc = NS_MC, w = crate::document::W_NS, wp = NS_WP, a = NS_A, pic = NS_PIC, r = NS_R,
        am3d = NS_AM3D, model = model, picture = picture)
}
