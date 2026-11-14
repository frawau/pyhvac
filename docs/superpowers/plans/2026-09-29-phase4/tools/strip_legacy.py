"""Phase 4 move: pyhvac/plugins/<m>.py -> pyhvac/protocols/<new>.py with the
old API removed. Prints what it removed; refuses if a kept name still refers
to a removed one."""

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
LEGACY_ROOTS = {"HVAC", "PulseBased", "IRGHVAC", "GenPluginObject", "Manchester"}
RENAME = {
    "mitsubishi_heavy_industries": "mitsubishi_heavy",
    "trotech": "trotec",
}


def plan():
    src_dir = ROOT / "pyhvac" / "plugins"
    modules = {}
    for p in sorted(src_dir.glob("*.py")):
        if p.name in ("__init__.py", "hvaclib.py"):
            continue
        modules[p.stem] = p
    return modules


def strip(path):
    src = path.read_text()
    tree = ast.parse(src)
    legacy = set(LEGACY_ROOTS)
    # transitive: a class whose base is legacy is legacy
    changed = True
    while changed:
        changed = False
        for n in tree.body:
            if isinstance(n, ast.ClassDef) and n.name not in legacy:
                bases = {getattr(b, "id", getattr(b, "attr", None)) for b in n.bases}
                if bases & legacy or n.name == "PluginObject":
                    legacy.add(n.name)
                    changed = True
    drop = []  # (start, end) line ranges, 1-based inclusive
    removed = []
    for i, n in enumerate(tree.body):
        start = n.lineno
        if getattr(n, "decorator_list", None):
            start = min(d.lineno for d in n.decorator_list)
        end = n.end_lineno
        kind = None
        if isinstance(n, ast.ClassDef) and n.name in legacy:
            kind = f"class {n.name}"
        elif isinstance(n, ast.ImportFrom) and n.module in ("hvaclib", "irhvac"):
            kind = f"import from .{n.module}"
        elif isinstance(n, ast.Try) and "irhvac" in ast.get_source_segment(src, n):
            kind = "guarded irhvac import"
        elif isinstance(n, ast.ImportFrom) and n.level == 1 and n.module:
            names = [a.name for a in n.names]
            keep = [a for a in n.names if a.name not in legacy]
            if not keep:
                kind = f"import of legacy {names}"
        elif isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DEVICES" for t in n.targets
        ):
            kind = "DEVICES ="
        elif (
            isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Attribute)
            and getattr(n.value.func.value, "id", None) == "DEVICES"
        ):
            kind = "DEVICES.update"
        elif (
            isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and getattr(n.test.left, "id", None) == "__name__"
        ):
            kind = "__main__ block"
        elif isinstance(n, ast.FunctionDef) and n.name == "main":
            kind = "legacy main()"
        if kind:
            drop.append((start, end))
            removed.append(kind)
    lines = src.splitlines(keepends=True)
    keep = [
        line
        for no, line in enumerate(lines, 1)
        if not any(a <= no <= b for a, b in drop)
    ]
    out = "".join(keep)
    # the kept code must not refer to a removed class
    kept = ast.parse(out)
    names = {n.id for n in ast.walk(kept) if isinstance(n, ast.Name)}
    names |= {
        getattr(b, "id", None)
        for n in ast.walk(kept)
        if isinstance(n, ast.ClassDef)
        for b in n.bases
    }
    attrs = {
        f"{n.value.id}.{n.attr}"
        for n in ast.walk(kept)
        if isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name)
        and n.value.id in legacy
    }
    dangling = sorted(((names & legacy) - LEGACY_ROOTS) | (names & {"irhvac"}) | attrs)
    return out, removed, dangling


def main():
    dst = ROOT / "pyhvac" / "protocols"
    dst.mkdir(exist_ok=True)
    (dst / "__init__.py").write_text('"""Protocol code: layouts and Device classes."""\n')
    problems = []
    for stem, path in plan().items():
        out, removed, dangling = strip(path)
        tree = ast.parse(out)
        has_code = any(
            isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.Assign)) for n in tree.body
        )
        if dangling:
            problems.append(f"{stem}: still refers to {dangling}")
        if not has_code:
            print(f"{stem}: registration-only, dropped")
            continue
        new = RENAME.get(stem, stem)
        (dst / f"{new}.py").write_text(out)
        print(f"{stem} -> protocols/{new}.py; removed: {', '.join(removed)}")
    if problems:
        print("PROBLEMS:\n" + "\n".join(problems))
        sys.exit(1)


if __name__ == "__main__":
    main()
