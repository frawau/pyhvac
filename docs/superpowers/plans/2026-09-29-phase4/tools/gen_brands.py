"""Generate pyhvac/brands.py from the phase-4 name table (rows.json)."""

import json
import sys
from collections import defaultdict

RENAME = {"mitsubishi_heavy_industries": "mitsubishi_heavy", "trotech": "trotec"}


def main(rows_path, out_path, package="protocols", drop=()):
    rows = json.load(open(rows_path))
    imports = defaultdict(set)
    table, seen, aliases = [], {}, []
    for r in rows:
        if (r["old_brand"], r["old_model"]) in drop:
            continue
        module, cls = r["cls"].split(".")
        module = RENAME.get(module, module) if package == "protocols" else module
        imports[module].add(cls)
        key = (r["brand"], r["model"])
        entry = (r["brand"], r["model"], r["kind"], cls, r["var"])
        if key in seen:
            assert seen[key] == entry, f"merge with different device: {key}"
        else:
            seen[key] = entry
            table.append(entry)
        if r["alias"]:
            aliases.append(((r["old_brand"], r["old_model"]), key))
    lines = [
        '"""The brand/model table: which brand sells which model on which',
        "protocol. Generated once from the phase-4 name table; edit by hand",
        'from now on. Rows: (brand, model, kind, Device class, variant)."""',
        "",
    ]
    for module in sorted(imports):
        names = ", ".join(sorted(imports[module]))
        lines.append(f"from .{package}.{module} import {names}")
    lines += ["", "MODELS = ("]
    for brand, model, kind, cls, var in sorted(table, key=lambda e: (e[0].casefold(), e[1].casefold())):
        lines.append(f"    ({brand!r}, {model!r}, {kind!r}, {cls}, {var!r}),")
    lines += [")", "", "# 0.1.x strings of the devices that were pure Python in 0.1.x.", "ALIASES = {"]
    for old, new in aliases:
        lines.append(f"    {old!r}: {new!r},")
    lines += ["}", ""]
    open(out_path, "w").write("\n".join(lines))
    print(f"{len(table)} rows, {len(aliases)} aliases, {len({e[0] for e in table})} brands")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "protocols",
         drop={("sharp", "generic")})
