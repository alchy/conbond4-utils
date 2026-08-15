#!/usr/bin/env python
"""Rozbor rodiny C — vnořená věta, 15 vět (zadání kola #81).

    python nalezy/vnorena_veta.py            # tabulky
    python nalezy/vnorena_veta.py --vety     # výpis po jedné

**Čtyři otázky, které měl rozbor zodpovědět, a odpovědi:**

1 · KTERÝ DEPREL A KOLIK VĚT
    `acl` 7 · `advcl` 5 · `xcomp` 4 · `csubj` 2 · **`ccomp` ANI JEDNOU**.
    Tabulka rozhodovacích pravidel, kterou reviewer předem sestavil, má
    tedy jednu položku, na kterou korpus nedosáhne — a `ccomp` je zrovna
    ta, kde bylo rozhodnutí „role hlavní predikace" nejjistější.

2 · MÁ `advcl` SPOJKU (`mark`)?
    **ANO, ve všech pěti a bez výjimky**: `pokud` 2×, `než` 2×, `aby` 1×,
    `protože` 1×. Jméno role je tedy z tvaru čitelné a předpoklad, že se
    u `advcl` smí učit, měřením obstál.

3 · PRŮNIK S `nmod+Gen`
    **4 z 12, ne 12.** Tohle je číslo, kvůli kterému stojí za to se
    zastavit: důvod pro pořadí „C před B" zněl, že C odblokuje těch
    dvanáct genitivů, které rodina A nedosáhla. Měření říká, že jich
    dosáhne nejvýš na čtyři.

4 · HLOUBKA VNOŘENÍ
    Cest se **dvěma** hranami rodiny C je 7 (proti 35 s jednou). Vnoření
    tedy jde do druhé úrovně a `DepthExceeded` není teoretická obava.

**Tenhle skript do jádra nesahá a nesmí.** Čte záznam měření a rozbor
z téže služby, kterou používá jádro; zařazení dělá z JMENOVEK ROZBORU
(`acl`, `advcl`, `mark`), ne z povrchu věty. Je to popis nálezu, ne druhé
čtení. Opravu dělá Builder jádra.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.oracle import UDPipeOracle  # noqa: E402

_TVAR = re.compile(r"„([^„\"]+)“ \(([^)]+)\)")

#: Hrany, které dělají z části věty VĚTU VE VĚTĚ.
RODINA_C = ("acl", "advcl", "xcomp", "ccomp", "csubj")


def _posledni_zaznam() -> Path:
    """Nejnovější podle ČASU, ne podle abecedy — viz `role_rozbor.py`."""
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not zaznamy:
        raise SystemExit("ve `mereni/` není žádný záznam")
    return zaznamy[-1]


def _vety(zaznam: Path) -> list[tuple[str, list[tuple[str, str]]]]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    found = []
    for tema in data.get("topics", ()):
        for veta in tema.get("sentences", ()):
            if veta.get("sole") != "role":
                continue
            tvary = _TVAR.findall(veta.get("reason") or "")
            hrany = {t.split(">")[-1].split("+")[0] for _, t in tvary}
            if hrany & set(RODINA_C):
                found.append((veta["text"], tvary))
    return found


def _genitivni(zaznam: Path) -> set[str]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return {
        veta["text"]
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
        if veta.get("sole") == "role"
        and any(
            t.split(">")[-1] == "nmod+Gen"
            for _, t in _TVAR.findall(veta.get("reason") or "")
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vety", action="store_true")
    args = parser.parse_args()

    zaznam = _posledni_zaznam()
    vety = _vety(zaznam)
    if not vety:
        print(f"{zaznam.name}: rodina C je prázdná")
        return 1

    oracle = UDPipeOracle()
    print("=" * 72)
    print(f"RODINA C — VNOŘENÁ VĚTA  ({len(vety)} vět) — {zaznam.name}")
    print("=" * 72)

    if args.vety:
        for cislo, (text, tvary) in enumerate(vety, 1):
            hrany = sorted(
                {
                    t.split(">")[-1].split("+")[0]
                    for _, t in tvary
                    if t.split(">")[-1].split("+")[0] in RODINA_C
                }
            )
            print(f"\n{cislo:2}. {text[:92]}")
            print(f"    hrany: {', '.join(hrany)}")
        return 0

    # 1 · deprely
    per_veta = collections.Counter()
    for _, tvary in vety:
        for hrana in {
            t.split(">")[-1].split("+")[0]
            for _, t in tvary
            if t.split(">")[-1].split("+")[0] in RODINA_C
        }:
            per_veta[hrana] += 1
    print("\n1 · DEPREL — kolik VĚT ho nese")
    for hrana in RODINA_C:
        kolik = per_veta.get(hrana, 0)
        znak = "  ← ANI JEDNOU" if kolik == 0 else ""
        print(f"   {hrana:10} {kolik:3}{znak}")

    # 2 · mark u advcl
    marky: collections.Counter[str] = collections.Counter()
    bez_marku = 0
    for text, _ in vety:
        reading = oracle.parse(text).readings[0]
        for token in reading.tokens:
            if token.deprel != "advcl":
                continue
            mark = [
                t.form.lower()
                for t in reading.tokens
                if t.head == token.index and t.deprel == "mark"
            ]
            if mark:
                marky[mark[0]] += 1
            else:
                bez_marku += 1
    print("\n2 · MÁ `advcl` SPOJKU (`mark`)?")
    for spojka, kolik in marky.most_common():
        print(f"   „{spojka}“ {kolik}×")
    print(f"   BEZ marku: {bez_marku}")

    # 3 · průnik s nmod+Gen
    genitivni = _genitivni(zaznam)
    cecka = {text for text, _ in vety}
    print("\n3 · PRŮNIK S `nmod+Gen`")
    print(f"   vět s nmod+Gen: {len(genitivni)}")
    print(f"   vět rodiny C:   {len(cecka)}")
    print(f"   PRŮNIK:         {len(genitivni & cecka)}")

    # 4 · hloubka
    hloubky: collections.Counter[int] = collections.Counter()
    for _, tvary in vety:
        for _, tvar in tvary:
            kroky = [k.split("+")[0] for k in tvar.split(">")]
            hloubky[sum(1 for k in kroky if k in RODINA_C)] += 1
    print("\n4 · HLOUBKA VNOŘENÍ (hran rodiny C na jedné cestě)")
    for hloubka, kolik in sorted(hloubky.items()):
        print(f"   {hloubka} hran: {kolik:3} cest")

    print("\n" + "=" * 72)
    print(
        "NA CO SE DÁVÁ POZOR: průnik s genitivy je 4 z 12, ne 12. Důvod\n"
        "pro pořadí „C před B“ zněl, že C ty genitivy odblokuje — měření\n"
        "říká, že dosáhne nejvýš na třetinu z nich."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
