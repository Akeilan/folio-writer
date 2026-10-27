//! Lines per page: plines <docx>
use folio_core::document::Document;
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let mut fonts = FontCache::new();
    let doc = Document::open(&std::fs::read(&a[1]).unwrap()).unwrap();
    let lay = layout_document(&doc, &mut fonts);
    for (i, pg) in lay.pages.iter().enumerate() {
        println!("page {} floats {} body {:.1}-{:.1} hdr {:?} ftr {:?} notes {} hf_lines {}", i + 1, pg.floats.len(), pg.body_top, pg.body_bottom, pg.header, pg.footer, pg.notes.len(), pg.hf_lines.len());
        for fb in &pg.floats {
            println!("   float {:.1},{:.1} {:.1}x{:.1} {:?} para {}", fb.x, fb.y, fb.float.pic.w, fb.float.pic.h, fb.float.wrap, fb.para);
            for l in &fb.lines { println!("      tb p{} l{} {:.1},{:.1}", l.para, l.line, l.x, l.y); }
        }
        for l in &pg.lines {
            let p = &lay.paras[l.para];
            let ln = &p.lines[l.line];
            let t: String = doc.para_text(p.node).chars().skip(ln.pos_start).take((ln.pos_end - ln.pos_start).min(50)).collect();
            println!("  p{} l{} y={:.1} h={:.1} adv={:.1} x0={:.1} {:?}", l.para, l.line, l.y, ln.height, ln.adv, ln.xs.first().copied().unwrap_or(0.0), t);
        }
    }
}
