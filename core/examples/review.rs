use folio_core::document::Document;
use folio_core::editor::Editor;
use folio_core::fonts::FontCache;

fn main() {
    let mut n = 0;
    for path in std::env::args().skip(1) {
        let Ok(doc) = Document::open_path(&path) else { continue };
        let fonts = FontCache::new();
        let mut e = Editor::new(doc, fonts);
        let ch = e.all_changes().len();
        let cm = e.comments();
        let ranged = cm.iter().filter(|c| c.range.is_some()).count();
        if ch == 0 && cm.is_empty() {
            continue;
        }
        n += 1;
        let pages = e.layout.pages.len();
        let a = e.accept_reject_all(true, None);
        let left = e.all_changes().len();
        e.undo();
        let r = e.accept_reject_all(false, None);
        let left2 = e.all_changes().len();
        let ok = e.doc.write().is_ok();
        println!("{} changes={ch} comments={} ranged={ranged} pages={pages} acc={a} left={left} rej={r} left={left2} write={ok}",
                 path.rsplit('/').next().unwrap(), cm.len());
    }
    eprintln!("{n} docs");
}
