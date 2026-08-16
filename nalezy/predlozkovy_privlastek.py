#!/usr/bin/env python
"""Předložkový přívlastek jména — CO BY ZRCADLO W‑39 STÁLO *(kolo #146)*.

    python nalezy/predlozkovy_privlastek.py

Zadání kola znělo POSTAVIT. Zrcadlo je šest řádků v `genitive_attributes`
(přijmout `nmod`, které má dítě s `deprel=case`, a do dvojice psát
předložku); postavené bylo a tahle sonda měří, co dělá a co bere.

**POSTAVENO V KOLE #147.** Reviewer rozhodl ve prospěch W‑39 a akceptační
sada I‑16 se překotvila z „Petr má alergii na penicilin." na `advcl+Nom`
(„působil jako vychovatel"), kde ztracený člen účastníkem děje SKUTEČNĚ
je. Tahle sonda tedy měří UŽ POSTAVENÝ stav; čísla dole jsou předpověď
z #146, kterou běh #147 potvrdil přesně.

Kořen je vidět z výpisu níž: rozbor „alergii na penicilin" a „pobytu
v Berlíně" NEROZLIŠÍ. Obojí je `nmod` s `case` pod jménem, které je ve
čtení. Rozdíl je lexikální — `na penicilin` je VAZBA toho jména („lék
na X", „recept na Y"), `v Berlíně` je URČENÍ toho pobytu — a v rozboru
pro něj signál není. Táž hranice jako W‑82, jenže tam ji rozbor značí
(`:arg`).

Čísla z celého korpusu (238 vět, obojí týmž během):

    ZAPSÁNO                8 → 9      (odemčení, jak předpověděl #142)
    vět s [ZAHOZENO: …]  188 → 181
    vět s [PŘÍVLASTEK: …] 82 → 117

Rozsah: 4 zmínky v populaci z #139, 9 v širší populaci reviewera,
50 zmínek ve 48 větách v celém korpusu.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.cascade import (  # noqa: E402
    _reported_lost,
    base_deprel,
    is_bare_genitive,
)
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
from core_semantics.tests import golden  # noqa: E402

#: Patch, který se měřil. Je tady DOSLOVA, aby se dal přiložit k verdiktu
#: bez toho, že by si ho někdo musel odvozovat z popisu.
ZRCADLO = """\
    for token in reading.tokens:
        if token.deprel != "nmod":
            continue
        predlozka = next(
            (c.form for c in reading.children(token.index) if c.upos == "ADP"),
            None,
        )
        if predlozka is None and not is_bare_genitive(token, reading):
            continue
        ...
        najdene.append((ve_cteni[head.index],
                        f"{predlozka} {token.lemma}" if predlozka else token.lemma,
                        token.index))
"""

#: Dvě věty, na kterých je spor vidět celý. Rozbor je u obou TÝŽ.
SPOR: tuple[str, ...] = (
    "Mluvil o pobytu v Berlíně.",
    "Mluvil o pobytu bratra.",
    "Petr má alergii na penicilin.",
)

#: Testy, které zrcadlo shodí. Čtyři poslední jsou ta podstatná půlka.
ROZBIJE: tuple[str, ...] = (
    "test_cascade.py::test_a_prepositional_genitive_is_not_an_attribute",
    "test_cascade.py::test_a_lost_head_is_reported_with_what_was_composed_into_it",
    "test_lost_role.py::test_only_what_is_really_in_the_parse_is_asked_about",
    "test_lost_role.py::test_a_lost_member_is_asked_about_not_just_noted",
    "test_lost_role.py::test_the_answer_completes_the_very_sentence_that_asked",
    "test_lost_role.py::test_one_answer_closes_the_whole_class",
)


def _rozbor(oracle: UDPipeOracle) -> None:
    """Rozbor obou vět vedle sebe — tady je vidět, že signál není."""
    print("=" * 74)
    print("ROZBOR TĚCH DVOU VĚT SE NELIŠÍ")
    print("=" * 74)
    for text in SPOR:
        print(f"\n» {text}")
        session = Session(lexicon=golden.golden_lexicon())
        result = session.utter(text, oracle)
        for token in oracle.parse(text).readings[0].tokens:
            print(f"   {token.index} {token.form:12} {token.upos:6} "
                  f"head={token.head} {token.deprel}")
        for line in result.lines:
            if "PŘÍVLASTEK" in line or "ZAHOZENO" in line:
                print(f"   HLÁSÍ: {line.strip()[:88]}")


def _kolik(oracle: UDPipeOracle) -> None:
    """Kolik zmínek to je v celém korpusu — populace je v hlavičce."""
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    data = json.loads(zaznamy[-1].read_text(encoding="utf-8"))
    vety = [s["text"] for t in data["topics"] for s in t["sentences"]]

    zminek = 0
    vet: set[str] = set()
    ukazky: list[str] = []
    for text in vety:
        session = Session(lexicon=golden.golden_lexicon())
        try:
            result = session.utter(text, oracle)
            reading = oracle.parse(text).readings[0]
        except Exception:  # pragma: no cover — měřicí sonda
            continue
        if result.predication is None:
            continue
        ve_cteni = {r.mention.token_index for r in result.predication.roles}
        podle_indexu = {t.index: t for t in reading.tokens}
        for token in _reported_lost(reading, result.predication):
            if base_deprel(token.deprel) != "nmod" or token.head not in ve_cteni:
                continue
            hlava = podle_indexu[token.head]
            if hlava.upos not in ("NOUN", "PROPN"):
                continue
            if is_bare_genitive(token, reading):
                continue
            predlozky = [
                t.form for t in reading.tokens
                if t.head == token.index and t.upos == "ADP"
            ]
            if not predlozky:
                continue
            zminek += 1
            vet.add(text)
            if len(ukazky) < 8:
                ukazky.append(f"{hlava.form} {predlozky[0]} {token.form}")

    print("\n" + "=" * 74)
    print(f"PŘEDLOŽKOVÝ PŘÍVLASTEK HLÁŠENÝ JAKO ZTRACENÝ ČLEN: "
          f"{zminek} zmínek ve {len(vet)} větách")
    print("=" * 74)
    for ukazka in ukazky:
        print(f"   · {ukazka}")


def main() -> int:
    oracle = UDPipeOracle()
    _rozbor(oracle)
    _kolik(oracle)
    print("\n" + "=" * 74)
    print("MĚŘENÝ PATCH")
    print("=" * 74)
    print(ZRCADLO)
    print("SHODÍ TYHLE TESTY:")
    for test in ROZBIJE:
        print(f"   · {test}")
    print(
        "\nČtyři poslední jsou akceptační sada I‑16 na větě „Petr má alergii\n"
        "na penicilin." + '"' + " Přepsat je, aby prošla moje změna, jsem si sám\n"
        "nevzal: je to rozhodnutí o VÝZNAMU (co je role věty), ne o kódu.\n"
        "Doporučení je v docs/CORE-SEMANTICS-0.1.md § 12 — rozhodnout ve\n"
        "prospěch W‑39 a ty čtyři testy překotvit na `xcomp>obj+Acc`."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
