#!/usr/bin/env python
"""Protipříklad k W‑78: poznámka neplaší, skutečná změna se pozná.

    python nalezy/revize_poplach.py

Pole `core_na_konci` existuje jen proto, aby odpovědělo na jednu otázku:
**změnilo se jádro během běhu?** Dokud v porovnávané hodnotě ležel počet
nesledovaných souborů, odpovídalo ANO kvůli jednomu `__pycache__` — šum
se tím nezrušil, jen přesunul o pole vedle.

Kontroluje se obojí a na **vymyšlených řetězcích**, ne na běhu: kdyby to
viselo na tom, co zrovna dělá Builder jádra, byl by to test počasí.
Skutečný běh to pak potvrdí, ale ověřit se to musí bez něj.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cb_utils.revize import identity, note, tracked  # noqa: E402

REVIZE = "1009036 2026-08-16 09:25 Rozklad přívlastku ve jmenné frázi"

PRIPADY: tuple[tuple[str, str, str, bool], ...] = (
    (
        "přibyl nesledovaný soubor",
        f"{REVIZE} (+6 nesledovaných souborů)",
        f"{REVIZE} (+7 nesledovaných souborů)",
        True,  # má vyjít SHODA
    ),
    (
        "uklizeno vedle běhu",
        f"{REVIZE} (+2 nesledovaných souborů)",
        REVIZE,
        True,
    ),
    (
        "sledovaný strom se změnil",
        f"{REVIZE} +dirty:bb2a6d72",
        f"{REVIZE} +dirty:21360955",
        False,  # má vyjít ROZDÍL
    ),
    (
        "commit se změnil",
        REVIZE,
        "27c6a62 2026-08-16 09:52 W-78: přívlastek ve jmenné frázi",
        False,
    ),
    (
        "z čistého na rozdělaný",
        REVIZE,
        f"{REVIZE} +dirty:bb2a6d72",
        False,
    ),
)


def main() -> None:
    print("POROVNÁVANÁ HODNOTA vs POZNÁMKA PRO ČLOVĚKA\n")
    spatne = 0
    for jmeno, prvni, druhy, ma_byt_shoda in PRIPADY:
        shoda = tracked(prvni) == tracked(druhy)
        ok = shoda is ma_byt_shoda
        spatne += not ok
        print(f"  {'✓' if ok else '✗'} {jmeno:28}"
              f" {'shoda' if shoda else 'ROZDÍL':7}"
              f" (čekáno {'shoda' if ma_byt_shoda else 'ROZDÍL'})")
        if not ok:
            print(f"      {prvni!r}\n      {druhy!r}")

    print("\nPOZNÁMKA SE NEZTRÁCÍ, JEN NELEŽÍ V POROVNÁVANÉ HODNOTĚ\n")
    vzorek = f"{REVIZE} (+6 nesledovaných souborů)"
    print(f"  hodnota:  {tracked(vzorek)}")
    print(f"  poznámka: {note(vzorek)}")
    if not note(vzorek):
        spatne += 1
        print("  ✗ poznámka zmizela — to je ztráta informace, ne oprava")

    hodnota, poznamka = identity(Path(__file__).resolve().parent.parent)
    print(f"\n  tenhle repozitář: {hodnota}")
    print(f"                    {poznamka or '(čistý)'}")

    print(f"\n  PORUŠENÍ: {spatne}"
          f"   {'— protipříklad drží' if not spatne else '— NEDRŽÍ'}")
    sys.exit(1 if spatne else 0)


if __name__ == "__main__":
    main()
