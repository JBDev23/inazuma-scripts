# -*- coding: utf-8 -*-
"""
Match export S3 players -> juego3 nicknames using Level 99 stats.

Export gp/tp/kick/... == juego3 Level 99 FP/TP/Kick/...
"""

import argparse
import csv
import io
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_NICKS = DATA_RAW / "nicks_ie3.txt"
OUT_MAP = DATA_RAW / "nicks_ie3_mapping.csv"

# Contiguous HEX blocks for FI / special teams
TEAM_HEX = {
    "big-waves": (0xBCD, 0xBDC),
    "desert-lion": (0xBE1, 0xBF0),
    "fire-dragon": (0xBF5, 0xC04),
    "knights-of-queen": (0xC09, 0xC18),
    "team-k": (0xC1D, 0xC2C),
    "the-empire": (0xC31, 0xC40),
    "unicorn": (0xC45, 0xC54),
    "orpheus": (0xC59, 0xC68),
    "os-reis": (0xC6D, 0xC7C),
    "team-garshield": (0xC81, 0xC90),
    "little-gigant": (0xC95, 0xCA4),
    "rose-griffon": (0xCA9, 0xCB8),
    "red-matador": (0xCBD, 0xCCC),
    "the-great-horn": (0xCE5, 0xCF4),
    "tenkuu-no-shito": (0xD49, 0xD53),  # includes Sanctus (Sein)
    "makai-gundan-z": (0xD5D, 0xD67),
}

ELEM_MAP = {
    "earth": "earth",
    "wood": "wood",
    "fire": "fire",
    "wind": "air",
    "air": "air",
    "wood ": "wood",
}


def fold(s: str) -> str:
    s = (s or "").strip().lower().replace("\u2019", "'").replace("\u2018", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s)


def parse_hex(h):
    m = re.search(r"0x([0-9A-Fa-f]+)", h or "")
    return int(m.group(1), 16) if m else None


def to_int(x):
    return int(float(str(x).strip().replace(",", ".")))


def elem_norm(e):
    return ELEM_MAP.get((e or "").strip().lower(), (e or "").strip().lower())


def get_args():
    parser = argparse.ArgumentParser(description="Match export S3 players to juego3")
    parser.add_argument(
        "export_csv",
        type=Path,
        help="Path to the 'Jugadores Inazuma Eleven - Export' CSV file",
    )
    return parser.parse_args()


args = get_args()

# --- load juego3 ---
raw = (DATA_RAW / "juego3.csv").read_bytes().decode("utf-8", errors="replace")
reader = csv.reader(raw.splitlines()[1:])
next(reader)
juego = []
by_hex = {}
for row in reader:
    if len(row) < 32 or not row[1].strip():
        continue
    try:
        l99 = [to_int(row[i]) for i in (15, 17, 19, 21, 23, 25, 27, 29, 31)]
    except Exception:
        continue
    p = {
        "full": row[0].strip(),
        "nick": row[1].strip(),
        "pos": row[2].strip().upper(),
        "elem": elem_norm(row[5]),
        "l99": l99,
        "hex": parse_hex(row[-1]),
    }
    juego.append(p)
    if p["hex"] is not None:
        by_hex[p["hex"]] = p

# --- load export S3 ---
export_rows = list(
    csv.DictReader(io.StringIO(args.export_csv.read_bytes().decode("utf-8-sig")))
)
s3 = [r for r in export_rows if str(r.get("season", "")).strip() == "3"]


def export_stats(r):
    return [
        to_int(r[k])
        for k in [
            "gp",
            "tp",
            "kick",
            "body",
            "control",
            "guard",
            "speed",
            "stamina",
            "guts",
        ]
    ]


def stat_dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def score_pair(er, jp):
    """Lower is better."""
    es = export_stats(er)
    d = stat_dist(es, jp["l99"])
    pos_pen = 0 if er["position"].strip().upper() == jp["pos"] else 40
    elem_pen = 0 if elem_norm(er["element"]) == jp["elem"] else 25
    # soft name bonus (negative = better)
    name_bonus = 0
    en, ef = fold(er["nickname"]), fold(er.get("name") or "")
    words = [fold(w) for w in jp["full"].split()]
    pn = fold(jp["nick"])
    if en == pn or (ef and ef == fold(jp["full"])):
        name_bonus = -50
    elif en in words or (words and en == words[0]):
        name_bonus = -30
    elif en and pn and (pn.startswith(en) or en.startswith(pn.rstrip("x"))):
        name_bonus = -15
    return d + pos_pen + elem_pen + name_bonus, d, pos_pen, elem_pen


def team_pool(team):
    if team in TEAM_HEX:
        a, b = TEAM_HEX[team]
        return [by_hex[h] for h in range(a, b + 1) if h in by_hex]
    if team == "inazuma-japan":
        # Prefer matching by full name / known IJ; use all juego as fallback pool
        # but we'll primarily match by exact full name then stats among name hits
        return juego
    return juego


def hungarian_greedy(members, pool):
    """Assign each export member to unique pool player minimizing score."""
    pairs = []
    for i, er in enumerate(members):
        for jp in pool:
            sc, d, pp, ep = score_pair(er, jp)
            pairs.append((sc, d, i, er, jp))
    pairs.sort(key=lambda x: (x[0], x[1]))

    assigned = {}
    used = set()
    for sc, d, i, er, jp in pairs:
        if i in assigned or id(jp) in used:
            continue
        assigned[i] = (jp, sc, d)
        used.add(id(jp))
        if len(assigned) == len(members):
            break
    return assigned


def rescue_bad_matches(members, assigned, used_ids, max_dist=10):
    """If in-team match has high stat_dist, search globally for exact/near L99 match."""
    for i, er in enumerate(members):
        if i not in assigned:
            continue
        jp, sc, d = assigned[i]
        if d <= max_dist:
            continue
        es = export_stats(er)
        # exact L99 match unused globally
        cands = []
        for p in juego:
            if id(p) in used_ids and id(p) != id(jp):
                continue
            dd = stat_dist(es, p["l99"])
            if dd <= max_dist:
                cands.append((dd, score_pair(er, p)[0], p))
        if not cands:
            continue
        cands.sort(key=lambda x: (x[0], x[1]))
        best_d, best_sc, best_p = cands[0]
        # free old, take new
        used_ids.discard(id(jp))
        used_ids.add(id(best_p))
        assigned[i] = (best_p, best_sc, best_d)
    return assigned


by_team = defaultdict(list)
for r in s3:
    by_team[r["team-slug"]].append(r)

results = []
# Process team by team for FI; inazuma-japan special
for team, members in by_team.items():
    if team == "inazuma-japan":
        assigned = {}
        used = set()
        # 1) exact full name first
        for i, er in enumerate(members):
            name = (er.get("name") or "").strip()
            hits = [p for p in juego if p["full"] == name]
            if hits:
                # pick best L99 among same full name (duplicate forms)
                best = min(hits, key=lambda p: score_pair(er, p)[0])
                assigned[i] = (best, *score_pair(er, best)[:2])
                used.add(id(best))
        # 2) remaining by stats among unused (prefer low hex = base form)
        remaining = [i for i in range(len(members)) if i not in assigned]
        pool = [p for p in juego if id(p) not in used]
        sub = hungarian_greedy([members[i] for i in remaining], pool)
        for local_i, (jp, sc, d) in sub.items():
            assigned[remaining[local_i]] = (jp, sc, d)
    else:
        pool = team_pool(team)
        assigned = hungarian_greedy(members, pool)
        used_ids = {id(assigned[i][0]) for i in assigned}
        # Rescue orphans / guests (e.g. Hide Nakata in Orpheus list)
        assigned = rescue_bad_matches(members, assigned, used_ids, max_dist=5)
        # Also try to fill still-unassigned via global exact stats
        for i, er in enumerate(members):
            if i in assigned:
                continue
            es = export_stats(er)
            cands = []
            for p in juego:
                if id(p) in used_ids:
                    continue
                dd = stat_dist(es, p["l99"])
                if dd <= 5:
                    cands.append((dd, score_pair(er, p)[0], p))
            if cands:
                cands.sort(key=lambda x: (x[0], x[1]))
                dd, sc, p = cands[0]
                assigned[i] = (p, sc, dd)
                used_ids.add(id(p))

    for i, er in enumerate(members):
        if i not in assigned:
            results.append(
                {
                    "team": team,
                    "export_nick": er["nickname"].strip(),
                    "export_name": (er.get("name") or "").strip(),
                    "juego_nick": "",
                    "juego_full": "",
                    "hex": "",
                    "stat_dist": "",
                    "score": "",
                    "changed": True,
                    "ok": False,
                }
            )
            continue
        jp, sc, d = assigned[i]
        results.append(
            {
                "team": team,
                "export_nick": er["nickname"].strip(),
                "export_name": (er.get("name") or "").strip(),
                "juego_nick": jp["nick"],
                "juego_full": jp["full"],
                "hex": f"0x{jp['hex']:X}" if jp["hex"] is not None else "",
                "stat_dist": d,
                "score": sc,
                "changed": er["nickname"].strip() != jp["nick"],
                "ok": True,
            }
        )

# Reorder to export order
ordered = []
used_idx = set()
for er in s3:
    for j, res in enumerate(results):
        if j in used_idx:
            continue
        if (
            res["team"] == er["team-slug"]
            and res["export_nick"] == er["nickname"].strip()
            and res["export_name"] == (er.get("name") or "").strip()
        ):
            ordered.append(res)
            used_idx.add(j)
            break
results = ordered

# Report
missing = [r for r in results if not r["ok"]]
bad_stats = [r for r in results if r["ok"] and r["stat_dist"] > 5]
dups = defaultdict(list)
for r in results:
    if r["juego_nick"]:
        dups[r["juego_nick"]].append(f"{r['team']}/{r['export_nick']}")

print(
    f"Total {len(results)} | ok {sum(1 for r in results if r['ok'])} | missing {len(missing)}"
)
print(
    f"stat_dist>5: {len(bad_stats)} | changed nicks: {sum(1 for r in results if r['changed'])}"
)
print("DUPS:")
for n, o in sorted(dups.items()):
    if len(o) > 1:
        print(f"  {n}: {o}")
print("MISSING:")
for r in missing:
    print(f"  {r['team']:18} {r['export_nick']!r}")
print("HIGH STAT DIST:")
for r in sorted(bad_stats, key=lambda x: -x["stat_dist"])[:40]:
    print(
        f"  dist={r['stat_dist']:4} score={r['score']:4} {r['team']:18} {r['export_nick']!r:16} -> {r['juego_nick']!r:14} {r['juego_full']}"
    )

print("\n=== FULL MAPPING ===")
for r in results:
    flag = " !!" if not r["ok"] else (" ~" if r["ok"] and r["stat_dist"] > 5 else "")
    ch = " *" if r["changed"] else ""
    print(
        f"{r['juego_nick'] or ('?' + r['export_nick']):14} "
        f"d={str(r['stat_dist']):>3}  "
        f"# {r['team']:18} {r['export_nick']} -> {r['juego_full']}{ch}{flag}"
    )

# Write nicks (skip unmatched)
nicks = [r["juego_nick"] for r in results if r["ok"] and r["juego_nick"]]
with OUT_NICKS.open("w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(nicks) + "\n")

with OUT_MAP.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "team",
            "export_nick",
            "export_name",
            "juego_nick",
            "juego_full",
            "hex",
            "stat_dist",
            "score",
            "changed",
            "ok",
        ],
    )
    w.writeheader()
    w.writerows(results)

print(f"\nWrote {OUT_NICKS} ({len(nicks)} nicks)")
print(f"Wrote {OUT_MAP}")
