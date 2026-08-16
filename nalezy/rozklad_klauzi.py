#!/usr/bin/env python
"""Rozklad KLAUZÍ — měření a rodiny, bez hypotézy *(zadání kola #148)*.

    python nalezy/rozklad_klauzi.py

Po nálezu z #147 (ztracený člen, který je účastníkem děje a NENÍ
v klauzi, v tomhle korpusu prakticky neexistuje) je klauze největší
zbývající kus. Tahle sonda ho MĚŘÍ — nenavrhuje, co s ním.

**Hlavní číslo: ze 197 klauzí se 159 (81 %) přečte jako samostatná
věta.** Jádro tedy klauzi UMÍ přečíst; co neumí, je spojit ji s větou,
ve které visí.

RODINY PODLE TOHO, K ČEMU SE KLAUZE VÁŽE (ne podle spojky — to by byl
výčet slov, dvanáctkrát vyvrácený, W‑32 … W‑83):

    je ARGUMENT slovesa   75 klauzí   (ccomp, csubj, xcomp)
    určuje JMÉNO          71 klauzí   (acl, acl:relcl)
    doplněk PŘÍSUDKU      30 klauzí   (advcl:pred)
    určuje DĚJ            21 klauzí   (advcl)

Vztažná věta má navíc vlastní půlku problému: z 58 jich 52 nese vztažné
zájmeno, a to zájmeno ODKAZUJE NA HLAVU („lidé, **kteří** nemají…").
Přečtená klauze proto dá `¬mít(kdo:·který)` — predikaci se správnou
stavbou a s uzlem, který nikdo nezaložil.
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

from core_semantics.cascade import base_deprel  # noqa: E402
from core_semantics.oracle import Reading, Token, UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
from core_semantics.tests import golden  # noqa: E402

#: K ČEMU SE KLAUZE VÁŽE. Bere se to z DEPRELU, tedy ze stavby, ne ze
#: spojky — „že" uvozuje `ccomp` i `acl` a rozhodnout to slovem nejde.
DRUH: dict[str, str] = {
    "ccomp": "je ARGUMENT slovesa",
    "csubj": "je ARGUMENT slovesa",
    "xcomp": "je ARGUMENT slovesa",
    "acl": "určuje JMÉNO",
    "acl:relcl": "určuje JMÉNO",
    "advcl:pred": "doplněk PŘÍSUDKU",
    "advcl": "určuje DĚJ",
}

#: Vztažná zájmena, která se hledají jako NOSIČ ODKAZU. Je to seznam
#: MĚŘICÍ SONDY, ne jádra — sonda musí být vidět, podle čeho počítá.
VZTAZNA = ("který", "jenž", "co", "kdo", "jehož", "kde")


def _podstrom(token: Token, reading: Reading) -> str:
    """Klauze jako samostatná věta — doslova její podstrom."""
    deti: dict[int, list[Token]] = collections.defaultdict(list)
    for x in reading.tokens:
        deti[x.head].append(x)
    strom: list[Token] = []
    zasobnik = [token]
    while zasobnik:
        uzel = zasobnik.pop()
        strom.append(uzel)
        zasobnik.extend(deti[uzel.index])
    slova = [x.form for x in sorted(strom, key=lambda x: x.index)
             if x.upos != "PUNCT"]
    veta = " ".join(slova).lstrip(", ")
    return veta[0].upper() + veta[1:] + "." if veta else ""


def main() -> int:
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    data = json.loads(zaznamy[-1].read_text(encoding="utf-8"))
    vety = [s["text"] for t in data["topics"] for s in t["sentences"]]

    oracle = UDPipeOracle()
    rodina: collections.Counter[str] = collections.Counter()
    cte: collections.Counter[str] = collections.Counter()
    ukazka: dict[str, list[str]] = collections.defaultdict(list)
    vztazne = zajmeno = 0
    nosic: collections.Counter[str] = collections.Counter()

    for text in vety:
        try:
            reading = oracle.parse(text).readings[0]
        except Exception:  # pragma: no cover — měřicí sonda
            continue
        deti: dict[int, list[Token]] = collections.defaultdict(list)
        for x in reading.tokens:
            deti[x.head].append(x)
        for token in reading.tokens:
            deprel = (
                token.deprel if token.deprel in DRUH
                else base_deprel(token.deprel)
            )
            if deprel not in DRUH:
                continue
            druh = DRUH[deprel]
            rodina[druh] += 1
            if token.deprel == "acl:relcl":
                vztazne += 1
                nalezena = [c for c in deti[token.index] if c.lemma in VZTAZNA]
                if nalezena:
                    zajmeno += 1
                    nosic[f"{nalezena[0].lemma}/{nalezena[0].deprel}"] += 1
            veta = _podstrom(token, reading)
            session = Session(lexicon=golden.golden_lexicon())
            try:
                result = session.utter(veta, oracle)
            except Exception:  # pragma: no cover — měřicí sonda
                continue
            if result.predication is None:
                continue
            cte[druh] += 1
            if len(ukazka[druh]) < 2:
                ukazka[druh].append(
                    f"„{veta[:52]}“ → {str(result.predication)[:48]}"
                )

    print("=" * 74)
    print(f"KLAUZE V KORPUSU — {len(vety)} vět")
    print("=" * 74)
    celkem = sum(rodina.values())
    ctenych = sum(cte.values())
    for druh, kolik in rodina.most_common():
        print(f"\n  {druh:22} {kolik:4} klauzí · jako samostatná věta se "
              f"PŘEČTE {cte[druh]:3}")
        for radek in ukazka[druh]:
            print(f"        {radek}")
    print("\n" + "=" * 74)
    print(f"CELKEM {celkem} klauzí · PŘEČTE SE {ctenych} "
          f"({100 * ctenych // max(celkem, 1)} %)")
    print(f"VZTAŽNÝCH VĚT {vztazne} · s vztažným zájmenem {zajmeno}")
    for k, n in nosic.most_common(8):
        print(f"   {n:3}  {k}")
    print(
        "\nJádro klauzi UMÍ PŘEČÍST; co neumí, je spojit ji s větou, ve\n"
        "které visí. U vztažné věty je to navíc dvojí úloha: predikace\n"
        "se přečte, ale její podmět je `·který` — uzel, který nikdo\n"
        "nezaložil a který MÁ BÝT hlavou z věty nadřazené."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
