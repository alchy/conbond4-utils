#!/usr/bin/env python
"""Rozbor třídy `role` — 40 vět, největší zbylá mezera.

    python nalezy/role_rozbor.py            # tvary podle četnosti + rodiny
    python nalezy/role_rozbor.py --vety     # výpis po jedné větě

**Otázka, kterou má rozbor zodpovědět** (zadání kola #77): je `role`
JEDNA mezera, nebo ČTYŘICET jednotlivých doptání, která jsou vlastně
v pořádku? Na tom závisí, jestli je to vada, nebo normální provoz dialogu.

**Odpověď: ani jedno.** Je to JEDNA DOMINANTNÍ MEZERA navrstvená
několika dalšími — a to je pro rozhodování o opravě podstatnější než
obojí z původních možností.

  * **Rodina A — přívlastek ve jmenné frázi** (`nmod`, `amod`, `nummod`,
    `det`) je ve VŠECH 40 VĚTÁCH. Ani jedna věta se bez ní neobejde.
  * Sama o sobě by ale odblokovala jen **6 vět**: zbylých 34 má vedle ní
    ještě jinou rodinu.
  * Teprve pět rodin dohromady (A+B+C+D+E) pokryje **25 ze 40**.

Není to tedy „čtyřicet různých doptání" — jedna konstrukce se opakuje
pořád dokola. A není to ani „jedna mezera" — opravit ji samotnou skoro
nic neodblokuje, protože věty encyklopedické prózy nesou několik těch
konstrukcí naráz.

**Co z toho plyne pro pořadí oprav**: samostatná rodina má malý výnos,
takže měřit „kolik vět uvolní tahle jedna oprava" je zavádějící metrika.
Rozhodovat se má podle KUMULATIVNÍHO pokrytí, které tenhle skript počítá.

**Tenhle skript do jádra nesahá a nesmí.** Čte záznam měření, tedy to, co
jádro samo vrátilo, a zařazení do rodin dělá z JMENOVEK ROZBORU
(`nmod`, `acl`, `conj`, …), ne z povrchu věty. Je to popis nálezu, ne
druhé čtení. Opravu dělá Builder jádra.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"

#: Zmínka a její povrchový tvar z hlášky jádra: „slovo" (cesta+Pád).
_TVAR = re.compile(r"„([^„\"]+)“ \(([^)]+)\)")

#: Dependenční hrana → RODINA konstrukce. Zařazení je strukturní: co je
#: uvnitř jmenné fráze, co je vnořená věta, co je koordinace. Povrch věty
#: do toho nemluví.
RODINY: dict[str, str] = {
    "nmod": "A · přívlastek ve jmenné frázi",
    "amod": "A · přívlastek ve jmenné frázi",
    "nummod": "A · přívlastek ve jmenné frázi",
    "det": "A · přívlastek ve jmenné frázi",
    "flat": "B · víceslovné jméno",
    "appos": "B · víceslovné jméno",
    "acl": "C · vnořená věta",
    "xcomp": "C · vnořená věta",
    "advcl": "C · vnořená věta",
    "ccomp": "C · vnořená věta",
    "csubj": "C · vnořená věta",
    "conj": "D · koordinace",
    "obl": "E · příslovečné určení",
    "obj": "F · předmět",
    "nsubj": "G · podmět",
}

#: Pořadí, ve kterém se počítá kumulativní pokrytí. Je to pořadí podle
#: ČETNOSTI rodiny, ne podle domnělé snadnosti opravy — snadnost je odhad,
#: četnost je měření.
PORADI = ("A", "B", "C", "D", "E", "F", "G", "Z")


def _posledni_zaznam() -> Path:
    """Nejnovější záznam podle ČASU, ne podle abecedy.

    Abecední pořadí tu klame: `2026-08-15.json` je starší než
    `2026-08-15-8b691b3.json`, ale řadí se za něj. Rozbor by pak mluvil
    o jiné revizi, než na kterou se odvolává — a nikdo by si toho
    nevšiml, protože čísla by pořád dávala smysl.
    """
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not zaznamy:
        raise SystemExit("ve `mereni/` není žádný záznam")
    return zaznamy[-1]


def _vety(zaznam: Path) -> list[dict]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return [
        veta
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
        if veta.get("sole") == "role"
    ]


def _tvary(veta: dict) -> list[tuple[str, str]]:
    return _TVAR.findall(veta.get("reason") or "")


def _rodina(tvar: str) -> str:
    """Rodina podle POSLEDNÍ hrany cesty — na ní se čtení zaseklo."""
    hrana = tvar.split(">")[-1].split("+")[0]
    return RODINY.get(hrana, f"Z · {hrana}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vety", action="store_true")
    args = parser.parse_args()

    zaznam = _posledni_zaznam()
    vety = _vety(zaznam)
    if not vety:
        print(f"{zaznam.name}: třída `role` je prázdná")
        return 1

    print("=" * 72)
    print(f"ROZBOR TŘÍDY `role`  ({len(vety)} vět) — {zaznam.name}")
    print("=" * 72)

    if args.vety:
        for cislo, veta in enumerate(vety, 1):
            rodiny = sorted({_rodina(t)[0] for _, t in _tvary(veta)})
            print(f"\n{cislo:2}. {veta['text'][:92]}")
            print(f"    rodiny: {', '.join(rodiny)}")
            for slovo, tvar in _tvary(veta):
                print(f"      „{slovo}“ — {tvar}")
        return 0

    # -- tvary podle četnosti ---------------------------------------------
    vet_s_hranou: dict[str, set[int]] = collections.defaultdict(set)
    vyskytu: collections.Counter[str] = collections.Counter()
    for index, veta in enumerate(vety):
        for _, tvar in _tvary(veta):
            hrana = tvar.split(">")[-1]
            vet_s_hranou[hrana].add(index)
            vyskytu[hrana] += 1

    print("\nPOVRCHOVÝ TVAR BEZ JMÉNA — podle počtu VĚT, které ho sdílejí")
    print("   tvar                       vět   výskytů")
    for hrana, veta_set in sorted(
        vet_s_hranou.items(), key=lambda x: (-len(x[1]), x[0])
    ):
        print(f"   {hrana:26} {len(veta_set):3}   {vyskytu[hrana]:3}")

    # -- rodiny -----------------------------------------------------------
    per_veta: list[set[str]] = [
        {_rodina(t)[0] for _, t in _tvary(veta)} for veta in vety
    ]
    vet_s_rodinou: dict[str, set[int]] = collections.defaultdict(set)
    sama: collections.Counter[str] = collections.Counter()
    for index, rodiny in enumerate(per_veta):
        for zkratka in rodiny:
            vet_s_rodinou[zkratka].add(index)
        if len(rodiny) == 1:
            sama[next(iter(rodiny))] += 1
    jmena = {r[0]: r for r in {_rodina(t) for v in vety for _, t in _tvary(v)}}

    print("\nRODINA KONSTRUKCE                     vyskytuje se   SAMA ve větě")
    for zkratka, veta_set in sorted(
        vet_s_rodinou.items(), key=lambda x: -len(x[1])
    ):
        print(f"   {jmena.get(zkratka, zkratka):36} {len(veta_set):3} vět      {sama[zkratka]:3}")

    print("\nKUMULATIVNÍ POKRYTÍ — kolik z vět by opravy odblokovaly DOHROMADY")
    for konec in range(1, len(PORADI) + 1):
        skupina = set(PORADI[:konec])
        hotovo = sum(1 for rodiny in per_veta if rodiny <= skupina)
        print(f"   {'+'.join(PORADI[:konec]):22} {hotovo:3} / {len(vety)}")

    histogram = collections.Counter(len(r) for r in per_veta)
    print(
        "\nkolik RODIN nese jedna věta: "
        + ", ".join(f"{k}× rodina: {v} vět" for k, v in sorted(histogram.items()))
    )
    print("=" * 72)
    print(
        "ODPOVĚĎ NA OTÁZKU KOLA: ani jedna mezera, ani čtyřicet doptání.\n"
        "Rodina A je ve VŠECH větách, ale sama odblokuje jen zlomek —\n"
        "encyklopedická věta nese několik těch konstrukcí naráz. Pořadí\n"
        "oprav se proto má řídit KUMULATIVNÍM pokrytím, ne tím, kolik vět\n"
        "uvolní jedna oprava samotná."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
