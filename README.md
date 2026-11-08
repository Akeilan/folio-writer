# Folio Page

A word processor with a ribbon, for Zorin OS and Ubuntu. Part of Folio Studio. It was called
Folio Writer until 2.31; the old name still installs this one.

`.docx` is its own format: Page reads and writes it directly, with its own engine, and does not
go through another office suite. It also reads and writes `.doc` (Word 97-2003), `.rtf`, `.odt`,
`.txt` and `.html`, and saves PDF.

## What it does

- **The Word ribbon**, with KeyTips (press Alt), ScreenTips, a File view, and the usual keyboard
  shortcuts. Light and dark themes of its own, whatever the desktop is set to.
- **Writing**: styles, lists, tables (nested too), columns, sections, headers and footers,
  footnotes and endnotes, bookmarks, cross-references, captions, an index and a table of
  contents, hyphenation, line numbers, a watermark, drop caps.
- **Pictures and drawings**: pictures with wrapping, crop and background removal, shapes,
  text boxes, WordArt, SmartArt, charts, icons, screenshots and screen clippings, ink.
- **3D models**: a glTF model (`.glb`, `.gltf`) read and drawn here, turned from the views
  gallery or to exact angles. It travels in the `.docx` as Word keeps one — the model itself as
  its own part, with a picture of the view it is turned to — so Word opens it as a model again
  and every other reader sees the picture.
- **Equations**: typed in linear format (`a^2+b^2=c^2`) and shown professionally, as Word does.
- **Reviewing**: track changes, comments, compare two documents, spelling and grammar as you
  type, a thesaurus, read aloud, Immersive Reader, protection and restricted editing.
- **Version history**: every save keeps how the document stood before it, on this computer.
  File ▸ Info lists them with their dates; open one read-only, compare it with what is there
  now, or restore it. Options ▸ Save says how many to keep, or turns it off.
- **Mail merge**: letters, labels and envelopes from a spreadsheet or a table.
- **Developer**: content controls, macros in Python, document properties.
- **With the rest of Folio Studio**: copy and paste with Sheet, Show and Draw; a Cork diagram
  pasted here stays editable, and double-clicking it opens Cork.

## Layout

| Folder | What's in it |
| --- | --- |
| `app/folio` | the interface, in Python with GTK 3 |
| `core` | the document engine, in Rust (about 23,000 lines): the model, layout, and every file format |
| `share` | templates, icons, fonts, autocorrect lists, the manual page |
| `tests` | the test suites (see below) |
| `tools` | build, release and maintenance scripts |

## Building and testing

```sh
cd core && cargo build --release        # the engine
./build-deb.sh out/                     # the package
tools/run_native_tests.sh               # the engine and interface tests (n1 to n46)
tools/run_word_tests.sh                 # Word parity: files written here, read back
tools/run_theme_audit.sh                # desktop themes don't show through
XD=97 tools/release.sh                  # everything, on the three test machines
```

Needs python3-gi, GTK 3, Cairo, Poppler, python3-enchant and the Carlito, Caladea and Liberation
fonts; see `Depends` in `build-deb.sh` for the full list.
