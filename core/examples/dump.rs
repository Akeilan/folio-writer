//! Print what lands on pages a..b.
use folio_core::document::Document;
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let (p0, p1): (usize, usize) = (a[2].parse().unwrap(), a[3].parse().unwrap());
    let mut fonts = FontCache::new();
    let doc = Document::open(&std::fs::read(&a[1]).unwrap()).unwrap();
    let lay = layout_document(&doc, &mut fonts);
    for pg in p0..=p1.min(lay.pages.len()) {
        let page = &lay.pages[pg - 1];
        println!("=== page {pg} ({}x{} top {} bottom {}) cells {}", page.width, page.height, page.top, page.bottom, page.cells.len());
        for c in page.cells.iter().take(12) {
            println!("   cell x {:.1} y {:.1} w {:.1} h {:.1}", c.x, c.y, c.w, c.h);
        }
        let mut last = usize::MAX;
        for l in &page.lines {
            let p = &lay.paras[l.para];
            let line = &p.lines[l.line];
            let t: String = doc.para_text(p.node).chars().skip(line.pos_start).take((line.pos_end - line.pos_start).min(50)).collect();
            let mark = if l.para != last { format!("P{}", l.para) } else { "  ".into() };
            last = l.para;
            println!("{mark:>6} y {:7.1} h {:5.1} x {:6.1} b{:.0}/a{:.0} kn{} | {}", l.y, line.height, l.x, p.before, p.after,
                p.props.keep_next.unwrap_or(false) as u8, t.replace('\n', " "));
        }
    }
}
