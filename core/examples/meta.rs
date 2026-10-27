//! Render the metafiles in a .docx: meta <docx> <outdir>
use std::io::Read;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let f = std::fs::File::open(&a[1]).unwrap();
    let mut z = zip::ZipArchive::new(f).unwrap();
    for i in 0..z.len() {
        let mut e = z.by_index(i).unwrap();
        let name = e.name().to_string();
        let lower = name.to_lowercase();
        if !(lower.ends_with(".emf") || lower.ends_with(".wmf")) {
            continue;
        }
        let mut b = Vec::new();
        e.read_to_end(&mut b).unwrap();
        let (w, h) = folio_core::metafile::natural_size(&b).unwrap_or((200.0, 150.0));
        let k = (400.0 / w.max(h).max(1.0)).min(4.0);
        let (pw, ph) = ((w * k).max(4.0) as i32, (h * k).max(4.0) as i32);
        let surf = cairo::ImageSurface::create(cairo::Format::ARgb32, pw, ph).unwrap();
        {
            let cr = cairo::Context::new(&surf).unwrap();
            cr.set_source_rgb(1.0, 1.0, 1.0);
            cr.paint().unwrap();
            let t = std::time::Instant::now();
            let ok = folio_core::metafile::draw(&b, &cr, pw as f64, ph as f64);
            eprintln!("{name}: {ok} {}x{} {}ms", pw, ph, t.elapsed().as_millis());
        }
        let doc = std::path::Path::new(&a[1]).file_stem().unwrap().to_string_lossy().to_string();
        let out = format!("{}/{}__{}.png", a[2], doc, name.replace('/', "_"));
        surf.write_to_png(&mut std::fs::File::create(out).unwrap()).unwrap();
    }
}
