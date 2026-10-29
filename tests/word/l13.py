import os as _o; TESTS = _o.environ.get("FOLIO_WRITER_TESTS") or (lambda f: f(f, _o.path.dirname(_o.path.abspath(_o.environ.get("FOLIO_TEST_SCRIPT", "./x")))))(lambda f, d: d if _o.path.exists(_o.path.join(d, "common.py")) or d in ("/", "") else f(f, _o.path.dirname(d))); exec(open(TESTS + "/common.py").read())
exec(open(TESTS + "/word/wc.py").read())
def fmt():
    fresh(); yield 0.3
    set_text("Source words\nTarget words"); yield 0.4
    para_rng(0).select()
    E.ed.toggle("w:b"); E.ed.set_color("C00000"); E.ed.set_size(16.0)
    E.ed.set_align("center"); E.ed.apply_para([("w:ind", [("w:left", "720")])])
    E.view.after_edit()
    K("ctrl+Home"); K("Right"); yield 0.4
    K("ctrl+shift+c"); yield 0.5
    K("ctrl+End"); yield 0.4
    K("ctrl+shift+v"); yield 0.8
    p1 = top_paras()[1]
    n = len(ptext(p1))
    r = Rng((p1, n - 3), (p1, n)).run()
    check("char formatting pasted", r["bold"] and r["color"] == 0xC00000 and r["size"] == 16.0, (r["bold"], r["color"], r["size"]))
    q = pv(1)
    check("paragraph formatting pasted", q["align"] == "center" and q["ind_left"] == 720, (q["align"], q["ind_left"]))
def hf():
    fresh(); yield 0.3
    T("x"); yield 0.3
    win.run("header"); yield 1.2
    win.select_tab("Header & Footer"); yield 0.5
    sb = win.hf_spins["header_top"]
    sb.set_value(2000); yield 0.8
    hd = page_setup(E.ed.current_section())["header"]
    check("header from top (20 mm = 1134 twips)", abs(hd - 1134) < 12, hd)
    labs = [_clean(getattr(c, "label", "") or "") or (getattr(c, "tooltip_text", "") or "") for c in win.ribbon.controls if getattr(c, "tab_name", "") == "Header & Footer"]
    check("Insert Alignment Tab button", "Insert Alignment Tab" in labs, labs)
    from folio import hfedit
    GLib.idle_add(lambda: (hfedit.alignment_tab_dialog(win), False)[1]); yield 1.0
    check("Alignment Tab dialog", bool(dlg("Alignment Tab")))
    respond("Alignment Tab"); yield 0.8
    h = caret_para_text()
    hx = parts_xml("word/header")
    check("tab inserted in header", "\t" in h or "w:ptab" in hx, repr(h))
    shot("l13_hf")
run_scenarios(fmt, hf)
