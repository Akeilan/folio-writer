exec(open("/home/claude/folio2/tests/common.py").read())
exec(open("/home/claude/folio2/tests/word/wc.py").read())
def a():
    fresh(); yield 0.3
    T("b\t2\na\t3\nc\t1"); yield 0.8
    K("ctrl+a"); yield 0.5
    vcur = docapi.view_cursor(M())
    rng = vcur.getText().createTextCursorByRange(vcur.getStart()); rng.gotoRange(vcur.getEnd(), True)
    desc = rng.createSortDescriptor()
    note("desc", [(p.Name, repr(p.Value)[:120]) for p in desc])
    import traceback, uno
    from folio import sortdlg
    try:
        tm = [p for p in desc if p.Name == "SortFields"][0].Value[0]
        note("tmpl", repr(tm))
        f = sortdlg._fields([(2, 1, True)], False, None, tm)
        note("mine", repr(f[0]))
        out = []
        for p in desc:
            if p.Name == "SortFields": p.Value = uno.Any("[]com.sun.star.table.TableSortField", f)
            out.append(p)
        uno.invoke(rng, "sort", (tuple(out),))
        note("ok1", para_texts())
        note("delim", repr(ord([p for p in desc if p.Name == "Delimiter"][0].Value.value)))
        f1 = sortdlg._fields([(1, 2, True)], False, None, tm)
        out = []
        for p in desc:
            if p.Name == "SortFields": p.Value = uno.Any("[]com.sun.star.table.TableSortField", f1)
            out.append(p)
        uno.invoke(rng, "sort", (tuple(out),))
        note("field1 alpha", para_texts())
        out = []
        for p in desc:
            if p.Name == "SortFields": p.Value = uno.Any("[]com.sun.star.table.TableSortField", f)
            if p.Name == "Delimiter": p.Value = uno.Any("char", uno.Char("\t"))
            out.append(p)
        uno.invoke(rng, "sort", (tuple(out),))
        note("field2 tab", para_texts())
    except Exception as e:
        note("err1", traceback.format_exc()[-400:])
run_scenarios(a)
