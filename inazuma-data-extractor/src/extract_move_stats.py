"""
Extrae la lista de técnicas (hissatsu) del FAQ HTML de Inazuma Eleven 3
y las exporta a JSON.

Uso:
    python extract.py
    python extract.py data/source.html -o moves.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# Bonus de poder al nivel máximo (Base Power Increasement → etapa final).
# Grade → G5; Shin/Version → Shin/V3.
MAX_POWER_BONUS: dict[tuple[str, str], int] = {
    ("Grade", "Slow"): 18,
    ("Grade", "Medium"): 16,
    ("Grade", "Fast"): 14,
    ("Shin", "Slow"): 12,
    ("Shin", "Medium"): 10,
    ("Shin", "Fast"): 8,
    ("Version", "Slow"): 12,
    ("Version", "Medium"): 10,
    ("Version", "Fast"): 8,
}

EVOLUTION_KIND = {"G": "Grade", "Shin": "Shin", "Ver": "Version"}
EVOLUTION_SPEED = {"Slow": "Slow", "Med": "Medium", "Fast": "Fast"}
ELEMENT_MAP = {
    "WIND TYPE": "Wind",
    "FOREST TYPE": "Wood",
    "FIRE TYPE": "Fire",
    "EARTH TYPE": "Earth",
    "MOUNTAIN TYPE": "Earth",
}
SKILL_TYPE_MAP = {
    "SHOOT SKILL": "Shoot",
    "DRIBBLE SKILL": "Dribble",
    "BLOCK SKILL": "Block",
    "KEEPER SKILL": "Keeper",
}

ROW_RE = re.compile(
    r"^/"
    r"(.+?)"
    r"\s{2,}"
    r"(\d+)"
    r"\s+"
    r"(\d+)"
    r"\s+"
    r"(\S+)"
    r"\s+"
    r"(G|Shin|Ver),(Slow|Med|Fast)"
    r"\s*/\s*$"
)
ELEMENT_HEADER_RE = re.compile(
    r"^/\s*(WIND TYPE|FOREST TYPE|FIRE TYPE|EARTH TYPE|MOUNTAIN TYPE)\s*/\s*$"
)
SKILL_HEADER_RE = re.compile(
    r"^-(SHOOT SKILL|DRIBBLE SKILL|BLOCK SKILL|KEEPER SKILL)\s*$"
)
FOUL_RE = re.compile(r"^(\d+)(?:\(([^)]+)\))?$")


def format_evolution(kind_raw: str, speed_raw: str) -> str:
    kind = EVOLUTION_KIND[kind_raw]
    speed = EVOLUTION_SPEED[speed_raw]
    return f"{kind} ({speed})"


def power_at_max(base_power: int, kind_raw: str, speed_raw: str) -> int:
    kind = EVOLUTION_KIND[kind_raw]
    speed = EVOLUTION_SPEED[speed_raw]
    return base_power + MAX_POWER_BONUS[(kind, speed)]


def parse_middle_column(skill_type: str, raw: str) -> tuple[str, str]:
    """Devuelve (fouls_rate, secondary_type) según el tipo de skill."""
    if skill_type == "Shoot":
        secondary = "" if raw == "None" else raw
        return "", secondary

    if skill_type in {"Dribble", "Block"}:
        match = FOUL_RE.match(raw)
        if not match:
            return "", raw
        rate, secondary = match.group(1), match.group(2) or ""
        return f"{rate}%", secondary

    if skill_type == "Keeper":
        return "", raw

    return "", ""


def extract_faq_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    parts = [pre.get_text() for pre in soup.select("pre")]
    if parts:
        return "\n".join(parts)
    return soup.get_text()


def parse_moves(text: str) -> list[dict]:
    skill_type: str | None = None
    element: str | None = None
    moves: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        skill_match = SKILL_HEADER_RE.match(line)
        if skill_match:
            skill_type = SKILL_TYPE_MAP[skill_match.group(1)]
            element = None
            continue

        # Tras Spirit Skill (u otras secciones) dejamos de parsear moves.
        if line.startswith("-") and "SKILL" in line and skill_match is None:
            if not any(k in line for k in SKILL_TYPE_MAP):
                skill_type = None
                element = None
            continue

        element_match = ELEMENT_HEADER_RE.match(line)
        if element_match:
            element = ELEMENT_MAP[element_match.group(1)]
            continue

        if skill_type is None or element is None:
            continue

        row = ROW_RE.match(line)
        if not row:
            continue

        name = row.group(1).strip()
        base_power = int(row.group(2))
        tp_cost = int(row.group(3))
        middle = row.group(4)
        evo_kind = row.group(5)
        evo_speed = row.group(6)

        key = (name, skill_type, element)
        if key in seen:
            continue
        seen.add(key)

        fouls_rate, secondary_type = parse_middle_column(skill_type, middle)
        evolution_type = format_evolution(evo_kind, evo_speed)

        moves.append(
            {
                "Move Name": name,
                "Type": skill_type,
                "Element": element,
                "Fouls Rate": fouls_rate,
                "Base Power": base_power,
                "Power at Max Lv.": power_at_max(base_power, evo_kind, evo_speed),
                "TP Cost": tp_cost,
                "Secondary Type": secondary_type,
                "Evolution Type": evolution_type,
                "HEX ID": "",
            }
        )

    return moves


def main() -> int:
    default_html = (
        Path(__file__).resolve().parent.parent / "data" / "raw" / "source.html"
    )

    parser = argparse.ArgumentParser(
        description="Extrae técnicas de Inazuma Eleven 3 (FAQ HTML) a JSON."
    )
    parser.add_argument(
        "html_file",
        type=Path,
        nargs="?",
        default=default_html,
        help=f"Ruta al HTML (default: {default_html.name})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "data"
        / "processed"
        / "moves.json",
        help="Archivo JSON de salida (default: moves.json)",
    )
    args = parser.parse_args()

    if not args.html_file.is_file():
        print(f"Error: no existe el archivo '{args.html_file}'", file=sys.stderr)
        return 1

    html = args.html_file.read_text(encoding="utf-8", errors="replace")
    moves = parse_moves(extract_faq_text(html))

    args.output.write_text(
        json.dumps(moves, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Extraidas {len(moves)} tecnicas -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
