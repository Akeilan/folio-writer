//! Compare page counts with what the original recorded in the file:
//! docProps/app.xml <Pages> and w:lastRenderedPageBreak.
use folio_core::document::Document;
use folio_core::fonts::FontCache;
use folio_core::paginate::layout_document;

fn main() {
    let mut fonts = FontCache::new();
    let (mut same, mut near, mut total) = (0, 0, 0);
    for path in std::env::args().skip(1) {
        let bytes = match std::fs::read(&path) { Ok(b) => b, Err(_) => continue };
        let doc = match Document::open(&bytes) { Ok(d) => d, Err(e) => { println!("{path}: open failed {:?}", e.0); continue } };
        let app = doc.pkg.raw("docProps/app.xml").map(|b| String::from_utf8_lossy(b).to_string()).unwrap_or_default();
        let pages_app: Option<usize> = app.split("<Pages>").nth(1).and_then(|s| s.split('<').next()).and_then(|s| s.trim().parse().ok());
        let main = doc.pkg.raw(&doc.main).map(|b| String::from_utf8_lossy(b).to_string()).unwrap_or_default();
        let lrpb = main.matches("lastRenderedPageBreak").count();
        let t = std::time::Instant::now();
        let lay = layout_document(&doc, &mut fonts);
        let ms = t.elapsed().as_millis();
        let ours = lay.pages.len();
        let name = std::path::Path::new(&path).file_name().unwrap().to_string_lossy().to_string();
        if let Some(a) = pages_app {
            total += 1;
            if a == ours { same += 1 } else if (a as i64 - ours as i64).abs() <= 1 { near += 1 }
            let mark = if a == ours { "=" } else { "X" };
            println!("{mark} {name:50} ours {ours:4} app {a:4} lrpb+1 {:4}  {ms}ms", lrpb + 1);
        } else {
            println!("? {name:50} ours {ours:4} lrpb+1 {:4}  {ms}ms", lrpb + 1);
        }
    }
    println!("exact {same}/{total}, off by one {near}");
}
