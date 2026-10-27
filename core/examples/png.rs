//! Render pages to PNG: png <docx> <outdir> [scale] [first] [last]
use folio_core::document::Document;
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;
use folio_core::render::{render_page_image, Overlay, Renderer};

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let scale: f64 = a.get(3).and_then(|s| s.parse().ok()).unwrap_or(1.5);
    let mut fonts = FontCache::new();
    let doc = Document::open(&std::fs::read(&a[1]).unwrap()).unwrap();
    let lay = layout_document(&doc, &mut fonts);
    let first: usize = a.get(4).and_then(|s| s.parse().ok()).unwrap_or(1);
    let last: usize = a.get(5).and_then(|s| s.parse().ok()).unwrap_or(lay.pages.len());
    let mut r = Renderer::new();
    let ov = Overlay { gridlines: true, ..Default::default() };
    for i in first..=last.min(lay.pages.len()) {
        let t = std::time::Instant::now();
        let s = render_page_image(&mut r, &lay, i - 1, &mut fonts, scale, &ov).unwrap();
        let mut f = std::fs::File::create(format!("{}/p{:03}.png", a[2], i)).unwrap();
        s.write_to_png(&mut f).unwrap();
        eprintln!("page {i} {}ms", t.elapsed().as_millis());
    }
}
