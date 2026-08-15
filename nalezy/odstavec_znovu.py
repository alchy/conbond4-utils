#!/usr/bin/env python
"""Odstavec z #105 PŘEMĚŘENÝ — a měří se ÚČINEK, ne existence *(kolo #120)*.

    python nalezy/odstavec_znovu.py

Reviewer chtěl u KAŽDÉ otázky vědět, jestli na ni existuje tah, a teprve
podle výsledku psát nebo nepsat dvacátou druhou doménu. V #105 to bylo
**7 tahů a 6 otázek bez tahu**.

**Dnes je to 7 tahů a 3 otázky bez tahu — a doména se přesto nepíše.**
Tři překážky z #105 jsou zavřené (souřadný přísudek W‑70/71/73, časový
údaj W‑74/75/77, zvratné zájmeno W‑68), ale zbyly dvě věci, a druhá
z nich je nová:

  1 · TŘI OTÁZKY TAH NEMAJÍ. „zápal"/„plic" je souřadné JMÉNO a „Praze"
      je `nmod` pod obecným jménem. Obě jsou pojmenované meze — a
      `names_role` u nich sice tah PŘIJME („✓ naučeno"), ale ČTENÍ SE
      NEZMĚNÍ. To je horší než chybějící tah: vypadá to jako odpověď.

  2 · ODSTAVEC SE NEZAPÍŠE ANI TEHDY, KDYŽ SE ODPOVÍ NA VŠECHNO. První
      věta projde na „✓ přečteno" a skončí na `(zakotvení neproběhlo —
      do báze nejde nic)`: `si` se stane rolí s fillerem a ta role dostane
      za uzel „se". Zvratné zájmeno ale ÚČASTNÍK NENÍ — je to část tvaru
      slovesa („přivodit si"). W‑68 odstranila nepravdivou OTÁZKU, role
      zůstala.

**Doména se proto nepíše ani teď.** Každý krok v ní má být odpovědí na
otázku, kterou systém sám položil; kroky, které tam jsou „aby to vyšlo",
by z ní udělaly zkoušku psanou podle výsledku — a doména, kde je
`writes` všude prázdné, nedokládá nic.
"""

from __future__ import annotations

import sys
from pathlib import Path

_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.cascade import (  # noqa: E402
    AWAITING_QUANTIFIER,
    AWAITING_REFERENCE,
    surface_roles,
)
from core_semantics.lexicon import Operation  # noqa: E402
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import (  # noqa: E402
    Session,
    answers_quantifier,
    names_role,
)
from core_semantics.tests import golden  # noqa: E402

#: Čtyři DOSLOVNÉ věty z korpusu, v pořadí a beze změny — stejné jako
#: v `odstavec_tahy.py`, aby se ta dvě měření dala postavit vedle sebe.
ODSTAVEC: tuple[str, ...] = (
    "V prosinci 1938 si Karel Čapek přivodil lehkou chřipku.",
    "Ke chřipce se přidal zánět ledvin a zápal plic.",
    "Jeho stav se přechodně zlepšil, ale brzy musel znovu ulehnout.",
    "Byl pohřben na Vyšehradském hřbitově v Praze.",
)


def _tahy(oracle: UDPipeOracle) -> tuple[int, int]:
    """Kolik otázek TAH MÁ a kolik ho nemá — počítáno jako v #105."""
    session = Session(lexicon=golden.golden_lexicon())
    ma = nema = 0
    for text in ODSTAVEC:
        result = session.utter(text, oracle)
        predication = result.predication
        print(f"\n» {text}")
        if predication is None:
            print("   NEPŘEČTENO")
            continue
        tvary = list(surface_roles(predication))
        kvant = [r.name for r in predication.roles if r.awaiting == AWAITING_QUANTIFIER]
        odkaz = [r.name for r in predication.roles if r.awaiting == AWAITING_REFERENCE]
        ztraceno = [f for f, _ in result.turn.lost]
        ma += len(tvary) + len(kvant) + len(odkaz)
        nema += len(ztraceno)
        print(f"   čtení:      {predication}")
        print(f"   →@ tvar:    {tvary}")
        print(f"   →∀ kvant.:  {kvant}")
        print(f"   →= odkaz:   {odkaz}")
        print(f"   BEZ TAHU:   {ztraceno}")
        print(f"   zápis:      {result.statement_id}")
    return ma, nema


def _prijata_odpoved_bez_ucinku(oracle: UDPipeOracle) -> None:
    """Tah, který se PŘIJME a NIC NEZMĚNÍ — to je ta horší půlka."""
    text = ODSTAVEC[1]
    session = Session(lexicon=golden.golden_lexicon())
    pred = session.utter(text, oracle).predication
    after = session.play(
        names_role("Podmět.", oracle.parse(text).readings[0], "nsubj>conj+Nom", "kdo")
    )
    print("\n" + "=" * 72)
    print("TAH, KTERÝ SE PŘIJME A NIC NEZMĚNÍ")
    print("=" * 72)
    print(f"   před:  {pred}")
    print(f"   po:    {after.predication}")
    print(f"   hlásí: {after.lines[0].strip()}")


def _cela_prvni_veta(oracle: UDPipeOracle) -> None:
    """Věta, na jejíž KAŽDOU otázku se odpoví — a stejně se nezapíše."""
    text = ODSTAVEC[0]
    session = Session(lexicon=golden.golden_lexicon())
    session.utter(text, oracle)
    reading = oracle.parse(text).readings[0]
    session.play(names_role("Kdy.", reading, "v+Loc/rok", "kdy"))
    named = session.play(names_role("Komu.", reading, "Dat", "komu"))
    role = next(r for r in named.predication.roles if r.name == "komu")
    final = session.play(
        answers_quantifier("Konkrétnímu.", named.predication, role.pending, Operation.SELF)
    )
    print("\n" + "=" * 72)
    print("PRVNÍ VĚTA S ODPOVĚDÍ NA VŠECHNO")
    print("=" * 72)
    for line in final.lines:
        print(f"   {line}")


def main() -> int:
    oracle = UDPipeOracle()
    print("=" * 72)
    print(f"ODSTAVEC PŘEMĚŘENÝ — {len(ODSTAVEC)} DOSLOVNÝCH VĚT, jedno sezení")
    print("=" * 72)
    ma, nema = _tahy(oracle)
    _prijata_odpoved_bez_ucinku(oracle)
    _cela_prvni_veta(oracle)
    print("\n" + "=" * 72)
    print(f"OTÁZEK, KTERÉ TAH MAJÍ:  {ma}   (v #105 to bylo 7)")
    print(f"OTÁZEK BEZ TAHU:         {nema}   (v #105 to bylo 6)")
    print(
        "\nA TO ČÍSLO POŘÁD NENÍ NULA, takže doména se NEPÍŠE — a i kdyby\n"
        "nula bylo, nestačí to: první věta projde na „✓ přečteno“ a skončí\n"
        "na „zakotvení neproběhlo“, protože `si` dostane za uzel „se“.\n"
        "Doména, kde je `writes` všude prázdné, nedokládá nic."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
