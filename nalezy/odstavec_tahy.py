#!/usr/bin/env python
"""Kolik tahů stojí přečíst SKUTEČNÝ ODSTAVEC *(zadání kola #105)*.

    python nalezy/odstavec_tahy.py

Reviewer chtěl číslo DŘÍV, než z toho vznikne dvacátá druhá doména.
Odstavec jsou ČTYŘI DOSLOVNÉ VĚTY z měřeného korpusu, v pořadí, bez úprav.

**Výsledek není číslo, je to NE.** Ten odstavec se dnes přečíst do konce
NEDÁ, a to ze tří důvodů, které se sčítají:

  1 · NĚKTERÉ OTÁZKY NEMAJÍ TAH. „1938" visí jako `nummod` uvnitř
      časového údaje a „musel"/„ulehnout" jsou SOUŘADNÝ DRUHÝ PŘÍSUDEK —
      pojmenovat je rolí by znamenalo tvrdit, že jsou členy té věty.

  2 · JEDNA OTÁZKA ODMÍTÁ VLASTNÍ ODPOVĚĎ. U „si" se systém ptá „Na koho
      odkazuje? Řekni to prosím jménem", ale role `komu` čeká na
      KVANTIFIKÁTOR — `decides_reference` proto odpoví „role na odkaz
      nečeká". Otázka a stav se rozešly.

  3 · ODSTAVEC SE NEROZBĚHNE SÁM. Poslední věta nemá vyslovený podmět
      a v souvislém sezení pro něj NENÍ KANDIDÁT — předchozí věty se
      totiž nezapsaly (všechny visí na nepojmenovaných rolích), takže
      v kontextu textu nic neleží.

**Doména se proto nepíše.** Každý krok v ní má být odpovědí na otázku,
kterou systém sám položil; kroky, které tam jsou „aby to vyšlo", by z ní
udělaly zkoušku napsanou podle výsledku.
"""

from __future__ import annotations

import sys
from pathlib import Path

_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
from core_semantics.cascade import (  # noqa: E402
    AWAITING_QUANTIFIER,
    AWAITING_REFERENCE,
    surface_roles,
)
from core_semantics.tests import golden  # noqa: E402

#: Čtyři DOSLOVNÉ věty z korpusu, v pořadí. Opsané, ne vybrané podle
#: toho, co projde — to je celý smysl téhle sondy.
ODSTAVEC: tuple[str, ...] = (
    "V prosinci 1938 si Karel Čapek přivodil lehkou chřipku.",
    "Ke chřipce se přidal zánět ledvin a zápal plic.",
    "Jeho stav se přechodně zlepšil, ale brzy musel znovu ulehnout.",
    "Byl pohřben na Vyšehradském hřbitově v Praze.",
)


def main() -> int:
    oracle = UDPipeOracle()
    session = Session(lexicon=golden.golden_lexicon())

    print("=" * 72)
    print(f"ODSTAVEC — {len(ODSTAVEC)} DOSLOVNÝCH VĚT, jedno sezení")
    print("=" * 72)

    tahy_dostupne = 0
    tahy_chybi = 0
    for text in ODSTAVEC:
        result = session.utter(text, oracle)
        predication = result.predication
        print(f"\n» {text}")
        if predication is None:
            print("   NEPŘEČTENO")
            continue
        role_tvar = list(surface_roles(predication))
        kvantifikator = [
            r.name for r in predication.roles if r.awaiting == AWAITING_QUANTIFIER
        ]
        odkaz = [
            r.name for r in predication.roles if r.awaiting == AWAITING_REFERENCE
        ]
        ztracene = list(result.turn.lost)
        tahy_dostupne += len(role_tvar) + len(kvantifikator) + len(odkaz)
        tahy_chybi += len(ztracene)
        print(f"   →@ tvar bez významu: {role_tvar}")
        print(f"   →∀ čeká na kvantifikátor: {kvantifikator}")
        print(f"   →= čeká na odkaz: {odkaz}")
        print(f"   BEZ TAHU — ztracené členy: {[f for f, _ in ztracene]}")
        print(f"   zapsáno: {result.statement_id}")

    print("\n" + "=" * 72)
    print(
        f"TAHŮ, KTERÉ MAJÍ ODPOVĚĎ: {tahy_dostupne} (plus {len(ODSTAVEC)} vět)\n"
        f"OTÁZEK BEZ TAHU:          {tahy_chybi}\n"
    )
    print(
        "A TO ČÍSLO NENÍ ODPOVĚĎ. Odstavec se do konce přečíst NEDÁ:\n"
        "  · některé otázky tah nemají (číslovka v časovém údaji,\n"
        "    souřadný druhý přísudek);\n"
        "  · jedna otázka ODMÍTÁ VLASTNÍ ODPOVĚĎ — u „si“ se ptá na\n"
        "    ODKAZ, ale role čeká na KVANTIFIKÁTOR;\n"
        "  · odstavec se nerozběhne sám: nic se nezapsalo, takže poslední\n"
        "    věta nemá pro svůj vynechaný podmět v kontextu kandidáta."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
