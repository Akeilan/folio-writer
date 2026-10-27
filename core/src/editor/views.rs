//! Views other than Print Layout: what Outline view and the Immersive
//! Reader show of the body's paragraphs, moving paragraphs and sections, and
//! hyphenation points (syllables).

use super::{Editor, Pos};
use crate::xml::NodeId;

/// One body paragraph for the outline: node, text, level (1-9 headings, 10
/// body text), size (points), bold, italic, colour (-1 automatic), font.
pub type OutlinePara = (NodeId, String, i32, f64, bool, bool, i64, String);

impl Editor {
    pub fn set_view_mode(&mut self, mode: u8, width: f64) {
        if mode == self.view_mode && (mode != 2 || (width - self.web_width).abs() < 0.5) {
            return;
        }
        self.view_mode = mode;
        if width > 50.0 {
            self.web_width = width;
        }
        self.sel_obj = None;
        self.cache.clear();
        let p = self.caret.para;
        self.relayout();
        if self.pidx(&p).is_none() {
            if let Some(first) = self.layout.paras.first() {
                self.caret = Pos { para: first.node, off: 0 };
                self.anchor = self.caret;
            }
        }
    }

    /// The body's paragraphs (tables left out) for Outline view.
    pub fn outline_paras(&self) -> Vec<OutlinePara> {
        let dom = &self.doc.dom;
        let mut out = Vec::new();
        for b in &self.doc.blocks {
            if b.kind != crate::document::BlockKind::Para {
                continue;
            }
            let p = b.node;
            let (pp, rp) = self.doc.para_props(p);
            let level = pp.outline_lvl.map(|l| l as i32 + 1).filter(|l| *l <= 9).unwrap_or(10);
            let text: String = self.doc.para_text(p).chars().filter(|c| *c != '\u{fffc}').collect();
            let size = rp.size.map(|s| s as f64 / 2.0).unwrap_or(11.0);
            let color = match &rp.color {
                Some(crate::props::ColorVal::Rgb(c)) => *c as i64,
                _ => -1,
            };
            let family = rp.font_ascii.clone().unwrap_or_default();
            let _ = dom;
            out.push((p, text, level, size, rp.bold.unwrap_or(false), rp.italic.unwrap_or(false), color, family));
        }
        out
    }

    /// Move paragraphs (in order, siblings) before or after `target`.
    pub fn move_paras(&mut self, nodes: &[NodeId], target: NodeId, after: bool) -> bool {
        if nodes.is_empty() || nodes.contains(&target) {
            return false;
        }
        let dom = &self.doc.dom;
        let Some(parent) = dom.parent(target) else { return false };
        if nodes.iter().any(|&n| dom.parent(n) != Some(parent)) {
            return false;
        }
        let caret_para = self.caret.para;
        self.begin();
        let dom = &mut self.doc.dom;
        for &n in nodes {
            dom.detach(n);
        }
        let mut idx = dom.index_in_parent(target).unwrap_or(0) + if after { 1 } else { 0 };
        // after a heading's whole section
        for &n in nodes {
            dom.insert(parent, idx, n);
            idx += 1;
        }
        self.doc.scan();
        let keep = nodes.contains(&caret_para);
        self.commit("Move", false);
        if keep {
            self.caret = Pos { para: caret_para, off: 0 };
            self.anchor = self.caret;
        }
        true
    }

    /// The paragraphs of a heading's section: it and what follows up to the
    /// next heading of its level or higher.
    pub fn section_paras(&self, head: NodeId) -> Vec<NodeId> {
        let paras = self.outline_paras();
        let Some(i) = paras.iter().position(|p| p.0 == head) else { return Vec::new() };
        let lvl = paras[i].2;
        let mut out = vec![head];
        if lvl == 10 {
            return out;
        }
        for p in &paras[i + 1..] {
            if p.2 <= lvl {
                break;
            }
            out.push(p.0);
        }
        out
    }

    /// Replace a paragraph's text (Outline view's typing).
    pub fn set_para_text(&mut self, p: NodeId, text: &str) -> bool {
        let Some(pl) = self.para_layout(p) else { return false };
        let len = pl.text_len;
        self.caret = Pos { para: p, off: 0 };
        self.anchor = Pos { para: p, off: len };
        self.type_text(text);
        true
    }

    /// Where a word can be hyphenated (character offsets), for syllables.
    pub fn hyphen_points(&self, word: &str, lang: &str) -> Vec<usize> {
        crate::hyph::patterns(lang).map(|p| p.points(word)).unwrap_or_default()
    }
}

impl Editor {
    /// The `n`th body table's cells: rows of cells, each its paragraphs.
    pub fn table_cells(&self, n: usize) -> Vec<Vec<Vec<NodeId>>> {
        let dom = &self.doc.dom;
        let Some(t) = self.doc.blocks.iter().filter(|b| b.kind == crate::document::BlockKind::Table).nth(n).map(|b| b.node) else {
            return Vec::new();
        };
        let mut out = Vec::new();
        for tr in dom.elements(t).filter(|&r| dom.is(r, "w:tr")) {
            let mut row = Vec::new();
            for tc in dom.elements(tr).filter(|&c| dom.is(c, "w:tc")) {
                row.push(dom.elements(tc).filter(|&p| dom.is(p, "w:p")).collect());
            }
            out.push(row);
        }
        out
    }
}

fn lum(c: u32) -> f64 {
    let ch = |v: u32| {
        let v = v as f64 / 255.0;
        if v <= 0.03928 { v / 12.92 } else { ((v + 0.055) / 1.055).powf(2.4) }
    };
    0.2126 * ch((c >> 16) & 255) + 0.7152 * ch((c >> 8) & 255) + 0.0722 * ch(c & 255)
}

fn contrast(a: u32, b: u32) -> f64 {
    let (la, lb) = (lum(a), lum(b));
    (la.max(lb) + 0.05) / (la.min(lb) + 0.05)
}

fn highlight_rgb(name: &str) -> Option<u32> {
    Some(match name {
        "yellow" => 0xFFFF00, "green" => 0x00FF00, "cyan" => 0x00FFFF, "magenta" => 0xFF00FF,
        "blue" => 0x0000FF, "red" => 0xFF0000, "darkBlue" => 0x000080, "darkCyan" => 0x008080,
        "darkGreen" => 0x008000, "darkMagenta" => 0x800080, "darkRed" => 0x800000,
        "darkYellow" => 0x808000, "darkGray" => 0x808080, "lightGray" => 0xC0C0C0, "black" => 0,
        "white" => 0xFFFFFF,
        _ => return None,
    })
}

impl Editor {
    /// Check Accessibility: (category, label, paragraph or object node).
    pub fn accessibility_issues(&self) -> Vec<(String, String, NodeId)> {
        let dom = &self.doc.dom;
        let mut out: Vec<(String, String, NodeId)> = Vec::new();
        // objects
        for (node, name, kind, _vis) in self.objects_list() {
            if kind == "Equation" || name.starts_with("Ink ") {
                continue;
            }
            let holder = dom.child(node, "wp:inline").or_else(|| dom.child(node, "wp:anchor"));
            let dp = holder.and_then(|h| dom.child(h, "wp:docPr"));
            let file = regex::Regex::new(r"(?i)\.(png|jpe?g|gif|bmp|svg|webp|tiff?|emf|wmf)$").unwrap();
            let desc = dp.map(|d| {
                let a = dom.attr(d, "descr").unwrap_or("").trim().to_string();
                let t = dom.attr(d, "title").unwrap_or("").trim().to_string();
                [a, t].into_iter().find(|v| !v.is_empty() && !file.is_match(v)).unwrap_or_default()
            }).unwrap_or_default();
            let decorative = dp.map_or(false, |d| crate::pictures::find(dom, d, "adec:decorative")
                .map_or(false, |e| dom.attr(e, "val") == Some("1")));
            let text_box = kind == "Text Box" || crate::pictures::find(dom, node, "w:txbxContent").is_some();
            if desc.is_empty() && !decorative && !text_box {
                out.push(("Missing alternative text".into(), name.clone(), node));
            }
            if holder.map_or(false, |h| dom.is(h, "wp:anchor")) && !text_box {
                out.push(("Object not inline".into(), name.clone(), node));
            }
        }
        // tables: a header row
        let mut tn = 0;
        for b in &self.doc.blocks {
            if b.kind != crate::document::BlockKind::Table {
                continue;
            }
            tn += 1;
            let first = dom.elements(b.node).find(|&r| dom.is(r, "w:tr"));
            let hdr = first.and_then(|r| dom.child(r, "w:trPr")).and_then(|p| dom.child(p, "w:tblHeader")).is_some();
            if !hdr {
                let p = first.and_then(|r| crate::pictures::find(dom, r, "w:p")).unwrap_or(b.node);
                out.push(("Missing table header".into(), format!("Table {tn}"), p));
            }
        }
        // paragraphs
        let mut last_level = 0;
        let mut empties = 0;
        for b in &self.doc.blocks {
            if b.kind != crate::document::BlockKind::Para {
                continue;
            }
            let p = b.node;
            let (pp, base) = self.doc.para_props(p);
            let text = self.doc.para_text(p);
            let t = text.trim();
            if let Some(l) = pp.outline_lvl {
                let lvl = l as i32 + 1;
                if lvl <= 9 && !t.is_empty() {
                    if last_level > 0 && lvl > last_level + 1 {
                        out.push(("Skipped heading level".into(), t.chars().take(40).collect(), p));
                    }
                    last_level = lvl;
                }
            }
            if t.is_empty() && !text.contains('\u{fffc}') {
                empties += 1;
                if empties == 3 {
                    out.push(("Repeated blank characters".into(), "Empty paragraphs".into(), p));
                }
                continue;
            }
            empties = 0;
            if text.contains("    ") || text.contains("\t\t\t") {
                out.push(("Repeated blank characters".into(), t.chars().take(40).collect(), p));
            }
            let pbg = pp.shading;
            let mut links: Vec<(NodeId, String)> = Vec::new();
            let mut low_contrast = false;
            for pc in self.doc.para_pieces(p, &base) {
                let crate::document::Item::Text(s) = &pc.item else { continue };
                if s.trim().is_empty() {
                    continue;
                }
                if let Some(l) = pc.link {
                    match links.iter_mut().find(|x| x.0 == l) {
                        Some(x) => x.1.push_str(s),
                        None => links.push((l, s.clone())),
                    }
                }
                if let Some(crate::props::ColorVal::Rgb(c)) = &pc.rpr.color {
                    let bg = pc.rpr.highlight.as_deref().and_then(highlight_rgb)
                        .or(pc.rpr.shading).or(pbg).unwrap_or(0xFFFFFF);
                    if contrast(*c, bg) < 4.5 {
                        low_contrast = true;
                    }
                }
            }
            if low_contrast {
                out.push(("Hard-to-read text contrast".into(), t.chars().take(40).collect(), p));
            }
            for (_l, s) in links {
                let low = s.trim().to_lowercase();
                if matches!(low.as_str(), "click here" | "here" | "link" | "this link" | "read more" | "more")
                    || low.starts_with("http://") || low.starts_with("https://") || low.starts_with("www.") {
                    out.push(("Unclear hyperlink text".into(), s.trim().chars().take(40).collect(), p));
                }
            }
        }
        if self.core_prop_pub("dc:title").map_or(true, |v| v.trim().is_empty()) {
            out.push(("Missing document title".into(), "Document".into(), self.doc.body));
        }
        out
    }
}
