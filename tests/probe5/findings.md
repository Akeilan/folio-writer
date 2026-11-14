# Page findings (running notes)
1. Undo leaves parts behind in the file: after undoing a header/footer/watermark/comment/footnote/bullets, the saved .docx still holds the part (header21.xml etc.); undoing Margins>Mirrored leaves mirrorMargins set. [p1b]
2. Save as .odt/.rtf/.doc silently drops: shapes, tracked insertions (become plain text), content controls (odt not warned), highlight (odt). Compatibility checker warns of none of these. [p3]
3. .doc round trip: 3x3 table comes back with 12 cells, extra blank paragraphs. [p3]
4. HTML reader ignores <b>, <i>, <sub>, <s>, highlight, footnotes, header/footer when opening .html it wrote itself. [p3]
5. Command walk never visits Table Design, Table Layout, Header & Footer, Equation, Chart Design, SmartArt Design tabs (excluded, no setup). Coverage gap.
6. engine toggle("bold") (unknown name) writes an invalid <bold/> element into the docx — macros can corrupt files. [p3 first run]
7. Convert Text to Table: OK in the dialog raises AttributeError setString (dlg_table.py:102 uses the old UNO model). Feature dead. [p2]
8. RTL scripts: Arabic drawn unshaped and left-to-right; Hebrew drawn in reverse order. No bidi. [p8 screenshot]
9. Emoji: monochrome; skin-tone modifier drawn as a separate box. [p8]
10. Reading .doc: headers/footers of later sections and pages lost (sections.doc). Reading .odt: every page gets the first-page header, others lost; column break lost (breaks.odt 3 pages vs 4); chart object dropped (61745.odt). Reading .rtf: A5 section size lost, landscape header lost, 5 pages vs 6. [p7,p9]
11. OK: corpus of 13 docx + LO-written docx/doc/odt/rtf (65 files) all open, no errors; page counts match LibreOffice on all docx (92-page doc included); words all present.
12. OK: equations tab works at user level (my p4 setup was wrong).
13. Baseline suites on rebuilt machine: native 46/48 scripts clean, word 55/57; the 4 failures are the machine (xclip missing then, DejaVu UI font making ribbon 101px). Need re-run.
14. AutoRecover writes .odt (app.py write_autorecover): after a crash the recovered document has lost shapes, tracked changes, content controls, highlight (same losses as Save As .odt). Confirmed end to end. [p12]
15. Text files not UTF-8 open as garbage: Latin-1 shows replacement chars, UTF-16 shows NULs. No encoding detection or prompt. [p13]
16. A 2.4 MB .txt (40,000 lines) takes 52 s to open; a 490-page .docx takes 0.8 s. [p14]
17. AutoRecover's .odt write blocks the window 1.8 s on a 490-page novel (docx save is 0.03 s). [p14]
18. Memory: 766 MB with a 490-page (250k words) document open. [p14] (check baseline)
19. Ribbon height depends on installed UI font: 96 px designed, 101 with DejaVu, 107 with Noto Sans; n33 fails on a machine with Noto Sans (which Ubuntu/Zorin ship). [baseline]
OK: engine fuzz 33,000 random edits over 90 runs: no panic, every save reopens identically, undo-all returns the exact original XML.
OK: 600 damaged files: 432 opened, 168 refused cleanly, no panic, no hang.
OK: perf on 490 pages: 40 ms per key at start and end, find-all 60 ms, PDF 0.3 s.
OK: save names (unicode, 200 chars, no extension), missing/zero/garbage files refused with a message.
20. Printing marks the document modified (lastPrinted). [p17]
21. Mailings/Share still tell the user to install Folio Post "which comes with the Folio Suite". [code]
DOC: Backlog 5 = https://claude.ai/artifact/BhArf1Nqj8aQYzzjtLoZ1U node 1ca94a34-26ff session mrjrxvrdgcb; s1 pending .28, Page table .134, s3 .30, s4 .31; rev 2. W5-01..W5-16 written.
22. Office Theme (File > Options): Black and Dark Gray leave tab names dark-on-dark (only the active tab readable) and ribbon/status labels ghosted (shadowed, hard to read); Styles gallery, ruler stay white. White theme: title-bar icons (save, undo, redo, search glass) and window buttons vanish white-on-white. Only Colorful is right. Page does not follow a dark desktop. [p19 screenshots]
23. Window minimum width is 859 px: cannot be half-tiled on a 1366 px screen. [p19]
24. Typing prose: "..." straight after a word is not turned into an ellipsis (it is when it stands alone) and the next word is capitalised: 'so... what then' -> 'So... What then'; '"Well..." she said' -> '“Well...” She said'. [p20b]
25. 'teh ' at a paragraph start becomes 'The '; one Undo gives 'the ', a second 'teh ' (Word: one). Minor. [p20b]
26. Save Selection to ... Gallery (Quick Parts, Cover Page, Header, Footer, Text Box, Equation, Bibliography): always answers "Select the text you want to save first." with text selected. 7 commands dead. [p24]
27. Record Macro, Stop Recording, Pause Recording (View > Macros and the status bar button) and Ctrl+Alt+K (AutoFormat) answer "This isn't available with the new engine yet." Not routed in native/actions.py WINDOW list though window.act_record_macro / act_autoformat_now exist. [p23]
28. Walk SKIP list is by substring: "open" hides Bullets > Open bullet and Paragraph Spacing > Open, "record" hides the four Mailings record buttons, "print" hides View > Print Layout, "close" hides Close Outline View. [p22]
OK: all 171 other action names route. Print path (lp) correct with mixed page sizes. Skipped commands otherwise fine.
29. Memory: 115 MB empty, 450-510 MB with a 490-page document, and it is not given back when that document is closed (508 MB with a one-line document open). Reopening does not keep growing (549 after three more). [p28]
