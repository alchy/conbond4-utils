#!/usr/bin/env python
"""Jména rolí — zeď, před kterou korpus stojí *(zadání kola #96)*.

    python nalezy/role_zed.py             # rozklad po tvarech
    python nalezy/role_zed.py --plnice    # čím se `v+Loc` plní
    python nalezy/role_zed.py --pass      # `nsubj:pass` — je to vada?

**Čte se z KASKÁDY, ne ze záznamu**, a je to nutné: `cb-wiki.py` ukládá
`reason` zkrácený na ~160 znaků, takže ze záznamu vyjde 10 vět a 8 tvarů
místo skutečných čísel. Je to potřetí, co by mě záznam poslal špatně
(nejdřív abeceda, pak čas, teď délka pole), a pořád táž rodina: **měřit
podle něčeho, co o měřené věci nic neříká**.

**Co má tenhle rozbor rozhodnout** (a rozhodnutí je první krok, ne kód):

  1 · Je „`v+Loc` → `kde`" ZNALOST O JAZYCE, nebo HYPOTÉZA O TÉHLE VĚTĚ?
  2 · Kde ta znalost bydlí, jestli vznikne.
  3 · Patří `nsubj:pass` mezi okolnostní role vůbec?

**Sort filleru se k rozhodnutí použít NEDÁ, a je to důležité.** V § 3.6
platí, že SORT PLYNE Z ROLE (`kde` → `Place`). Kdyby role plynula ze
sortu, byl by to kruh. Co je k dispozici PŘED rozhodnutím, je jen to, co
stojí v rozboru: lemma filleru, jeho `upos` a rysy — hlavně `NameType`,
kde UD samo odlišuje `Geo` od ostatních.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.cascade import generate, surface_roles, surface_role  # noqa: E402


def _zaznam() -> Path:
    """Nejnovější záznam TÉŽE sady — viz `titul_jmeno.py`."""
    podle_casu = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not podle_casu:
        raise SystemExit("ve `mereni/` není žádný záznam")
    posledni = podle_casu[-1]
    return posledni


def _vety(zaznam: Path) -> list[str]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return [
        veta["text"]
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
    ]


def _cteni(oracle: UDPipeOracle, text: str):  # noqa: ANN202
    try:
        reading = oracle.parse(text).readings[0]
    except Exception:  # noqa: BLE001 — nerozebratelná věta se přeskočí
        return None, None
    try:
        kandidati = generate(reading)
    except Exception:  # noqa: BLE001
        return reading, None
    return reading, (kandidati[0].predication if kandidati else None)


def rozklad(oracle: UDPipeOracle, vety: list[str]) -> None:
    tvary: collections.Counter[str] = collections.Counter()
    s_otazkou = 0
    for text in vety:
        _, predication = _cteni(oracle, text)
        if predication is None:
            continue
        shapes = surface_roles(predication)
        if shapes:
            s_otazkou += 1
        for shape in shapes:
            tvary[shape] += 1

    vyskytu = sum(tvary.values())
    print("=" * 72)
    print("TVARY BEZ VÝZNAMU — na co se systém ptá")
    print("=" * 72)
    print(f"\nvět: {len(vety)} · vět s aspoň jednou takovou rolí: {s_otazkou}")
    print(f"různých tvarů: {len(tvary)} · výskytů celkem: {vyskytu}\n")
    beh = 0
    for poradi, (tvar, kolik) in enumerate(tvary.most_common(), 1):
        beh += kolik
        znak = "  ← 77,5 %" if poradi == 15 else ""
        if poradi <= 20:
            print(
                f"  {poradi:2}. {tvar:16} {kolik:3}   "
                f"kumulativně {beh / vyskytu:5.1%}{znak}"
            )
    print(f"\n  prvních 15 tvarů pokrývá {sum(k for _, k in tvary.most_common(15)) / vyskytu:.1%}")


def plnice(oracle: UDPipeOracle, vety: list[str], tvar: str) -> None:
    """ČÍM se ten tvar plní. Rozhoduje otázku (1).

    Vypisuje LEMMA a `NameType`, protože to jsou jediné dvě věci, které
    o filleru stojí v rozboru dřív, než se o roli rozhodne. Sort použít
    nejde — ten plyne z role (§ 3.6) a byl by to kruh.
    """
    lemmata: collections.Counter[str] = collections.Counter()
    typy: collections.Counter[str] = collections.Counter()
    ukazky: list[str] = []
    for text in vety:
        reading, predication = _cteni(oracle, text)
        if predication is None or reading is None:
            continue
        if tvar not in surface_roles(predication):
            continue
        for role in predication.roles:
            if role.name != tvar:
                continue
            token = next(
                (t for t in reading.tokens if t.index == role.mention.token_index),
                None,
            )
            if token is None:
                continue
            feats = dict(token.feats)
            lemmata[token.lemma] += 1
            typy[feats.get("NameType", "(bez NameType)")] += 1
            if len(ukazky) < 12:
                ukazky.append(f"{token.lemma:16} {feats.get('NameType', '—'):8} {text[:56]}")

    print("=" * 72)
    print(f"ČÍM SE PLNÍ „{tvar}“ — rozhoduje otázku „znalost, nebo hypotéza?“")
    print("=" * 72)
    print(f"\nvýskytů: {sum(lemmata.values())} · různých lemmat: {len(lemmata)}\n")
    print("  podle `NameType` (jediný rys, kterým UD samo odlišuje jména míst):")
    for typ, kolik in typy.most_common():
        print(f"    {typ:20} {kolik}")
    print("\n  nejčastější lemmata:")
    for lemma, kolik in lemmata.most_common(15):
        print(f"    {lemma:20} {kolik}")
    print("\n  ukázky:")
    for u in ukazky:
        print(f"    {u}")


def pasivum(oracle: UDPipeOracle, vety: list[str]) -> None:
    """`nsubj:pass` mezi okolnostními rolemi — otázka (3).

    Podmět trpné věty NENÍ okolnost. Jestli se na něj systém ptá „co ta
    role znamená", ptá se na něco, co ví.
    """
    kde: list[tuple[str, str]] = []
    for text in vety:
        reading, predication = _cteni(oracle, text)
        if predication is None or reading is None:
            continue
        for shape in surface_roles(predication):
            if "nsubj" not in shape:
                continue
            kde.append((shape, text[:70]))
    print("=" * 72)
    print("`nsubj:pass` MEZI OKOLNOSTNÍMI ROLEMI — je to vada?")
    print("=" * 72)
    print(f"\nvýskytů: {len(kde)}\n")
    for shape, text in kde[:15]:
        print(f"  {shape:16} {text}")
    if not kde:
        print("  ŽÁDNÝ — kaskáda se na podmět trpné věty neptá.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plnice", default="")
    parser.add_argument("--pass", dest="pasiv", action="store_true")
    args = parser.parse_args()

    zaznam = _zaznam()
    vety = _vety(zaznam)
    oracle = UDPipeOracle()

    if args.pasiv:
        pasivum(oracle, vety)
    elif args.plnice:
        plnice(oracle, vety, args.plnice)
    else:
        rozklad(oracle, vety)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
