#!/usr/bin/env python
"""Kvantifikátor naučený jako TVAR — dvě měření *(W‑102, kolo #162)*.

    python nalezy/kvantifikator_tvarem.py

Reviewer našel touž nepravdu jako B‑31, jen druhou cestou: „Od Velkého
třesku se **vesmír** rozšířil…" dá `∀vesmír` a po `subset(paralelní
vesmír, vesmír)` odpoví systém na „Rozšířil se paralelní vesmír?" ANO.
Rozhodl to naučený tvar `NOUN/Sing/Nom/nsubj → ∀`.

Sonda měří dvě věci, které si vyžádal, a **oběma lexikony**:

  (a) které tvary nesou kvantifikátor a jak často — a vypíše vzorek
      nejčastějšího `∀`, aby se dalo posoudit, jestli je to jeden tvar,
      nebo rodina;
  (b) na čem stojí počet zapsaných vět: s naučenými tvary, bez `∀`
      tvarů podmětu, a bez naučených tvarů vůbec.

**Rozdělení vzorku na generické a určité je ÚSUDEK, ne měření** — a to
je právě ta odpověď: generické × určité není vlastnost TVARU.
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

from core_semantics.ast import Quantifier  # noqa: E402
from core_semantics.lexicon import (  # noqa: E402
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
from core_semantics.tests import golden  # noqa: E402


def _bez_forall() -> Lexicon:
    """Golden lexikon BEZ `∀` tvarů podmětu; ostatní zůstávají."""
    lexicon = czech_seed()
    for upos, number, case, deprel, operation in golden._SHAPES:
        if operation is Operation.FOR_ALL:
            continue
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case,
                    deprel=deprel,
                ),
                operation=operation,
                learned_from="sonda W-102",
                status=PatternStatus.CONFIRMED,
            )
        )
    return lexicon


def main() -> int:
    vety: list[str] = []
    for cesta in sorted(
        _KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        data = json.loads(cesta.read_text(encoding="utf-8"))
        if "topics" not in data:
            continue
        vety = [s["text"] for t in data["topics"] for s in t["sentences"]]
        break
    if not vety:
        print("v mereni/ není záznam s poli topics/sentences")
        return 1

    oracle = UDPipeOracle()

    print("=" * 74)
    print("(b) NA ČEM STOJÍ POČET ZAPSANÝCH")
    print("=" * 74)
    for jmeno, lexikon in (
        ("golden_lexicon", golden.golden_lexicon),
        ("bez `∀` tvarů podmětu", _bez_forall),
        ("czech_seed (bez naučených)", czech_seed),
    ):
        zapsano = ptalo_se = 0
        for text in vety:
            session = Session(lexicon=lexikon())
            try:
                result = session.utter(text, oracle)
            except Exception:  # pragma: no cover — měřicí sonda
                continue
            if result.predication is None:
                continue
            if result.statement_id is not None:
                zapsano += 1
            if any(
                role.pending is not None and role.quantifier is None
                for role in result.predication.roles
            ):
                ptalo_se += 1
        print(f"   {jmeno:28} ZAPSÁNO {zapsano:3} · ptá se na kvantifikátor "
              f"u {ptalo_se} vět")

    tvar: collections.Counter[str] = collections.Counter()
    vzorek: list[str] = []
    for text in vety:
        session = Session(lexicon=golden.golden_lexicon())
        try:
            result = session.utter(text, oracle)
        except Exception:  # pragma: no cover — měřicí sonda
            continue
        predication = result.predication
        if predication is None:
            continue
        for role in predication.roles:
            if role.quantifier is None or role.pending is not None:
                continue
            mention = role.mention
            feats = dict(mention.feats)
            klic = (
                f"{mention.upos}/{feats.get('Number', '')}/"
                f"{feats.get('Case', '')}/{role.name} → {role.quantifier.value}"
            )
            tvar[klic] += 1
            if (
                role.quantifier is Quantifier.FOR_ALL
                and mention.upos == "NOUN"
                and feats.get("Number") == "Sing"
                and feats.get("Case") == "Nom"
                and len(vzorek) < 22
            ):
                vzorek.append(f"∀{mention.lemma:22} {text[:60]}")

    print("\n" + "=" * 74)
    print("(a) TVARY, KTERÉ NESOU KVANTIFIKÁTOR")
    print("=" * 74)
    for klic, kolik in tvar.most_common(8):
        print(f"   {kolik:4}  {klic}")
    print("\nVZOREK NEJČASTĚJŠÍHO `∀` TVARU — posoudit, ne spočítat:")
    for radek in vzorek:
        print(f"   {radek}")
    print(
        "\nGenerické × určité není vlastnost TVARU, je to vlastnost VĚTY —\n"
        "táž lekce jako u genitivu (W‑39) a u `v+Loc` (§ 12/1)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
