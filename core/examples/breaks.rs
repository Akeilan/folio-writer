//! First paragraph whose page differs from where the original put it
//! (by w:lastRenderedPageBreak).
use folio_core::document::{BlockKind, Document};
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;
use folio_core::xml::{Kind, NodeId, XmlDoc};

fn walk(d: &XmlDoc, n: NodeId, chars: &mut usize, hits: &mut Vec<usize>) {
    for &c in d.children(n) {
        match &d.node(c).kind {
            Kind::Element { name, .. } => {
                if name == "w:lastRenderedPageBreak" { hits.push(*chars); }
                else if name == "w:t" { *chars += d.text(c).chars().count(); }
                else if name == "w:tab" || name == "w:br" { *chars += 1; }
                else { walk(d, c, chars, hits) }
            }
            _ => {}
        }
    }
}

fn main() {
    let path = std::env::args().nth(1).unwrap();
    let show: usize = std::env::args().nth(2).and_then(|s| s.parse().ok()).unwrap_or(3);
    let quiet = show == 0;
    let mut agree = 0usize;
    let mut total = 0usize;
    let mut fonts = FontCache::new();
    let doc = Document::open(&std::fs::read(&path).unwrap()).unwrap();
    let lay = layout_document(&doc, &mut fonts);
    // our page of each paragraph's first line
    let mut first_page = std::collections::HashMap::new();
    for (pg, page) in lay.pages.iter().enumerate() {
        for l in &page.lines {
            first_page.entry(l.para).or_insert(pg + 1);
        }
    }
    let mut word_page = 1;
    let mut bad = 0;
    let mut last_diff: i64 = 0;
    let mut first_page_tbl = std::collections::HashMap::new();
    for (pg, page) in lay.pages.iter().enumerate() {
        for c in &page.cells { first_page_tbl.entry(c.cell).or_insert(pg + 1); }
    }
    for (bi, b) in doc.blocks.iter().enumerate() {
        let mut hits = Vec::new();
        let mut chars = 0;
        walk(&doc.dom, b.node, &mut chars, &mut hits);
        let starts_new = hits.first() == Some(&0) && b.kind == BlockKind::Para;
        let wp = word_page + starts_new as usize;
        let ours_any = if let Some(pi) = lay.block_para[bi] { first_page.get(&pi).copied().unwrap_or(0) } else {
            // first cell of the table
            let dom = &doc.dom;
            dom.children_named(b.node, "w:tr").next().and_then(|r| dom.children_named(r, "w:tc").next())
                .and_then(|c| first_page_tbl.get(&c).copied()).unwrap_or(0)
        };
        if ours_any > 0 && lay.block_para[bi].is_some() {
            total += 1;
            if ours_any == wp { agree += 1; }
        }
        if !quiet && ours_any > 0 && ours_any as i64 - wp as i64 != last_diff {
            last_diff = ours_any as i64 - wp as i64;
            let t: String = doc.para_text(b.node).chars().take(40).collect();
            println!("  diff {last_diff:+} at block {bi} ({:?}) word p{wp} ours p{ours_any} | {t}", b.kind);
        }
        if let Some(pi) = lay.block_para[bi] {
            let ours = first_page.get(&pi).copied().unwrap_or(0);
            if ours == 0 { word_page += hits.len(); continue; }
            if ours != wp && bad < show {
                bad += 1;
                let p = &lay.paras[pi];
                let t: String = doc.para_text(b.node).chars().take(60).collect();
                println!("block {bi}: word p{wp} ours p{ours} lines {} h {:.1} bef {:.1} aft {:.1} style {:?} kn {:?} | {t}",
                    p.lines.len(), p.height(), p.before, p.after, p.props.style, p.props.keep_next);
            }
        }
        word_page += hits.len();
    }
    if quiet {
        println!("AGREE {agree} {total} {}", path);
    } else {
        println!("pages: ours {} word(lrpb) {}", lay.pages.len(), word_page);
    }
}
