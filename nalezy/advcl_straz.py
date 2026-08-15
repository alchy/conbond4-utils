#!/usr/bin/env python
"""Tři věty s `advcl`, které stráž nebere — je úzká, nebo správná?

    python nalezy/advcl_straz.py            # rozbor tří vět
    python nalezy/advcl_straz.py --korpus   # podtypy advcl v celém korpusu

**Otázka kola #83**: stavba `advcl` odblokovala dvě věty z pěti. U tří
zbylých se stráž (`advcl` POD PŘÍSUDKEM a SE SPOJKOU) neuplatnila. Je ta
stráž správně ohraničená, nebo příliš úzká?

**Odpověď: účinek je správný u všech tří, ale u DVOU ZE TŘÍ z nesprávného
důvodu.** A to je horší, než kdyby byla prostě úzká — správnost, která
stojí na náhodě, se rozpadne při první změně, o které nikdo nebude vědět.

  1 · „Vlastnictví … se ukázalo **jako snižující** hladinu…"
      deprel `advcl:pred`, `ADJ`, POD PŘÍSUDKEM, MÁ `mark` („jako").
      Stráž ho nebere jen proto, že porovnává deprel ŘETĚZCOVOU SHODOU
      (`!= "advcl"`), takže podtyp `advcl:pred` propadne. Není to
      rozhodnutí, je to vedlejší účinek zápisu.

  3 · „**Jako nemístné** viděl v tehdejší situaci hledání viníků."
      Totéž: `advcl:pred`, `ADJ`, pod přísudkem, `mark` = „Jako".

  2 · „Vhodní mazlíčci procházejí…, **pokud** se jedná o psa, … **aby**
      se stali…" — dvakrát `advcl`, obojí pod `programy`/`NOUN`.
      Tady stráž funguje PŘESNĚ, jak byla zamýšlená: `advcl` pod jménem
      je přívlastek toho jména a patří k `acl`.

**Zahrnout `advcl:pred` by ale bylo VĚCNĚ ŠPATNĚ.** Je to DOPLNĚK
(predikativní komplement), ne okolnost: „ukázalo se **jako snižující**"
neodpovídá na proč ani kdy, ale na to, ČÍM se ta věc ukázala být.
Sémanticky je blíž `xcomp` — druhý přísudek o témž podmětu — a `xcomp`
se podle rozhodnutí z kola #81 SKLÁDÁ DO PŘÍSUDKU, ne přidává roli.

**A není to okrajové.** V měřeném korpusu je `advcl:pred` ČASTĚJŠÍ než
vlastní `advcl`: 30 proti 21. Nechat tak velký podtyp viset na řetězcové
shodě znamená, že se o něm nerozhoduje — jen se na něj zapomíná.

**Tenhle skript do jádra nesahá a nesmí.** Rozbor bere z téže služby,
kterou používá jádro, a zařazení dělá z JMENOVEK (`advcl:pred`, `mark`,
`upos`), ne z povrchu věty. Opravu dělá Builder jádra.
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

#: Věty, u kterých se stráž neuplatnila. Opsané z měření nad revizí
#: 2a28455, aby šel nález přehrát i bez běhu na Wikipedii.
VETY: tuple[str, ...] = (
    "Vlastnictví domácího mazlíčka se ukázalo jako významně snižující "
    "hladinu triglyceridů a tím i riziko srdečních onemocnění u starších "
    "lidí.",
    "Vhodní mazlíčci procházejí procesem výběru a pokud se jedná o psa, "
    "také dodatečnými výcvikovými programy, aby by se stali "
    "terapeutickými psy.",
    "Jako nemístné viděl v tehdejší situaci hledání viníků.",
)


def _posledni_zaznam() -> Path:
    """Nejnovější podle ČASU, ne podle abecedy — viz `role_rozbor.py`."""
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not zaznamy:
        raise SystemExit("ve `mereni/` není žádný záznam")
    return zaznamy[-1]


def rozbor_vety(oracle: UDPipeOracle, text: str) -> list[dict[str, object]]:
    reading = oracle.parse(text).readings[0]
    root = next((t for t in reading.tokens if t.head == 0), None)
    found: list[dict[str, object]] = []
    for token in reading.tokens:
        if not token.deprel.startswith("advcl"):
            continue
        head = next((t for t in reading.tokens if t.index == token.head), None)
        found.append(
            {
                "slovo": token.form,
                "deprel": token.deprel,
                "upos": token.upos,
                "pod": f"{head.form}/{head.upos}" if head else "?",
                "je_přísudek": bool(head and root and head.index == root.index),
                "mark": [
                    t.form
                    for t in reading.tokens
                    if t.head == token.index and t.deprel == "mark"
                ],
            }
        )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--korpus", action="store_true")
    args = parser.parse_args()

    oracle = UDPipeOracle()

    if args.korpus:
        zaznam = _posledni_zaznam()
        data = json.loads(zaznam.read_text(encoding="utf-8"))
        podtypy: collections.Counter[str] = collections.Counter()
        kde: collections.Counter[str] = collections.Counter()
        for tema in data.get("topics", ()):
            for veta in tema.get("sentences", ()):
                try:
                    reading = oracle.parse(veta["text"]).readings[0]
                except Exception:  # noqa: BLE001 — nerozebratelná věta se přeskočí
                    continue
                root = next((t for t in reading.tokens if t.head == 0), None)
                for token in reading.tokens:
                    if not token.deprel.startswith("advcl"):
                        continue
                    podtypy[token.deprel] += 1
                    head = next(
                        (t for t in reading.tokens if t.index == token.head), None
                    )
                    kde[
                        "přísudek"
                        if head and root and head.index == root.index
                        else (head.upos if head else "?")
                    ] += 1
        print("=" * 72)
        print(f"PODTYPY `advcl` V CELÉM KORPUSU — {zaznam.name}")
        print("=" * 72)
        for deprel, kolik in podtypy.most_common():
            print(f"   {deprel:16} {kolik:3}")
        print("\n   pod čím visí:")
        for co, kolik in kde.most_common():
            print(f"   {co:16} {kolik:3}")
        print(
            "\n`advcl:pred` je ČASTĚJŠÍ než vlastní `advcl`. Nechat tak velký\n"
            "podtyp viset na řetězcové shodě znamená, že se o něm\n"
            "nerozhoduje — jen se na něj zapomíná."
        )
        return 0

    print("=" * 72)
    print("TŘI VĚTY, U KTERÝCH SE STRÁŽ NEUPLATNILA")
    print("=" * 72)
    for cislo, text in enumerate(VETY, 1):
        print(f"\n{cislo}. {text[:88]}")
        nalezy = rozbor_vety(oracle, text)
        if not nalezy:
            print("    (parser tu žádné `advcl` nedal)")
            continue
        for n in nalezy:
            duvod = (
                "ŘETĚZCOVÁ SHODA — podtyp propadne"
                if n["deprel"] != "advcl" and n["je_přísudek"] and n["mark"]
                else "STRÁŽ ZÁMĚRNĚ — není pod přísudkem"
                if not n["je_přísudek"]
                else "bez spojky"
            )
            print(
                f"    {n['slovo']:12} deprel={n['deprel']:12} {n['upos']:5} "
                f"pod={n['pod']:14} přísudek={n['je_přísudek']!s:5} "
                f"mark={n['mark']}"
            )
            print(f"        → stráž ho nebere: {duvod}")
    print("\n" + "=" * 72)
    print(
        "ZÁVĚR: účinek stráže je správný u všech tří, ale u DVOU ZE TŘÍ\n"
        "z nesprávného důvodu — vylučuje je řetězcová shoda, ne rozhodnutí.\n"
        "Zahrnout `advcl:pred` by přitom bylo VĚCNĚ ŠPATNĚ: je to DOPLNĚK\n"
        "(„ukázalo se JAKO snižující“), ne okolnost, a sémanticky patří\n"
        "k `xcomp`, který se podle #81 skládá do přísudku."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
