#!/usr/bin/env python
"""Rodina `rozbor` — jedenáct vět, čtyři skupiny *(zadání kola #104)*.

    python nalezy/rozbor_rodiny.py

Reviewer žádal ROZKLAD PŘED OPRAVOU a řekl u toho jednu důležitou věc:
*„jestli je většina vlastnost textu, je správná odpověď to říct a směr
opustit — ne ho dotlačit."* Tenhle skript je to měření.

**Závěr: ANI JEDNA z těch jedenácti není vada čtení.** Devět je vlastnost
textu nebo už pojmenovaná mez, dvě jsou doptání, tedy správné chování.

**Zařazení se čte z HLÁŠENÍ JÁDRA, ne z povrchu věty.** Jádro od kol #101
a #102 samo říká, co vidí (`JMENNÁ FRÁZE`, `NADPIS`, `týž tvar`, `Čtu to
jako`), takže rozklad jen sbírá, co už bylo řečeno — nepřidává druhé
čtení, které by se s prvním rozešlo.

**A jeden nález o měřicí vrstvě.** Dvě věty, u kterých se jádro PTÁ
*„které z těch dvou čtení?"*, jsou v záznamu `NEPŘEČTENO` s
`open_questions=0`, ačkoli `TurnResult.question` je vyplněný. Je to vada
`cb-wiki.py`, ne jádra — ale zkresluje právě tu metriku, která má
`ZAPSÁNO` nahradit.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

#: Jak se pozná skupina. Klíč je kus HLÁŠENÍ JÁDRA — ne slovo z věty:
#: jádro už rozhodlo a tenhle skript to rozhodnutí jen čte. Pořadí je
#: pořadím zkoušení a je významné (`NADPIS` a `JMENNÁ FRÁZE` se nepřekrývají,
#: ale kdyby jednou začaly, ať je vidět, co má přednost).
SKUPINY: tuple[tuple[str, str], ...] = (
    ("NADPIS", "nadpis splynulý s větou — vlastnost TEXTU (segmentace, W‑64)"),
    ("JMENNÁ FRÁZE", "jmenný fragment — není věta"),
    ("týž tvar", "kolize dvou členů, z rozboru NEROZLIŠITELNÁ (W‑63)"),
    ("Čtu to jako", "dvě čtení a jádro se PTÁ — správné chování, ne mez"),
)


def _zaznam() -> Path:
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not zaznamy:
        raise SystemExit("ve `mereni/` není žádný záznam")
    return zaznamy[-1]


def main() -> int:
    zaznam = _zaznam()
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    skupiny: collections.Counter[str] = collections.Counter()
    radky: list[tuple[str, str]] = []
    for tema in data.get("topics", ()):
        for veta in tema.get("sentences", ()):
            if veta.get("sole") != "rozbor":
                continue
            duvod = str(veta.get("reason") or "")
            popis = next(
                (popis for klic, popis in SKUPINY if klic in duvod),
                "NEZAŘAZENO — to je nález",
            )
            skupiny[popis] += 1
            radky.append((popis, veta["text"]))

    print("=" * 72)
    print(f"RODINA `rozbor` — {sum(skupiny.values())} vět — {zaznam.name}")
    print("=" * 72)
    for popis, kolik in skupiny.most_common():
        print(f"\n  {kolik}× {popis}")
        for p, text in radky:
            if p == popis:
                print(f"       {text[:76]}")

    vada_cteni = skupiny.get("NEZAŘAZENO — to je nález", 0)
    print("\n" + "=" * 72)
    print(
        f"VAD ČTENÍ: {vada_cteni}. Zbytek je vlastnost textu, už pojmenovaná\n"
        "mez, nebo doptání. Dotlačit tenhle směr by znamenalo opravovat\n"
        "TEXTY, ne čtení — a jediné, co by z toho vzniklo, je systém,\n"
        "který přečte nadpis jako větu."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
