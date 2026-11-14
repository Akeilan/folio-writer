use folio_core::fonts::{is_emoji, FontCache};

fn main() {
    let mut fc = FontCache::new();
    for ch in ['\u{1F600}', '\u{1F44D}', '\u{1F3FD}', '\u{2713}'] {
        let picked = fc.emoji(ch).map(|f| (f.family.clone(), f.id));
        let fb = fc.fallback(ch, false, false).map(|f| f.family.clone());
        print!("U+{:04X} emoji={} picked={:?} fallback={:?}", ch as u32, is_emoji(ch), picked, fb);
        if let Some(f) = fc.emoji(ch) {
            let face = rustybuzz::ttf_parser::Face::parse(f.data(), f.index).unwrap();
            let gid = face.glyph_index(ch).map(|g| g.0).unwrap_or(0);
            let r = f.raster(gid, 160).map(|i| (i.width, i.height, i.ppem, i.x, i.y, i.png.len()));
            print!(" gid={} raster={:?}", gid, r);
        }
        println!();
    }
}
