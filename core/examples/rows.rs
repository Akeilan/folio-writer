//! Table rows: the page the original started each row on (from
//! w:lastRenderedPageBreak in its cells) against ours.
use folio_core::document::{BlockKind, Document};
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;
use folio_core::xml::{Kind, NodeId, XmlDoc};

fn count(d: &XmlDoc, n: NodeId) -> usize {
    let mut k = 0;
    for &c in d.children(n) {
        if let Kind::Element { name, .. } = &d.node(c).kind {
            if name == "w:lastRenderedPageBreak" { k += 1 } else if name != "w:tbl" { k += count(d, c) }
        }
    }
    k
}

fn main() {
    let path = std::env::args().nth(1).unwrap();
    let mut fonts = FontCache::new();
    let doc = Document::open(&std::fs::read(&path).unwrap()).unwrap();
    let lay = layout_document(&doc, &mut fonts);
    // the last page each paragraph has a line on
    let mut para_last = std::collections::HashMap::new();
    for (pg, page) in lay.pages.iter().enumerate() {
        for l in &page.lines { para_last.insert(lay.paras[l.para].node, pg + 1); }
    }
    fn paras_in(d: &XmlDoc, n: NodeId, out: &mut Vec<NodeId>) {
        for c in d.elements(n) {
            if d.is(c, "w:p") { out.push(c) } else { paras_in(d, c, out) }
        }
    }
    let dom = &doc.dom;
    let quiet = std::env::args().nth(2).is_some();
    let mut wp = 1;
    let mut shown = 0;
    let (mut agree, mut total) = (0, 0);
    for b in &doc.blocks {
        if b.kind == BlockKind::Para { wp += count(dom, b.node); continue; }
        for (ri, r) in dom.children_named(b.node, "w:tr").enumerate() {
            let hits = count(dom, r);
            let mut ps = Vec::new();
            paras_in(dom, r, &mut ps);
            let ours = ps.iter().filter_map(|p| para_last.get(p)).max().copied().unwrap_or(0);
            wp += hits;
            total += 1;
            if ours == wp { agree += 1; }
            if !quiet && ours != wp && shown < 40 {
                println!("row {ri}: word ends p{wp} ours p{ours}");
                shown += 1;
            }
        }
    }
    if quiet { println!("ROWS {agree} {total} {path}"); }
}
