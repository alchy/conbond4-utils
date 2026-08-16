#!/usr/bin/env python
"""Doklad, že se v záznamu nic neuřízne — porovnáno se stopou jádra.

    python nalezy/bez_zkraceni.py [záznam.json]

Do kola #3 se `reason` ořezával na 160 znaků. Věta s pěti otevřenými
věcmi tak vyšla ze záznamu jako věta s jednou a půl a nikdo to nemohl
poznat, protože chybějící konec vypadá stejně jako konec.

Tenhle skript vezme ze záznamu **nejdelší** otázku, pustí touž větu
znovu přes jádro a porovná znak po znaku, co jádro řeklo, s tím, co je
v záznamu. Bere nejdelší schválně: kdyby se ještě někde zkracovalo,
projeví se to tam.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cb_utils.triage import triage  # noqa: E402  (nastavuje cestu k jádru)

from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
import core_semantics.tests.golden as golden  # noqa: E402

from cb_utils.zaznamy import vyber  # noqa: E402


def main() -> None:
    cesta = vyber(sys.argv[1:])
    zaznam = json.loads(cesta.read_text(encoding="utf-8"))
    vety = [v for d in zaznam.get("documents", []) for v in d["sentences"]]
    if not vety:
        raise SystemExit(f"{cesta} nemá věty")
    veta = max(vety, key=lambda v: len(v["reason"]))
    print(f"záznam: {cesta.name}")
    print(f"jádro v záznamu: {zaznam.get('core', '?')}\n")
    print(f"věta: {veta['text']}")
    print(f"  reason v záznamu: {len(veta['reason'])} znaků")
    print(f"  otázek v seznamu: {len(veta['questions'])}"
          f" (open_questions {veta['open_questions']})\n")

    oracle = UDPipeOracle()
    session = Session(lexicon=golden.golden_lexicon())
    ziva = session.utter(veta["text"], oracle)
    otazka_jadra = ziva.question or ""

    print("POROVNÁNÍ SE ŽIVOU STOPOU JÁDRA")
    print(f"  jádro teď říká:   {len(otazka_jadra)} znaků")
    shoda = otazka_jadra == veta["reason"]
    print(f"  shoda znak po znaku: {'ANO' if shoda else 'NE'}")
    if not shoda:
        # Rozdíl nemusí být zkrácení — mezi během a kontrolou se mohlo
        # změnit jádro. Ukáže se konec obojího, ať je poznat co je co.
        print(f"    záznam končí: …{veta['reason'][-70:]!r}")
        print(f"    jádro končí:  …{otazka_jadra[-70:]!r}")
        print("    (liší-li se jen obsahem, změnilo se jádro;"
              " je-li záznam KRATŠÍ a je předponou, zkracuje se)")
        print(f"    je záznam předponou živé otázky?"
              f" {otazka_jadra.startswith(veta['reason'])}")

    znovu = triage(veta["text"], oracle)
    print("\nTÝŽ PRŮCHOD MĚŘICÍ VRSTVOU")
    print(f"  stav {znovu.verdict.value} · otázek {len(znovu.questions)}"
          f" · reason {len(znovu.detail)} znaků")
    for q in znovu.questions:
        print(f"   ? {q}")


if __name__ == "__main__":
    main()
