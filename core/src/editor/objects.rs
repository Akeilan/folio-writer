//! Pictures and shapes: finding them on the page, selecting, inserting,
//! resizing, moving, wrapping, rotating and deleting.

use super::{Editor, Pos};
use crate::document::Item;
use crate::layout::UnitKind;
use crate::xml::{NodeId, XmlDoc};

const EMU: f64 = 12700.0;
const NS_WP: &str = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing";
const NS_A: &str = "http://schemas.openxmlformats.org/drawingml/2006/main";
const NS_WPS: &str = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape";
const NS_PIC: &str = "http://schemas.openxmlformats.org/drawingml/2006/picture";
const NS_R: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const REL_IMAGE: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image";

/// Where an object is and what it is.
#[derive(Clone, Debug)]
pub struct ObjInfo {
    pub node: NodeId,
    pub page: usize,
    /// the object's box on the page (points), effects not included
    pub x: f64,
    pub y: f64,
    pub w: f64,
    pub h: f64,
    pub rot: f64,
    pub inline: bool,
    pub kind: &'static str,
    /// inline, square, tight, through, topbottom, behind, front
    pub wrap: &'static str,
    /// where it sits in the text
    pub pos: Pos,
}

fn emu(pt: f64) -> String {
    format!("{}", (pt * EMU).round() as i64)
}

/// The run child (w:drawing / w:pict / w:object) holding `n`.
fn obj_root(dom: &XmlDoc, mut n: NodeId) -> Option<NodeId> {
    loop {
        if dom.is(n, "w:drawing") || dom.is(n, "w:pict") || dom.is(n, "w:object") {
            return Some(n);
        }
        if dom.is(n, "w:p") || dom.is(n, "w:body") {
            return None;
        }
        n = dom.parent(n)?;
    }
}

fn para_of(dom: &XmlDoc, mut n: NodeId) -> Option<NodeId> {
    loop {
        if dom.is(n, "w:p") {
            return Some(n);
        }
        n = dom.parent(n)?;
    }
}

fn wrap_name(fl: &crate::pictures::Float) -> &'static str {
    use crate::pictures::Wrap;
    match fl.wrap {
        Wrap::Square => "square",
        Wrap::Tight => "tight",
        Wrap::Through => "through",
        Wrap::TopBottom => "topbottom",
        Wrap::None => {
            if fl.behind {
                "behind"
            } else {
                "front"
            }
        }
    }
}

/// Pixel size and resolution (dots per inch) of an image file.
pub(crate) fn image_size(bytes: &[u8]) -> Option<(u32, u32, f64, f64)> {
    let (w, h) = image::ImageReader::new(std::io::Cursor::new(bytes)).with_guessed_format().ok()?.into_dimensions().ok()?;
    let mut dpi = (96.0, 96.0);
    if bytes.starts_with(b"\x89PNG") {
        // pHYs: pixels per metre
        let mut i = 8;
        while i + 8 <= bytes.len() {
            let len = u32::from_be_bytes([bytes[i], bytes[i + 1], bytes[i + 2], bytes[i + 3]]) as usize;
            let kind = &bytes[i + 4..i + 8];
            if kind == b"pHYs" && i + 17 <= bytes.len() {
                let d = &bytes[i + 8..];
                let x = u32::from_be_bytes([d[0], d[1], d[2], d[3]]) as f64;
                let y = u32::from_be_bytes([d[4], d[5], d[6], d[7]]) as f64;
                if d[8] == 1 && x > 0.0 && y > 0.0 {
                    dpi = (x * 0.0254, y * 0.0254);
                }
                break;
            }
            if kind == b"IDAT" {
                break;
            }
            i += 12 + len;
        }
    } else if bytes.starts_with(b"\xFF\xD8") && bytes.len() > 20 && &bytes[6..11] == b"JFIF\0" {
        let unit = bytes[13];
        let x = u16::from_be_bytes([bytes[14], bytes[15]]) as f64;
        let y = u16::from_be_bytes([bytes[16], bytes[17]]) as f64;
        if x > 1.0 && y > 1.0 {
            match unit {
                1 => dpi = (x, y),
                2 => dpi = (x * 2.54, y * 2.54),
                _ => {}
            }
        }
    }
    Some((w, h, dpi.0.clamp(10.0, 2400.0), dpi.1.clamp(10.0, 2400.0)))
}

impl Editor {
    // ------------------------------------------------------------ finding
    /// The object at a point on a page, topmost first.
    pub fn object_at(&self, page: usize, x: f64, y: f64) -> Option<NodeId> {
        let pg = self.layout.pages.get(page)?;
        let dom = &self.doc.dom;
        let inside = |fx: f64, fy: f64, fw: f64, fh: f64| x >= fx - 1.0 && x <= fx + fw + 1.0 && y >= fy - 1.0 && y <= fy + fh + 1.0;
        let mut front: Vec<&crate::paginate::FloatBox> = pg.floats.iter().filter(|f| !f.float.behind).collect();
        front.sort_by_key(|f| -f.float.z);
        for fb in &front {
            if inside(fb.x, fb.y, fb.float.pic.w, fb.float.pic.h) {
                return obj_root(dom, fb.float.node);
            }
        }
        for pl in &pg.lines {
            let p = &self.layout.paras[pl.para];
            let line = &p.lines[pl.line];
            for u in line.start..line.end {
                let unit = &p.units[u];
                if unit.kind != UnitKind::Object {
                    continue;
                }
                let ux = pl.x + line.xs[u - line.start];
                let uy = pl.y + line.baseline - unit.obj.1;
                if inside(ux, uy, unit.obj.0, unit.obj.1) {
                    return p.pieces.get(unit.piece as usize).and_then(|pc| pc.node);
                }
            }
        }
        let mut behind: Vec<&crate::paginate::FloatBox> = pg.floats.iter().filter(|f| f.float.behind).collect();
        behind.sort_by_key(|f| -f.float.z);
        for fb in &behind {
            if inside(fb.x, fb.y, fb.float.pic.w, fb.float.pic.h) {
                return obj_root(dom, fb.float.node);
            }
        }
        None
    }

    /// Where an object is.
    pub fn object_info(&self, node: NodeId) -> Option<ObjInfo> {
        let dom = &self.doc.dom;
        let p = para_of(dom, node)?;
        // inline: its unit in the paragraph's lines
        if let Some(&pi) = self.pidx(&p) {
            let pl = &self.layout.paras[pi];
            for (li, line) in pl.lines.iter().enumerate() {
                for u in line.start..line.end {
                    let unit = &pl.units[u];
                    if pl.pieces.get(unit.piece as usize).and_then(|pc| pc.node) != Some(node) {
                        continue;
                    }
                    if unit.kind == UnitKind::Object {
                        let &(page, idx) = self.line_loc.get(&(pi, li))?;
                        let placed = self.placed(page, idx);
                        let x0 = placed.x + line.xs[u - line.start];
                        let y0 = placed.y + line.baseline - unit.obj.1;
                        let (e, w, h, rot, kind) = match &pl.pieces[unit.piece as usize].item {
                            Item::Object(_, _, pic) => (pic.effect, pic.w, pic.h, pic.rot, pic.kind),
                            _ => ([0.0; 4], unit.obj.0, unit.obj.1, 0.0, "object"),
                        };
                        return Some(ObjInfo { node, page, x: x0 + e[0], y: y0 + e[1], w, h, rot, inline: true,
                                              kind: kind_name(kind, node, dom), wrap: "inline",
                                              pos: Pos { para: p, off: unit.pos } });
                    }
                }
            }
        }
        // floating
        for (page, pg) in self.layout.pages.iter().enumerate() {
            for fb in &pg.floats {
                if obj_root(dom, fb.float.node) == Some(node) {
                    let off = self.anchor_off(p, node).unwrap_or(0);
                    return Some(ObjInfo { node, page, x: fb.x, y: fb.y, w: fb.float.pic.w, h: fb.float.pic.h,
                                          rot: fb.float.pic.rot, inline: false,
                                          kind: kind_name(fb.float.pic.kind, node, dom),
                                          wrap: wrap_name(&fb.float), pos: Pos { para: p, off } });
                }
            }
        }
        None
    }

    fn anchor_off(&self, p: NodeId, node: NodeId) -> Option<usize> {
        let pl = self.para_layout(p)?;
        pl.units.iter().find(|u| pl.pieces.get(u.piece as usize).and_then(|pc| pc.node) == Some(node)).map(|u| u.pos)
    }

    fn float_box(&self, node: NodeId) -> Option<&crate::paginate::FloatBox> {
        let dom = &self.doc.dom;
        self.layout.pages.iter().flat_map(|pg| pg.floats.iter()).find(|fb| obj_root(dom, fb.float.node) == Some(node))
    }

    /// While a text box's text is edited: its shape becomes the selected
    /// object (for Shape Format commands), the text story kept.
    pub fn select_story_textbox(&mut self) -> bool {
        let super::Story::TextBox(_, c) = self.story else { return false };
        let node = self.layout.pages.iter().flat_map(|pg| pg.floats.iter())
            .find(|f| f.float.pic.text.is_some_and(|t| t.0 == c))
            .and_then(|f| obj_root(&self.doc.dom, f.float.node));
        self.sel_obj = node;
        node.is_some()
    }

    /// Leave a text box's text for the body, the text box selected.
    pub fn leave_textbox(&mut self) -> bool {
        let super::Story::TextBox(_, c) = self.story else { return false };
        let node = self.layout.pages.iter().flat_map(|pg| pg.floats.iter())
            .find(|f| f.float.pic.text.is_some_and(|t| t.0 == c))
            .and_then(|f| obj_root(&self.doc.dom, f.float.node));
        self.edit_header_footer(None, false);
        if let Some(n) = node {
            self.select_object(Some(n));
        }
        true
    }

    /// Select an object (None: back to the text). The caret goes to it.
    pub fn select_object(&mut self, node: Option<NodeId>) {
        self.sel_obj = node;
        if let Some(n) = node {
            if let Some(info) = self.object_info(n) {
                self.caret = info.pos;
                self.anchor = info.pos;
            }
        }
    }

    /// The selected object, if it still exists.
    pub fn selected_object(&mut self) -> Option<ObjInfo> {
        let n = self.sel_obj?;
        let info = self.object_info(n);
        if info.is_none() {
            self.sel_obj = None;
        }
        info
    }

    // ------------------------------------------------------------ editing
    fn graphic_xfrm_ext(&self, root: NodeId) -> Vec<NodeId> {
        // the a:ext of the object's own a:xfrm (pic:spPr / wps:spPr)
        let dom = &self.doc.dom;
        let mut out = Vec::new();
        if let Some(gd) = crate::pictures::find(dom, root, "a:graphicData") {
            if let Some(obj) = dom.elements(gd).next() {
                for sp in ["pic:spPr", "wps:spPr", "wpg:grpSpPr"] {
                    if let Some(s) = dom.child(obj, sp) {
                        if let Some(x) = dom.child(s, "a:xfrm") {
                            if let Some(e) = dom.child(x, "a:ext") {
                                out.push(e);
                            }
                        }
                    }
                }
            }
        }
        out
    }

    /// Resize the selected object (points).
    pub fn object_resize(&mut self, w: f64, h: f64) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let (w, h) = (w.max(1.0), h.max(1.0));
        self.begin();
        let dom = &self.doc.dom;
        let holder = dom.child(node, "wp:inline").or_else(|| dom.child(node, "wp:anchor"));
        if let Some(hd) = holder {
            let ext = dom.child(hd, "wp:extent");
            let inner = self.graphic_xfrm_ext(node);
            let dom = &mut self.doc.dom;
            if let Some(e) = ext {
                dom.set_attr(e, "cx", &emu(w));
                dom.set_attr(e, "cy", &emu(h));
            }
            for e in inner {
                dom.set_attr(e, "cx", &emu(w));
                dom.set_attr(e, "cy", &emu(h));
            }
        } else if let Some(el) = crate::pictures::vml_shape(dom, node) {
            let style = dom.attr(el, "style").unwrap_or("").to_string();
            let mut parts: Vec<String> = style.split(';').filter(|p| {
                let k = p.split(':').next().unwrap_or("").trim();
                k != "width" && k != "height"
            }).map(|s| s.to_string()).collect();
            parts.push(format!("width:{:.2}pt", w));
            parts.push(format!("height:{:.2}pt", h));
            let st = parts.into_iter().filter(|p| !p.trim().is_empty()).collect::<Vec<_>>().join(";");
            self.doc.dom.set_attr(el, "style", &st);
        }
        self.commit("Size", false);
        true
    }

    /// Move the selected floating object so its top-left is at x, y on
    /// its page (points).
    pub fn object_move(&mut self, x: f64, y: f64) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let Some(fb) = self.float_box(node) else { return false };
        let (ox, oy) = fb.origin;
        let (dx, dy) = (x - ox, y - oy);
        let dom = &self.doc.dom;
        let Some(a) = dom.child(node, "wp:anchor") else { return false };
        self.begin();
        let dom = &mut self.doc.dom;
        dom.set_attr(a, "simplePos", "0");
        for (tag, v) in [("wp:positionH", dx), ("wp:positionV", dy)] {
            let ph = match dom.child(a, tag) {
                Some(n) => n,
                None => continue,
            };
            for c in dom.children(ph).to_vec() {
                dom.detach(c);
            }
            let off = dom.new_element("wp:posOffset", &[]);
            let t = dom.new_text(&emu(v));
            dom.append(off, t);
            dom.append(ph, off);
        }
        self.commit("Move", false);
        true
    }

    fn anchor_element(&self) -> Option<NodeId> {
        let node = self.sel_obj?;
        self.doc.dom.child(node, "wp:anchor")
    }

    fn next_z(&self) -> i64 {
        let mut z: i64 = 251658240;
        for pg in &self.layout.pages {
            for fb in &pg.floats {
                z = z.max(fb.float.z);
            }
        }
        z + 1024
    }

    /// Text wrapping: inline, square, tight, through, topbottom, behind,
    /// front.
    pub fn object_set_wrap(&mut self, how: &str) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let Some(info) = self.object_info(node) else { return false };
        if !self.doc.dom.is(node, "w:drawing") {
            return false;
        }
        if how == info.wrap {
            return true;
        }
        self.ensure_drawing_ns();
        self.begin();
        if how == "inline" {
            self.to_inline(node);
        } else {
            let a = match self.doc.dom.child(node, "wp:anchor") {
                Some(a) => a,
                None => self.to_anchor(node, &info),
            };
            self.set_wrap_element(a, how);
        }
        self.commit("Wrap Text", false);
        true
    }

    fn set_wrap_element(&mut self, a: NodeId, how: &str) {
        let dom = &mut self.doc.dom;
        for c in dom.children(a).to_vec() {
            if dom.name(c).starts_with("wp:wrap") {
                dom.detach(c);
            }
        }
        let el = match how {
            "square" => dom.new_element("wp:wrapSquare", &[("wrapText", "bothSides")]),
            "tight" | "through" => {
                let e = dom.new_element(if how == "tight" { "wp:wrapTight" } else { "wp:wrapThrough" },
                                        &[("wrapText", "bothSides")]);
                let poly = dom.new_element("wp:wrapPolygon", &[("edited", "0")]);
                for (i, (x, y)) in [(0, 0), (0, 21600), (21600, 21600), (21600, 0), (0, 0)].iter().enumerate() {
                    let pt = dom.new_element(if i == 0 { "wp:start" } else { "wp:lineTo" },
                                             &[("x", &x.to_string()), ("y", &y.to_string())]);
                    dom.append(poly, pt);
                }
                dom.append(e, poly);
                e
            }
            "topbottom" => dom.new_element("wp:wrapTopAndBottom", &[]),
            _ => dom.new_element("wp:wrapNone", &[]),
        };
        dom.set_attr(a, "behindDoc", if how == "behind" { "1" } else { "0" });
        // after extent / effectExtent
        let kids: Vec<NodeId> = dom.elements(a).collect();
        let mut idx = 0;
        for k in &kids {
            if matches!(dom.name(*k), "wp:simplePos" | "wp:positionH" | "wp:positionV" | "wp:extent" | "wp:effectExtent") {
                idx = dom.index_in_parent(*k).unwrap_or(0) + 1;
            }
        }
        dom.insert(a, idx, el);
    }

    /// wp:inline -> wp:anchor where the object is now.
    fn to_anchor(&mut self, node: NodeId, info: &ObjInfo) -> NodeId {
        let z = self.next_z();
        // measured from the column and the paragraph's top
        let page = &self.layout.pages[info.page];
        let sec = &self.doc.sections[page.section.min(self.doc.sections.len().saturating_sub(1))];
        let col_x = crate::layout::tw(sec.col_left(0));
        let p = info.pos.para;
        let para_top = self.pidx(&p).and_then(|&pi| {
            let &(pg, idx) = self.line_loc.get(&(pi, 0))?;
            if pg != info.page {
                return None;
            }
            let pl = &self.layout.paras[pi];
            Some(self.placed(pg, idx).y - pl.lines[0].skip - pl.before)
        });
        let (vrel, voff) = match para_top {
            Some(t) => ("paragraph", info.y - t),
            None => ("page", info.y),
        };
        let dom = &mut self.doc.dom;
        let inline = dom.child(node, "wp:inline").unwrap();
        let a = dom.new_element("wp:anchor", &[("distT", "0"), ("distB", "0"), ("distL", "114300"), ("distR", "114300"),
            ("simplePos", "0"), ("relativeHeight", &z.to_string()), ("behindDoc", "0"), ("locked", "0"),
            ("layoutInCell", "1"), ("allowOverlap", "1")]);
        let sp = dom.new_element("wp:simplePos", &[("x", "0"), ("y", "0")]);
        dom.append(a, sp);
        for (tag, rel, v) in [("wp:positionH", "column", info.x - col_x), ("wp:positionV", vrel, voff)] {
            let ph = dom.new_element(tag, &[("relativeFrom", rel)]);
            let off = dom.new_element("wp:posOffset", &[]);
            let t = dom.new_text(&emu(v));
            dom.append(off, t);
            dom.append(ph, off);
            dom.append(a, ph);
        }
        for c in dom.elements(inline).collect::<Vec<_>>() {
            dom.detach(c);
            dom.append(a, c);
        }
        let idx = dom.index_in_parent(inline).unwrap_or(0);
        dom.detach(inline);
        dom.insert(node, idx, a);
        a
    }

    /// wp:anchor -> wp:inline.
    fn to_inline(&mut self, node: NodeId) {
        let dom = &mut self.doc.dom;
        let Some(a) = dom.child(node, "wp:anchor") else { return };
        let inl = dom.new_element("wp:inline", &[("distT", "0"), ("distB", "0"), ("distL", "0"), ("distR", "0")]);
        for c in dom.elements(a).collect::<Vec<_>>() {
            let keep = matches!(dom.name(c), "wp:extent" | "wp:effectExtent" | "wp:docPr" | "wp:cNvGraphicFramePr" | "a:graphic");
            if keep {
                dom.detach(c);
                dom.append(inl, c);
            }
        }
        let idx = dom.index_in_parent(a).unwrap_or(0);
        dom.detach(a);
        dom.insert(node, idx, inl);
    }

    /// The drawing namespaces on the document element.
    fn ensure_drawing_ns(&mut self) {
        let dom = &mut self.doc.dom;
        let root = dom.root;
        let root_el = dom.elements(root).next().filter(|_| !dom.name(root).starts_with("w:")).unwrap_or(root);
        let target = if dom.name(root_el) == "w:document" { root_el } else { root };
        for (k, v) in [("xmlns:wp", NS_WP), ("xmlns:a", NS_A), ("xmlns:pic", NS_PIC), ("xmlns:r", NS_R)] {
            if dom.attr(target, k).is_none() {
                let rec = dom.recording;
                dom.recording = false;
                dom.set_attr(target, k, v);
                dom.recording = rec;
            }
        }
    }

    /// Rotate or flip: right, left (90 degrees), flipv, fliph.
    pub fn object_rotate(&mut self, how: &str) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let dom = &self.doc.dom;
        let Some(gd) = crate::pictures::find(dom, node, "a:graphicData") else { return false };
        let Some(obj) = dom.elements(gd).next() else { return false };
        let sp = ["pic:spPr", "wps:spPr", "wpg:grpSpPr"].iter().find_map(|t| dom.child(obj, t));
        let Some(sp) = sp else { return false };
        self.begin();
        let dom = &mut self.doc.dom;
        let xf = match dom.child(sp, "a:xfrm") {
            Some(x) => x,
            None => {
                let x = dom.new_element("a:xfrm", &[]);
                dom.insert(sp, 0, x);
                x
            }
        };
        match how {
            "right" | "left" => {
                let cur: i64 = dom.attr(xf, "rot").and_then(|v| v.parse().ok()).unwrap_or(0);
                let d = if how == "right" { 5400000 } else { -5400000 };
                let v = (cur + d).rem_euclid(21600000);
                if v == 0 {
                    dom.remove_attr(xf, "rot");
                } else {
                    dom.set_attr(xf, "rot", &v.to_string());
                }
            }
            "fliph" | "flipv" => {
                let k = if how == "fliph" { "flipH" } else { "flipV" };
                let on = dom.attr(xf, k).map_or(false, |v| v == "1" || v == "true");
                if on {
                    dom.remove_attr(xf, k);
                } else {
                    dom.set_attr(xf, k, "1");
                }
            }
            _ => {}
        }
        self.commit("Rotate", false);
        true
    }

    /// Bring forward / send backward (delta), or to the front / back
    /// (delta = +-1000).
    pub fn object_z(&mut self, delta: i32) -> bool {
        let Some(a) = self.anchor_element() else { return false };
        let mut zs: Vec<i64> = self.layout.pages.iter().flat_map(|p| p.floats.iter().map(|f| f.float.z)).collect();
        zs.sort();
        let cur: i64 = self.doc.dom.attr(a, "relativeHeight").and_then(|v| v.parse().ok()).unwrap_or(0);
        let nz = if delta >= 1000 {
            zs.last().copied().unwrap_or(cur) + 1024
        } else if delta <= -1000 {
            (zs.first().copied().unwrap_or(cur) - 1024).max(0)
        } else if delta > 0 {
            zs.iter().find(|&&z| z > cur).map(|z| z + 1).unwrap_or(cur)
        } else {
            zs.iter().rev().find(|&&z| z < cur).map(|z| (z - 1).max(0)).unwrap_or(cur)
        };
        self.begin();
        self.doc.dom.set_attr(a, "relativeHeight", &nz.to_string());
        self.commit("Order", false);
        true
    }

    /// Align a floating object with the margins or the page: left, center,
    /// right, top, middle, bottom.
    pub fn object_align(&mut self, where_: &str, page: bool) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let Some(info) = self.object_info(node) else { return false };
        if info.inline {
            return false;
        }
        let Some(a) = self.anchor_element() else { return false };
        let (tag, align) = match where_ {
            "left" | "center" | "right" => ("wp:positionH", where_),
            "top" => ("wp:positionV", "top"),
            "middle" => ("wp:positionV", "center"),
            "bottom" => ("wp:positionV", "bottom"),
            _ => return false,
        };
        let rel = if page { "page" } else { "margin" };
        self.begin();
        let dom = &mut self.doc.dom;
        let ph = match dom.child(a, tag) {
            Some(n) => n,
            None => return false,
        };
        dom.set_attr(ph, "relativeFrom", rel);
        for c in dom.children(ph).to_vec() {
            dom.detach(c);
        }
        let al = dom.new_element("wp:align", &[]);
        let t = dom.new_text(align);
        dom.append(al, t);
        dom.append(ph, al);
        self.commit("Align", false);
        true
    }

    /// Delete the selected object.
    pub fn object_delete(&mut self) -> bool {
        let Some(node) = self.sel_obj.take() else { return false };
        self.begin();
        let dom = &mut self.doc.dom;
        let run = dom.parent(node);
        dom.detach(node);
        if let Some(r) = run {
            if dom.is(r, "w:r") && dom.elements(r).all(|c| dom.is(c, "w:rPr")) {
                dom.detach(r);
            }
        }
        self.commit("Delete", false);
        true
    }

    /// Put a picture file in at the caret, in line with the text. `name` is
    /// the file name (its extension says the format).
    pub fn insert_picture(&mut self, bytes: &[u8], name: &str) -> bool {
        let Some((pw, ph, dx, dy)) = image_size(bytes) else { return false };
        let ext = name.rsplit('.').next().unwrap_or("png").to_ascii_lowercase();
        let (ext, ctype) = match ext.as_str() {
            "jpg" | "jpeg" | "jpe" => ("jpeg", "image/jpeg"),
            "gif" => ("gif", "image/gif"),
            "bmp" => ("bmp", "image/bmp"),
            "tif" | "tiff" => ("tiff", "image/tiff"),
            "webp" => ("webp", "image/webp"),
            _ => ("png", "image/png"),
        };
        // size: the picture's resolution, no wider than the column
        let mut w = pw as f64 * 72.0 / dx;
        let mut h = ph as f64 * 72.0 / dy;
        let sec = self.doc.blocks.iter().find(|b| b.node == self.caret.para).map(|b| b.section).unwrap_or(0);
        let col = self.doc.sections.get(sec).map(|s| crate::layout::tw(s.text_width())).unwrap_or(468.0);
        if w > col {
            h *= col / w;
            w = col;
        }
        // the part
        let main = self.doc.main.clone();
        let mut n = 1;
        while self.doc.pkg.has(&format!("word/media/image{}.{}", n, ext)) {
            n += 1;
        }
        let part = format!("word/media/image{}.{}", n, ext);
        self.doc.pkg.put_raw(&part, bytes.to_vec());
        self.doc.pkg.ensure_default(ext, ctype);
        let target = crate::package::Package::relative_target(&main, &part);
        let rid = self.doc.pkg.add_rel(&main, REL_IMAGE, &target);
        self.doc.images.insert(rid.clone(), crate::pictures::ImageData { part, bytes: std::sync::Arc::new(bytes.to_vec()) });
        // the drawing
        let id = self.next_docpr_id();
        let base = name.rsplit('/').next().unwrap_or(name).to_string();
        let xml = format!(
            "<w:drawing xmlns:w=\"{w}\"><wp:inline xmlns:wp=\"{wp}\" distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">\
             <wp:extent cx=\"{cx}\" cy=\"{cy}\"/><wp:effectExtent l=\"0\" t=\"0\" r=\"0\" b=\"0\"/>\
             <wp:docPr id=\"{id}\" name=\"Picture {id}\" descr=\"{descr}\"/><wp:cNvGraphicFramePr>\
             <a:graphicFrameLocks xmlns:a=\"{a}\" noChangeAspect=\"1\"/></wp:cNvGraphicFramePr>\
             <a:graphic xmlns:a=\"{a}\"><a:graphicData uri=\"{pic}\"><pic:pic xmlns:pic=\"{pic}\">\
             <pic:nvPicPr><pic:cNvPr id=\"{id}\" name=\"{descr}\"/><pic:cNvPicPr/></pic:nvPicPr>\
             <pic:blipFill><a:blip xmlns:r=\"{r}\" r:embed=\"{rid}\"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>\
             <pic:spPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"{cx}\" cy=\"{cy}\"/></a:xfrm>\
             <a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>\
             </wp:inline></w:drawing>",
            w = crate::document::W_NS, wp = NS_WP, a = NS_A, pic = NS_PIC, r = NS_R,
            cx = emu(w), cy = emu(h), id = id, rid = rid, descr = crate::xml::attr_escaped(&base));
        let Ok(tmp) = XmlDoc::parse(xml.as_bytes()) else { return false };
        let Some(src) = tmp.elements(tmp.root).next().or(Some(tmp.root)) else { return false };
        let src = if tmp.is(src, "w:drawing") { src } else { tmp.root };
        self.begin();
        self.delete_selection();
        let p = self.caret.para;
        let off = self.caret.off;
        let (parent, idx, like) = self.split_runs_at(p, off);
        let run = self.new_run(p, like, &[]);
        let d = self.doc.dom.import_node(&tmp, src);
        // namespace declarations stay with the drawing's parts
        self.doc.dom.remove_attr(d, "xmlns:w");
        self.doc.dom.append(run, d);
        self.doc.dom.insert(parent, idx, run);
        self.caret = Pos { para: p, off: off + 1 };
        self.anchor = self.caret;
        self.commit("Insert Picture", false);
        self.sel_obj = Some(d);
        true
    }

    /// Insert > Shapes / Draw Text Box: a shape (DrawingML preset `prst`, or
    /// "textbox") at x, y on page `pg`, w x h points (negative for a line
    /// drawn up or left), in front of the text; it ends up selected (a text
    /// box: its text being edited).
    #[allow(clippy::too_many_arguments)]
    pub fn insert_shape(&mut self, prst: &str, pg: usize, x: f64, y: f64, w: f64, h: f64, name: &str, arrow: bool) -> bool {
        if self.story != super::Story::Body {
            self.edit_header_footer(None, false);
        }
        let Some(page) = self.layout.pages.get(pg) else { return false };
        let (pw, ph) = (page.width, page.height);
        // the paragraph it is anchored in: the one beside the point
        let Some(at) = self.hit(pg, x.clamp(0.0, pw), y.clamp(0.0, ph)) else { return false };
        let p = match self.cell_of(at.para) {
            Some((tbl, _, _)) => {
                // not in a table: the paragraph after it (or before)
                let dom = &self.doc.dom;
                let mut n = tbl;
                while let Some(up) = dom.parent(n) {
                    if dom.is(up, "w:body") {
                        break;
                    }
                    n = up;
                }
                let parent = dom.parent(n).unwrap();
                let i = dom.index_in_parent(n).unwrap();
                dom.children(parent)[i + 1..].iter().copied().find(|&c| dom.is(c, "w:p"))
                    .or_else(|| dom.children(parent)[..i].iter().rev().copied().find(|&c| dom.is(c, "w:p")))
                    .unwrap_or(at.para)
            }
            None => at.para,
        };
        let line = matches!(prst, "line" | "straightConnector1" | "bentConnector3" | "curvedConnector3");
        let (flip_h, flip_v) = (w < 0.0, h < 0.0);
        let (x0, y0) = (if flip_h { x + w } else { x }, if flip_v { y + h } else { y });
        let (aw, ah) = (w.abs().max(if line { 0.0 } else { 1.0 }), h.abs().max(if line { 0.0 } else { 1.0 }));
        let id = self.next_docpr_id();
        // stacked above everything else
        fn max_height(dom: &XmlDoc, n: NodeId, m: &mut i64) {
            for c in dom.elements(n) {
                if dom.is(c, "wp:anchor") {
                    if let Some(v) = dom.attr(c, "relativeHeight").and_then(|v| v.parse::<i64>().ok()) {
                        *m = (*m).max(v);
                    }
                }
                max_height(dom, c, m);
            }
        }
        let mut z = 251659264i64;
        max_height(&self.doc.dom, self.doc.body, &mut z);
        let z = z + 1024;
        let textbox = prst == "textbox";
        let geom = if textbox { "rect" } else { prst };
        let flips = format!("{}{}", if flip_h { " flipH=\"1\"" } else { "" }, if flip_v { " flipV=\"1\"" } else { "" });
        let sp = if textbox {
            "<a:solidFill><a:schemeClr val=\"lt1\"/></a:solidFill><a:ln w=\"6350\"><a:solidFill><a:prstClr val=\"black\"/></a:solidFill></a:ln>".to_string()
        } else if line {
            format!("<a:ln w=\"9525\">{}</a:ln>", if arrow { "<a:tailEnd type=\"triangle\"/>" } else { "" })
        } else {
            String::new()
        };
        let style = if textbox {
            ""
        } else if line {
            "<wps:style><a:lnRef idx=\"1\"><a:schemeClr val=\"accent1\"/></a:lnRef><a:fillRef idx=\"0\"><a:schemeClr val=\"accent1\"/></a:fillRef>\
             <a:effectRef idx=\"0\"><a:schemeClr val=\"accent1\"/></a:effectRef><a:fontRef idx=\"minor\"><a:schemeClr val=\"tx1\"/></a:fontRef></wps:style>"
        } else {
            "<wps:style><a:lnRef idx=\"2\"><a:schemeClr val=\"accent1\"><a:shade val=\"50000\"/></a:schemeClr></a:lnRef>\
             <a:fillRef idx=\"1\"><a:schemeClr val=\"accent1\"/></a:fillRef><a:effectRef idx=\"0\"><a:schemeClr val=\"accent1\"/></a:effectRef>\
             <a:fontRef idx=\"minor\"><a:schemeClr val=\"lt1\"/></a:fontRef></wps:style>"
        };
        let txbx = if textbox {
            "<wps:txbx><w:txbxContent><w:p/></w:txbxContent></wps:txbx>"
        } else {
            ""
        };
        let body_pr = if textbox {
            "<wps:bodyPr rot=\"0\" vert=\"horz\" wrap=\"square\" lIns=\"91440\" tIns=\"45720\" rIns=\"91440\" bIns=\"45720\" anchor=\"t\" anchorCtr=\"0\"><a:noAutofit/></wps:bodyPr>"
        } else {
            "<wps:bodyPr rot=\"0\" spcFirstLastPara=\"0\" vertOverflow=\"overflow\" horzOverflow=\"overflow\" vert=\"horz\" wrap=\"square\" lIns=\"91440\" tIns=\"45720\" rIns=\"91440\" bIns=\"45720\" anchor=\"ctr\" anchorCtr=\"0\"><a:prstTxWarp prst=\"textNoShape\"><a:avLst/></a:prstTxWarp><a:noAutofit/></wps:bodyPr>"
        };
        let cnv = if textbox { "<wps:cNvSpPr txBox=\"1\"/>" } else if line { "<wps:cNvCnPr/>" } else { "<wps:cNvSpPr/>" };
        let xml = format!(
            "<w:r xmlns:w=\"{w}\" xmlns:wp=\"{wp}\" xmlns:a=\"{a}\" xmlns:wps=\"{wps}\"><w:rPr><w:noProof/></w:rPr><w:drawing>\
             <wp:anchor distT=\"0\" distB=\"0\" distL=\"114300\" distR=\"114300\" simplePos=\"0\" relativeHeight=\"{z}\" \
             behindDoc=\"0\" locked=\"0\" layoutInCell=\"1\" allowOverlap=\"1\"><wp:simplePos x=\"0\" y=\"0\"/>\
             <wp:positionH relativeFrom=\"page\"><wp:posOffset>{ex}</wp:posOffset></wp:positionH>\
             <wp:positionV relativeFrom=\"page\"><wp:posOffset>{ey}</wp:posOffset></wp:positionV>\
             <wp:extent cx=\"{cx}\" cy=\"{cy}\"/><wp:effectExtent l=\"0\" t=\"0\" r=\"0\" b=\"0\"/><wp:wrapNone/>\
             <wp:docPr id=\"{id}\" name=\"{name} {id}\"/><wp:cNvGraphicFramePr/>\
             <a:graphic><a:graphicData uri=\"{wps}\"><wps:wsp>{cnv}\
             <wps:spPr><a:xfrm{flips}><a:off x=\"0\" y=\"0\"/><a:ext cx=\"{cx}\" cy=\"{cy}\"/></a:xfrm>\
             <a:prstGeom prst=\"{geom}\"><a:avLst/></a:prstGeom>{sp}</wps:spPr>{style}{txbx}{body_pr}</wps:wsp>\
             </a:graphicData></a:graphic></wp:anchor></w:drawing></w:r>",
            w = crate::document::W_NS, wp = NS_WP, a = NS_A, wps = NS_WPS,
            ex = emu(x0), ey = emu(y0), cx = emu(aw), cy = emu(ah), name = crate::xml::attr_escaped(name));
        let Ok(tmp) = XmlDoc::parse(xml.as_bytes()) else { return false };
        self.begin();
        let r = self.doc.dom.import_node(&tmp, tmp.root);
        for k in ["xmlns:w"] {
            self.doc.dom.remove_attr(r, k);
        }
        let dom = &self.doc.dom;
        let idx = dom.child(p, "w:pPr").and_then(|pp| dom.index_in_parent(pp)).map(|i| i + 1).unwrap_or(0);
        self.doc.dom.insert(p, idx, r);
        self.caret = Pos { para: p, off: 0 };
        self.anchor = self.caret;
        self.commit(if textbox { "Insert Text Box" } else { "Insert Shape" }, false);
        let d = self.doc.dom.child(r, "w:drawing");
        if textbox {
            // straight into its text
            let content = d.and_then(|d| crate::pictures::find(&self.doc.dom, d, "w:txbxContent"));
            if let Some(c) = content {
                let found = self.layout.pages.iter().enumerate()
                    .find_map(|(i, pg)| pg.floats.iter().find(|f| f.float.pic.text.is_some_and(|t| t.0 == c)).map(|f| (i, f.x, f.y)));
                if let Some((i, fx, fy)) = found {
                    if self.edit_textbox(i, fx + 8.0, fy + 8.0) {
                        return true;
                    }
                }
            }
        }
        self.sel_obj = d;
        true
    }

    fn next_docpr_id(&self) -> u32 {
        fn walk(dom: &XmlDoc, n: NodeId, m: &mut u32) {
            for c in dom.elements(n) {
                if dom.is(c, "wp:docPr") || dom.is(c, "pic:cNvPr") {
                    if let Some(v) = dom.attr(c, "id").and_then(|v| v.parse::<u32>().ok()) {
                        *m = (*m).max(v);
                    }
                }
                walk(dom, c, m);
            }
        }
        let mut m = 0;
        walk(&self.doc.dom, self.doc.body, &mut m);
        m + 1
    }

    /// The picture's original size (points), for Reset Picture & Size.
    pub fn object_natural_size(&self) -> Option<(f64, f64)> {
        let node = self.sel_obj?;
        let dom = &self.doc.dom;
        let blip = crate::pictures::find(dom, node, "a:blip")?;
        let rid = dom.attr(blip, "r:embed")?;
        let img = self.doc.images.get(rid)?;
        let (pw, ph, dx, dy) = image_size(&img.bytes)?;
        Some((pw as f64 * 72.0 / dx, ph as f64 * 72.0 / dy))
    }
}

fn kind_name(kind: &'static str, node: NodeId, dom: &XmlDoc) -> &'static str {
    if kind == "shape" && crate::pictures::find(dom, node, "w:txbxContent").is_some() {
        return "textbox";
    }
    kind
}

// ------------------------------------------------------------- effects
const SPPR_ORDER: &[&str] = &["a:xfrm", "a:custGeom", "a:prstGeom", "a:noFill", "a:solidFill", "a:gradFill",
    "a:blipFill", "a:pattFill", "a:grpFill", "a:ln", "a:effectLst", "a:effectDag", "a:scene3d", "a:sp3d", "a:extLst"];
const EFFECT_ORDER: &[&str] = &["a:blur", "a:fillOverlay", "a:glow", "a:innerShdw", "a:outerShdw", "a:prstShdw",
    "a:reflection", "a:softEdge"];
const NS_DECL: &str = "xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" \
                       xmlns:a14=\"http://schemas.microsoft.com/office/drawing/2010/main\"";

fn insert_ordered(dom: &mut XmlDoc, parent: NodeId, node: NodeId, order: &[&str]) {
    let rank = |n: &str| order.iter().position(|x| *x == n).unwrap_or(order.len());
    let me = rank(dom.name(node));
    let kids: Vec<NodeId> = dom.elements(parent).collect();
    let mut idx = dom.children(parent).len();
    for k in kids {
        if rank(dom.name(k)) > me {
            idx = dom.index_in_parent(k).unwrap_or(idx);
            break;
        }
    }
    dom.insert(parent, idx, node);
}

impl Editor {
    /// The selected picture's or shape's spPr and its picture's a:blip.
    fn sel_props(&self) -> Option<(NodeId, Option<NodeId>, NodeId)> {
        let node = self.sel_obj?;
        let dom = &self.doc.dom;
        let holder = dom.child(node, "wp:inline").or_else(|| dom.child(node, "wp:anchor"))?;
        let gd = crate::pictures::find(dom, holder, "a:graphicData")?;
        let obj = dom.elements(gd).next()?;
        let sppr = dom.child(obj, "pic:spPr").or_else(|| dom.child(obj, "wps:spPr"))?;
        let blip = crate::pictures::find(dom, obj, "a:blip");
        Some((sppr, blip, holder))
    }

    fn parse_snippet(&mut self, xml: &str) -> Option<NodeId> {
        let wrapped = format!("<root {NS_DECL}>{xml}</root>");
        let tmp = XmlDoc::parse(wrapped.as_bytes()).ok()?;
        let first = tmp.elements(tmp.root).next()?;
        Some(self.doc.dom.import_node(&tmp, first))
    }

    /// Set (xml) or remove (None) one effect of the selected object:
    /// "a:outerShdw" (any shadow), "a:innerShdw", "a:glow", "a:softEdge",
    /// "a:reflection", or "bevel" (a:scene3d + a:sp3d).
    pub fn object_effect(&mut self, kind: &str, xml: Option<&str>) -> bool {
        let Some((sppr, _, _)) = self.sel_props() else { return false };
        self.begin();
        if kind == "bevel" {
            for name in ["a:scene3d", "a:sp3d"] {
                if let Some(n) = self.doc.dom.child(sppr, name) {
                    self.doc.dom.detach(n);
                }
            }
            if let Some(x) = xml {
                let both = format!("<g>{x}</g>");
                if let Some(g) = self.parse_snippet(&both) {
                    for k in self.doc.dom.children(g).to_vec() {
                        self.doc.dom.detach(k);
                        insert_ordered(&mut self.doc.dom, sppr, k, SPPR_ORDER);
                    }
                }
            }
        } else {
            let el = match self.doc.dom.child(sppr, "a:effectLst") {
                Some(e) => e,
                None => {
                    let e = self.doc.dom.new_element("a:effectLst", &[]);
                    insert_ordered(&mut self.doc.dom, sppr, e, SPPR_ORDER);
                    e
                }
            };
            // shadows replace each other
            let same: &[&str] = if kind == "a:outerShdw" || kind == "a:innerShdw" || kind == "a:prstShdw" {
                &["a:outerShdw", "a:innerShdw", "a:prstShdw"]
            } else {
                std::slice::from_ref(&kind)
            };
            for k in self.doc.dom.elements(el).collect::<Vec<_>>() {
                if same.contains(&self.doc.dom.name(k)) {
                    self.doc.dom.detach(k);
                }
            }
            if let Some(x) = xml {
                if let Some(n) = self.parse_snippet(x) {
                    insert_ordered(&mut self.doc.dom, el, n, EFFECT_ORDER);
                }
            }
            if self.doc.dom.elements(el).next().is_none() {
                self.doc.dom.detach(el);
            }
        }
        self.update_effect_extent();
        self.commit("Picture Effects", false);
        true
    }

    /// Set (xml) or remove the picture's colour settings: "a:lum",
    /// "a:grayscl", "a:biLevel", "a:duotone", "a:alphaModFix" (a:blip
    /// children); "recolor" removes all but transparency first.
    pub fn object_blip(&mut self, kind: &str, xml: Option<&str>) -> bool {
        let Some((_, Some(blip), _)) = self.sel_props() else { return false };
        self.begin();
        let recolor = ["a:grayscl", "a:biLevel", "a:duotone", "a:lum"];
        for k in self.doc.dom.elements(blip).collect::<Vec<_>>() {
            let nm = self.doc.dom.name(k);
            let hit = nm == kind || (kind == "recolor" && recolor.contains(&nm))
                // Word's brightness/contrast extension goes with a:lum
                || (kind == "a:lum" && nm == "a:extLst" && self.doc.dom.serialize_node(k).contains("brightnessContrast"));
            if hit {
                self.doc.dom.detach(k);
            }
        }
        if let Some(x) = xml {
            if let Some(n) = self.parse_snippet(x) {
                let at = self.doc.dom.elements(blip).position(|k| self.doc.dom.is(k, "a:extLst"));
                match at {
                    Some(i) => {
                        let idx = self.doc.dom.index_in_parent(self.doc.dom.elements(blip).nth(i).unwrap()).unwrap();
                        self.doc.dom.insert(blip, idx, n);
                    }
                    None => self.doc.dom.append(blip, n),
                }
            }
        }
        self.commit("Picture Color", false);
        true
    }

    /// The outline of the selected picture or shape (a:ln), or none.
    pub fn object_outline(&mut self, xml: Option<&str>) -> bool {
        let Some((sppr, _, _)) = self.sel_props() else { return false };
        self.begin();
        if let Some(n) = self.doc.dom.child(sppr, "a:ln") {
            self.doc.dom.detach(n);
        }
        if let Some(x) = xml {
            if let Some(n) = self.parse_snippet(x) {
                insert_ordered(&mut self.doc.dom, sppr, n, SPPR_ORDER);
            }
        }
        self.update_effect_extent();
        self.commit("Picture Border", false);
        true
    }

    /// Shape Fill: replace the fill (xml: a:solidFill / a:gradFill /
    /// a:noFill ...; None: back to the style's).
    pub fn object_fill(&mut self, xml: Option<&str>) -> bool {
        let Some((sppr, _, _)) = self.sel_props() else { return false };
        self.begin();
        for name in ["a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill"] {
            if let Some(n) = self.doc.dom.child(sppr, name) {
                self.doc.dom.detach(n);
            }
        }
        if let Some(x) = xml {
            if let Some(n) = self.parse_snippet(x) {
                insert_ordered(&mut self.doc.dom, sppr, n, SPPR_ORDER);
            }
        }
        self.commit("Shape Fill", false);
        true
    }

    /// Edit Shape > Change Shape: another preset geometry.
    pub fn object_geometry(&mut self, prst: &str) -> bool {
        let Some((sppr, _, _)) = self.sel_props() else { return false };
        self.begin();
        let dom = &mut self.doc.dom;
        if let Some(c) = dom.child(sppr, "a:custGeom") {
            dom.detach(c);
        }
        let g = match dom.child(sppr, "a:prstGeom") {
            Some(g) => g,
            None => {
                let g = dom.new_element("a:prstGeom", &[]);
                let av = dom.new_element("a:avLst", &[]);
                dom.append(g, av);
                insert_ordered(dom, sppr, g, SPPR_ORDER);
                g
            }
        };
        dom.set_attr(g, "prst", prst);
        if let Some(av) = dom.child(g, "a:avLst") {
            for k in dom.children(av).to_vec() {
                dom.detach(k);
            }
        }
        self.commit("Change Shape", false);
        true
    }

    /// The selected shape's wps:bodyPr: set (or remove) attributes (text
    /// direction "vert", vertical alignment "anchor").
    pub fn object_body(&mut self, attrs: &[(String, Option<String>)]) -> bool {
        let Some((sppr, _, _)) = self.sel_props() else { return false };
        let Some(wsp) = self.doc.dom.parent(sppr) else { return false };
        let Some(bp) = self.doc.dom.child(wsp, "wps:bodyPr") else { return false };
        self.begin();
        for (k, v) in attrs {
            match v {
                Some(v) => self.doc.dom.set_attr(bp, k, v),
                None => {
                    self.doc.dom.remove_attr(bp, k);
                }
            }
        }
        self.commit("Text Box", false);
        true
    }

    /// The selected text box's text: one run property set on every run
    /// (WordArt Styles > Text Fill / Text Outline).
    pub fn object_text_prop(&mut self, edit: &super::PropEdit) -> bool {
        let Some(node) = self.sel_obj else { return false };
        let Some(content) = crate::pictures::find(&self.doc.dom, node, "w:txbxContent") else { return false };
        fn runs(dom: &XmlDoc, n: NodeId, out: &mut Vec<NodeId>) {
            for c in dom.elements(n) {
                if dom.is(c, "w:r") {
                    out.push(c);
                } else {
                    runs(dom, c, out);
                }
            }
        }
        let mut rs = Vec::new();
        runs(&self.doc.dom, content, &mut rs);
        self.begin();
        for r in rs {
            let dom = &mut self.doc.dom;
            let rpr = super::ensure_child_first(dom, r, "w:rPr");
            super::set_prop_child(dom, rpr, edit, super::RPR_ORDER);
        }
        self.commit("Text Fill", false);
        true
    }

    /// Keep wp:effectExtent (the room effects take) up to date.
    fn update_effect_extent(&mut self) {
        let Some((sppr, blip, holder)) = self.sel_props() else { return };
        let colors = self.doc.styles.theme.colors.clone();
        let fx = crate::effects::parse(&self.doc.dom, Some(sppr), blip, &colors);
        let dom = &self.doc.dom;
        let ext = dom.child(holder, "wp:extent");
        let w = ext.and_then(|e| dom.attr(e, "cx")).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) / EMU;
        let h = ext.and_then(|e| dom.attr(e, "cy")).and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.0) / EMU;
        // an outline's outer half counts too
        let line = dom.child(sppr, "a:ln").and_then(|l| dom.attr(l, "w")).and_then(|v| v.parse::<f64>().ok())
            .map(|v| v / EMU / 2.0).unwrap_or(0.0);
        let mut e = fx.extents(w, h);
        for v in e.iter_mut() {
            *v = v.max(line);
        }
        let dom = &mut self.doc.dom;
        let ee = match dom.child(holder, "wp:effectExtent") {
            Some(n) => n,
            None => {
                let n = dom.new_element("wp:effectExtent", &[]);
                let idx = ext.and_then(|x| dom.index_in_parent(x)).map(|i| i + 1).unwrap_or(0);
                dom.insert(holder, idx, n);
                n
            }
        };
        for (k, v) in ["l", "t", "r", "b"].iter().zip(e) {
            dom.set_attr(ee, k, &emu(v));
        }
    }
}
