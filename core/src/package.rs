//! The .docx package: a zip of parts. Parts Folio never touches are written
//! back byte for byte; XML parts are parsed when first needed.

use crate::xml::{XmlDoc, XmlError};
use std::collections::{BTreeMap, HashMap};
use std::io::{Cursor, Read, Write};

#[derive(Debug)]
pub enum PkgError {
    Io(std::io::Error),
    Zip(String),
    Xml(XmlError),
    Missing(String),
}

impl std::fmt::Display for PkgError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PkgError::Io(e) => write!(f, "{}", e),
            PkgError::Zip(e) => write!(f, "not a valid document package: {}", e),
            PkgError::Xml(e) => write!(f, "{}", e),
            PkgError::Missing(p) => write!(f, "the document has no {}", p),
        }
    }
}

impl From<std::io::Error> for PkgError {
    fn from(e: std::io::Error) -> Self {
        PkgError::Io(e)
    }
}
impl From<XmlError> for PkgError {
    fn from(e: XmlError) -> Self {
        PkgError::Xml(e)
    }
}

struct Entry {
    name: String,
    raw: Vec<u8>,
    deflate: bool,
}

#[derive(Clone, Debug)]
pub struct Rel {
    pub id: String,
    pub kind: String,
    pub target: String,
    pub external: bool,
}

pub struct Package {
    entries: Vec<Entry>,
    xml: HashMap<String, XmlDoc>,
    dirty: std::collections::HashSet<String>,
}

pub const REL_OFFICE_DOC: &str =
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument";

impl Package {
    pub fn open(bytes: &[u8]) -> Result<Package, PkgError> {
        let mut zip = zip::ZipArchive::new(Cursor::new(bytes)).map_err(|e| PkgError::Zip(e.to_string()))?;
        let mut entries = Vec::with_capacity(zip.len());
        for i in 0..zip.len() {
            let mut f = zip.by_index(i).map_err(|e| PkgError::Zip(e.to_string()))?;
            if f.is_dir() {
                continue;
            }
            let name = f.name().to_string();
            // no path tricks inside the package
            if name.contains("..") {
                continue;
            }
            let deflate = f.compression() != zip::CompressionMethod::Stored;
            let mut raw = Vec::with_capacity(f.size() as usize);
            f.read_to_end(&mut raw)?;
            entries.push(Entry { name, raw, deflate });
        }
        Ok(Package { entries, xml: HashMap::new(), dirty: Default::default() })
    }

    pub fn from_parts(parts: Vec<(String, Vec<u8>)>) -> Package {
        let entries = parts.into_iter().map(|(name, raw)| Entry { name, raw, deflate: true }).collect();
        Package { entries, xml: HashMap::new(), dirty: Default::default() }
    }

    pub fn has(&self, name: &str) -> bool {
        self.entries.iter().any(|e| e.name == name)
    }

    pub fn part_names(&self) -> Vec<String> {
        self.entries.iter().map(|e| e.name.clone()).collect()
    }

    pub fn raw(&self, name: &str) -> Option<&[u8]> {
        self.entries.iter().find(|e| e.name == name).map(|e| e.raw.as_slice())
    }

    /// Parsed XML of a part (parsed on first use).
    pub fn xml(&mut self, name: &str) -> Result<&XmlDoc, PkgError> {
        self.load(name)?;
        Ok(&self.xml[name])
    }

    /// Mutable XML of a part: the part will be re-serialized on save.
    pub fn xml_mut(&mut self, name: &str) -> Result<&mut XmlDoc, PkgError> {
        self.load(name)?;
        self.dirty.insert(name.to_string());
        Ok(self.xml.get_mut(name).unwrap())
    }

    pub fn take_xml(&mut self, name: &str) -> Result<XmlDoc, PkgError> {
        self.load(name)?;
        self.dirty.insert(name.to_string());
        Ok(self.xml.remove(name).unwrap())
    }

    pub fn put_xml(&mut self, name: &str, doc: XmlDoc) {
        if !self.has(name) {
            self.entries.push(Entry { name: name.to_string(), raw: Vec::new(), deflate: true });
        }
        self.dirty.insert(name.to_string());
        self.xml.insert(name.to_string(), doc);
    }

    pub fn put_raw(&mut self, name: &str, raw: Vec<u8>) {
        self.xml.remove(name);
        self.dirty.remove(name);
        if let Some(e) = self.entries.iter_mut().find(|e| e.name == name) {
            e.raw = raw;
        } else {
            self.entries.push(Entry { name: name.to_string(), raw, deflate: true });
        }
    }

    /// Take a part out of the package.
    pub fn remove(&mut self, name: &str) {
        self.entries.retain(|e| e.name != name);
        self.xml.remove(name);
        self.dirty.remove(name);
    }

    /// A part's bytes as they would be saved now.
    pub fn bytes(&self, name: &str) -> Option<Vec<u8>> {
        let e = self.entries.iter().find(|e| e.name == name)?;
        if self.dirty.contains(name) {
            if let Some(d) = self.xml.get(name) {
                return Some(d.serialize().into_bytes());
            }
        }
        Some(e.raw.clone())
    }

    fn load(&mut self, name: &str) -> Result<(), PkgError> {
        if self.xml.contains_key(name) {
            return Ok(());
        }
        let raw = self.raw(name).ok_or_else(|| PkgError::Missing(name.to_string()))?;
        let doc = XmlDoc::parse(raw)?;
        self.xml.insert(name.to_string(), doc);
        Ok(())
    }

    // ------------------------------------------------------------ relations
    pub fn rels_name(part: &str) -> String {
        match part.rfind('/') {
            Some(i) => format!("{}/_rels/{}.rels", &part[..i], &part[i + 1..]),
            None => format!("_rels/{}.rels", part),
        }
    }

    pub fn rels(&mut self, part: &str) -> Vec<Rel> {
        let name = Self::rels_name(part);
        let Ok(doc) = self.xml(&name) else { return Vec::new() };
        doc.elements(doc.root)
            .map(|r| Rel {
                id: doc.attr(r, "Id").unwrap_or("").to_string(),
                kind: doc.attr(r, "Type").unwrap_or("").to_string(),
                target: doc.attr(r, "Target").unwrap_or("").to_string(),
                external: doc.attr(r, "TargetMode") == Some("External"),
            })
            .collect()
    }

    /// The target to write in `part`'s relationships for `target_part`.
    pub fn relative_target(part: &str, target_part: &str) -> String {
        let base = match part.rfind('/') {
            Some(i) => &part[..i + 1],
            None => "",
        };
        match target_part.strip_prefix(base) {
            Some(rest) => rest.to_string(),
            None => format!("/{}", target_part),
        }
    }

    /// Where relationship `rid` of `part` points (as written).
    pub fn rel_target(&self, part: &str, rid: &str) -> Option<String> {
        let name = Self::rels_name(part);
        let find = |x: &XmlDoc| x.elements(x.root).find(|&r| x.attr(r, "Id") == Some(rid))
            .and_then(|r| x.attr(r, "Target").map(|s| s.to_string()));
        if let Some(x) = self.xml.get(&name) {
            return find(x);
        }
        let x = XmlDoc::parse(self.raw(&name)?).ok()?;
        find(&x)
    }

    /// The package path a relationship of `part` points to.
    pub fn resolve(part: &str, target: &str) -> String {
        if let Some(t) = target.strip_prefix('/') {
            return t.to_string();
        }
        let base = match part.rfind('/') {
            Some(i) => &part[..i],
            None => "",
        };
        let mut segs: Vec<&str> = if base.is_empty() { Vec::new() } else { base.split('/').collect() };
        for s in target.split('/') {
            match s {
                ".." => {
                    segs.pop();
                }
                "." | "" => {}
                s => segs.push(s),
            }
        }
        segs.join("/")
    }

    /// The main document part (word/document.xml normally).
    pub fn main_part(&mut self) -> Result<String, PkgError> {
        for r in self.rels("") {
            if r.kind == REL_OFFICE_DOC
                || r.kind.ends_with("/officeDocument")
            {
                return Ok(Self::resolve("", &r.target));
            }
        }
        if self.has("word/document.xml") {
            return Ok("word/document.xml".into());
        }
        Err(PkgError::Missing("main document part".into()))
    }

    /// Find the part related to `part` by relationship type suffix
    /// (e.g. "/styles").
    pub fn related(&mut self, part: &str, kind_suffix: &str) -> Option<String> {
        self.rels(part)
            .into_iter()
            .find(|r| r.kind.ends_with(kind_suffix) && !r.external)
            .map(|r| Self::resolve(part, &r.target))
    }

    pub fn add_rel(&mut self, part: &str, kind: &str, target: &str) -> String {
        let name = Self::rels_name(part);
        if !self.has(&name) {
            let doc = XmlDoc::with_root(
                "Relationships",
                &[("xmlns", "http://schemas.openxmlformats.org/package/2006/relationships")],
            );
            self.put_xml(&name, doc);
        }
        let doc = self.xml_mut(&name).unwrap();
        let mut n = 1;
        let ids: Vec<String> =
            doc.elements(doc.root).filter_map(|r| doc.attr(r, "Id").map(|s| s.to_string())).collect();
        while ids.contains(&format!("rId{}", n)) {
            n += 1;
        }
        let id = format!("rId{}", n);
        let el = doc.new_element("Relationship", &[("Id", &id), ("Type", kind), ("Target", target)]);
        let root = doc.root;
        doc.append(root, el);
        id
    }

    /// A content type for every part with extension `ext`.
    pub fn ensure_default(&mut self, ext: &str, ctype: &str) {
        let Ok(doc) = self.xml_mut("[Content_Types].xml") else { return };
        let root = doc.root;
        let has = doc.children_named(root, "Default")
            .any(|d| doc.attr(d, "Extension").map(|e| e.eq_ignore_ascii_case(ext)).unwrap_or(false));
        if !has {
            let el = doc.new_element("Default", &[("Extension", ext), ("ContentType", ctype)]);
            doc.insert(root, 0, el);
        }
    }

    pub fn set_content_type(&mut self, part: &str, ctype: &str) {
        let Ok(doc) = self.xml_mut("[Content_Types].xml") else { return };
        let pname = format!("/{}", part);
        let root = doc.root;
        for o in doc.children_named(root, "Override").collect::<Vec<_>>() {
            if doc.attr(o, "PartName") == Some(&pname) {
                doc.set_attr(o, "ContentType", ctype);
                return;
            }
        }
        let el = doc.new_element("Override", &[("PartName", &pname), ("ContentType", ctype)]);
        doc.append(root, el);
    }

    // ------------------------------------------------------------ saving
    pub fn write(&self) -> Result<Vec<u8>, PkgError> {
        let mut buf = Cursor::new(Vec::new());
        {
            let mut zip = zip::ZipWriter::new(&mut buf);
            // [Content_Types].xml first, as Word writes it
            let mut order: Vec<&Entry> = self.entries.iter().collect();
            order.sort_by_key(|e| if e.name == "[Content_Types].xml" { 0 } else { 1 });
            for e in order {
                let opts = zip::write::SimpleFileOptions::default().compression_method(if e.deflate {
                    zip::CompressionMethod::Deflated
                } else {
                    zip::CompressionMethod::Stored
                });
                zip.start_file(e.name.as_str(), opts).map_err(|e| PkgError::Zip(e.to_string()))?;
                if self.dirty.contains(&e.name) {
                    if let Some(doc) = self.xml.get(&e.name) {
                        zip.write_all(doc.serialize().as_bytes())?;
                        continue;
                    }
                }
                zip.write_all(&e.raw)?;
            }
            zip.finish().map_err(|e| PkgError::Zip(e.to_string()))?;
        }
        Ok(buf.into_inner())
    }

    pub fn save(&self, path: &str) -> Result<(), PkgError> {
        let data = self.write()?;
        // write next to the file, then replace it: a failed save never
        // leaves a half-written document
        let tmp = format!("{}.folio-tmp", path);
        std::fs::write(&tmp, &data)?;
        std::fs::rename(&tmp, path)?;
        Ok(())
    }

    /// Media parts nothing points at any more, dropped, with the relationships that named them
    /// (W4-04). Returns how many parts went.
    ///
    /// Changing a picture writes a new part and leaves the old one in the file: Remove Background,
    /// Compress Pictures and turning a 3D model all do it, and a document edited for a while grows
    /// a tail of pictures nobody can see. A relationship counts as used when its own part mentions
    /// its Id; the ids come from the relationships themselves rather than from a guess at which
    /// attributes carry them, so this does not depend on knowing every attribute in the format.
    pub fn prune_media(&mut self) -> usize {
        let parts = self.part_names();
        let mut keep: std::collections::HashSet<String> = std::collections::HashSet::new();
        let mut drop_rels: Vec<(String, String)> = Vec::new();   // (part, rel id)
        for part in &parts {
            if part.ends_with(".rels") {
                continue;
            }
            let rels = self.rels(part);
            if rels.is_empty() {
                continue;
            }
            // Anything we cannot read keeps whatever it points at. A picture is only dropped on
            // the word of a part we have actually read and searched: losing one would be worse
            // than carrying it.
            let text = if Self::is_xml(part) {
                self.xml(part).ok().map(|d| d.serialize())
            } else {
                None
            };
            for r in rels {
                if r.external || r.id.is_empty() {
                    continue;
                }
                let target = Self::resolve(part, &r.target);
                let media = target.contains("/media/") || target.starts_with("media/");
                match &text {
                    Some(t) if media && !Self::mentions(t, &r.id) => {
                        drop_rels.push((part.clone(), r.id.clone()))
                    }
                    _ => {
                        keep.insert(target);
                    }
                }
            }
        }
        for (part, id) in &drop_rels {
            let name = Self::rels_name(part);
            if let Ok(doc) = self.xml_mut(&name) {
                let gone: Vec<_> = doc.elements(doc.root)
                    .filter(|&n| doc.attr(n, "Id") == Some(id.as_str())).collect();
                for n in gone {
                    doc.detach(n);
                }
            }
        }
        let mut went = 0;
        for part in parts {
            let media = part.contains("/media/") || part.starts_with("media/");
            if media && !keep.contains(&part) {
                self.remove(&part);
                went += 1;
            }
        }
        went
    }

    /// Whether a part mentions a relationship id as a whole attribute value.
    fn mentions(text: &str, id: &str) -> bool {
        let mut from = 0;
        while let Some(i) = text[from..].find(id) {
            let at = from + i;
            let end = at + id.len();
            let before = text[..at].chars().next_back();
            let after = text[end..].chars().next();
            // "rId7" must not match inside "rId70", and must sit in quotes
            let whole = !after.map(|c| c.is_ascii_alphanumeric()).unwrap_or(false)
                && matches!(before, Some('"') | Some('\''));
            if whole {
                return true;
            }
            from = end;
        }
        false
    }

    fn is_xml(name: &str) -> bool {
        name.ends_with(".xml") || name.ends_with(".rels")
    }

    /// Parts as (name, bytes), with modified XML serialized.
    pub fn parts(&self) -> BTreeMap<String, Vec<u8>> {
        let mut out = BTreeMap::new();
        for e in &self.entries {
            let data = match (self.dirty.contains(&e.name), self.xml.get(&e.name)) {
                (true, Some(d)) => d.serialize().into_bytes(),
                _ => e.raw.clone(),
            };
            out.insert(e.name.clone(), data);
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prune_media_drops_what_nothing_points_at() {
        // a document with two pictures in the file but only one in the text (W4-04)
        let mut zip = Vec::new();
        {
            let mut w = zip::ZipWriter::new(std::io::Cursor::new(&mut zip));
            let o = zip::write::FileOptions::<()>::default();
            let add = |w: &mut zip::ZipWriter<std::io::Cursor<&mut Vec<u8>>>, n: &str, b: &[u8]| {
                use std::io::Write;
                w.start_file(n, o).unwrap();
                w.write_all(b).unwrap();
            };
            add(&mut w, "[Content_Types].xml",
                br#"<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="png" ContentType="image/png"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/></Types>"#);
            add(&mut w, "_rels/.rels",
                br#"<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>"#);
            add(&mut w, "word/document.xml",
                br#"<?xml version="1.0"?><w:document xmlns:w="w" xmlns:r="r"><w:body><w:p><w:drawing><a:blip r:embed="rId5"/></w:drawing></w:p></w:body></w:document>"#);
            add(&mut w, "word/_rels/document.xml.rels",
                br#"<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/><Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/><Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/></Relationships>"#);
            add(&mut w, "word/media/image1.png", b"one");
            add(&mut w, "word/media/image2.png", b"two");
            w.finish().unwrap();
        }
        let mut pkg = Package::open(&zip).unwrap();
        assert!(pkg.has("word/media/image2.png"));
        let went = pkg.prune_media();
        assert_eq!(went, 1, "only the picture nothing points at goes");
        assert!(pkg.has("word/media/image1.png"), "the one in the text stays");
        assert!(!pkg.has("word/media/image2.png"), "the one nothing points at goes");
        let rels = pkg.rels("word/document.xml");
        assert!(rels.iter().any(|r| r.id == "rId5"), "its relationship stays");
        assert!(!rels.iter().any(|r| r.id == "rId6"), "the orphan relationship goes");
        assert!(rels.iter().any(|r| r.id == "rId9"), "a link to the web is not a picture");
        assert_eq!(pkg.prune_media(), 0, "nothing left to drop the second time");
    }

    #[test]
    fn a_relationship_id_is_matched_whole() {
        assert!(Package::mentions(r#"<a r:embed="rId7"/>"#, "rId7"));
        assert!(!Package::mentions(r#"<a r:embed="rId70"/>"#, "rId7"));
        assert!(!Package::mentions(r#"<a r:embed="xrId7"/>"#, "rId7"));
    }

    #[test]
    fn resolve_paths() {
        assert_eq!(Package::resolve("word/document.xml", "styles.xml"), "word/styles.xml");
        assert_eq!(Package::resolve("word/document.xml", "../customXml/item1.xml"), "customXml/item1.xml");
        assert_eq!(Package::resolve("", "word/document.xml"), "word/document.xml");
        assert_eq!(Package::rels_name("word/document.xml"), "word/_rels/document.xml.rels");
        assert_eq!(Package::rels_name(""), "_rels/.rels");
    }
}
