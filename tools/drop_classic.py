#!/usr/bin/env python3
"""W2-11 (one-off developer tool): Folio Writer always runs on its own engine since 2.30, so
every test of "is the new engine in use" is True. This rewrites the app's source with that
known, keeping the new-engine branch of each test and dropping the LibreOffice one.

    python3 tools/drop_classic.py app/folio/*.py ...     (rewrites the files in place)
"""
import sys

import libcst as cst
import libcst.matchers as m

ENGINE_OWNERS = {"win", "eng", "E", "w"}


def dotted(node):
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        d = dotted(node.value)
        return d + "." + node.attr.value if d else None
    return None


class Native(cst.CSTTransformer):
    def __init__(self, fname):
        self.fname = fname
        self.local_flags = [set()]
        self.changed = 0
        self.final = False

    # ------------------------------------------------------------ what is True
    def is_native(self, e):
        if isinstance(e, cst.Call) and dotted(e.func) == "getattr" and len(e.args) >= 2:
            a = e.args[1].value
            if isinstance(a, cst.SimpleString) and a.evaluated_value == "native":
                return True
        if isinstance(e, cst.Attribute) and e.attr.value == "native":
            owner = dotted(e.value) or ""
            last = owner.split(".")[-1]
            if owner in ("self.engine", "self.eng", "self.win.engine", "win.engine", "self.win",
                         "m.eng", "eng", "win", "E", "window", "self.window", "self.window.engine"):
                return True
            if owner == "self" and self.fname.endswith(("window.py", "panes.py")):
                return True
            if last in ("engine", "eng"):
                return True
        if isinstance(e, cst.Call) and dotted(e.func) == "self.native" and not e.args and self.fname.endswith("acwatch.py"):
            return True
        if isinstance(e, cst.Name) and e.value in self.local_flags[-1]:
            return True
        return False

    def has_native(self, e):
        if self.is_native(e):
            return True
        if isinstance(e, cst.UnaryOperation):
            return self.has_native(e.expression)
        if isinstance(e, cst.BooleanOperation):
            return self.has_native(e.left) or self.has_native(e.right)
        return False

    def truth(self, e):
        """True / False when the expression's value is known, else None."""
        if self.is_native(e):
            return True
        if isinstance(e, cst.Name) and e.value in ("True", "False"):
            return e.value == "True"
        if isinstance(e, cst.UnaryOperation) and isinstance(e.operator, cst.Not):
            t = self.truth(e.expression)
            return None if t is None else not t
        if isinstance(e, cst.BooleanOperation):
            l, r = self.truth(e.left), self.truth(e.right)
            if isinstance(e.operator, cst.And):
                if l is False or r is False:
                    return False if (l is False) else (False if r is False and l is not None else None)
                if l is True and r is True:
                    return True
            else:
                if l is True or (r is True and l is not None):
                    return True
                if l is False and r is False:
                    return False
        return None

    # ------------------------------------------------------------ scopes
    def visit_FunctionDef(self, node):
        self.local_flags.append(set())

    def leave_FunctionDef(self, orig, node):
        self.local_flags.pop()
        return node

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0].target, cst.Name) and self.is_native(node.value):
            if node.targets[0].target.value == "native":
                self.local_flags[-1].add("native")

    # ------------------------------------------------------------ simplify
    def leave_BooleanOperation(self, orig, node):
        l = self.truth(node.left) if self.has_native(node.left) else None
        r = self.truth(node.right) if self.has_native(node.right) else None
        if isinstance(node.operator, cst.And):
            if l is True:
                self.changed += 1
                return node.right
            if r is True and not _has_call(node.left) is None:
                self.changed += 1
                return node.left
        else:
            if l is False:
                self.changed += 1
                return node.right
            if r is False:
                self.changed += 1
                return node.left
        return node

    def leave_UnaryOperation(self, orig, node):
        if self.final and isinstance(node.operator, cst.Not) and self.has_native(node.expression):
            t = self.truth(node.expression)
            if t is not None:
                self.changed += 1
                return cst.Name("False" if t else "True")
        return node

    def leave_IfExp(self, orig, node):
        t = self.truth(node.test) if self.has_native(node.test) else None
        if t is True:
            self.changed += 1
            return node.body
        if t is False:
            self.changed += 1
            return node.orelse
        return node

    def leave_Call(self, orig, node):
        return node

    def leave_IndentedBlock(self, orig, node):
        """Statements after a return / raise in the same block never run."""
        body = list(node.body)
        for i, st in enumerate(body):
            if isinstance(st, cst.SimpleStatementLine) and any(isinstance(x, (cst.Return, cst.Raise)) for x in st.body):
                if i + 1 < len(body):
                    self.changed += 1
                    return node.with_changes(body=body[:i + 1])
                break
        return node

    def visit_If(self, node):
        if isinstance(node.orelse, cst.If):
            self.__dict__.setdefault("elifs", set()).add(id(node.orelse))

    def fix_orelse(self, node):
        """An elif whose test is known: it becomes the else, or goes."""
        o = node.orelse
        while isinstance(o, cst.If):
            t = self.truth(o.test) if self.has_native(o.test) else None
            if t is True:
                self.changed += 1
                return node.with_changes(orelse=cst.Else(body=o.body))
            if t is False:
                self.changed += 1
                node = node.with_changes(orelse=o.orelse)
                o = node.orelse
                continue
            sub = self.fix_orelse(o)
            if sub is not o:
                return node.with_changes(orelse=sub)
            break
        return node

    def leave_If(self, orig, node):
        node = self.fix_orelse(node)
        if id(orig) in getattr(self, "elifs", set()):
            return node
        t = self.truth(node.test) if self.has_native(node.test) else None
        if t is None:
            return node
        self.changed += 1
        if t:
            return cst.FlattenSentinel(node.body.body)
        if node.orelse is None:
            return cst.RemoveFromParent()
        if isinstance(node.orelse, cst.If):
            return node.orelse
        return cst.FlattenSentinel(node.orelse.body.body)


def _has_call(e):
    return None


def main():
    for f in sys.argv[1:]:
        src = open(f).read()
        mod = cst.parse_module(src)
        tr = Native(f)
        for _ in range(4):
            new = mod.visit(tr)
            if new.code == mod.code:
                break
            mod = new
        tr.final = True
        mod = mod.visit(tr)
        if mod.code != src:
            open(f, "w").write(mod.code)
            print("%-28s %d simplifications" % (f, tr.changed))


if __name__ == "__main__":
    main()
