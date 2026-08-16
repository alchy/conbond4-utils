#!/usr/bin/env python
"""Tři rodiny vedle sebe — a kde je hmota doopravdy *(měření kola #159)*.

    python nalezy/tri_rodiny.py

Zadání znělo změřit tři rodiny a přijít s porovnáním, ne se stavbou.
Měří se podle pravidla z #150: **ne z rozboru, ale z toho, co s nimi
systém dnes dělá.**

Výsledek: dosažitelné (hlava JE ve čtení) je u všech tří dohromady
SEDM. Společná příčina je táž — hlava MIMO čtení, což je přes celý
korpus 619 ztrát ze 735.

Doporučení je proto ŘETĚZ PŘÍVLASTKŮ (95 ztrát v 59 větách): mechanismus
je hotový (W‑84, W‑92, W‑98), rozhodnutí o významu už padlo a je to
čtení, takže nová možnost nepravdy nevzniká.
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

from core_semantics.cascade import (  # noqa: E402
    _reported_lost,
    _token_at,
    base_deprel,
)
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
from core_semantics.tests import golden  # noqa: E402

#: Rodiny ze zadání. Klíč je deprel, hodnota jméno, kterým se o ní mluví.
RODINY: dict[str, str] = {
    "advcl:pred": "doplněk přísudku",
    "advcl": "určuje děj",
    "acl:relcl": "vztažná klauze",
}


def main() -> int:
    # Záznam se hledá podle TVARU, ne podle času: ve složce `mereni/` leží
    # i soubory jiných běhů a nejnovější nemusí být ten s korpusem.
    vety: list[str] = []
    for cesta in sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        data = json.loads(cesta.read_text(encoding="utf-8"))
        if "topics" not in data:
            continue
        vety = [s["text"] for t in data["topics"] for s in t["sentences"]]
        break
    if not vety:
        print("v mereni/ není záznam s poli topics/sentences")
        return 1

    oracle = UDPipeOracle()
    stav: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    vrchol: collections.Counter[str] = collections.Counter()
    pod_privlastkem = 0
    vet_pod_privlastkem: set[str] = set()
    ztrat = mimo = 0

    for text in vety:
        session = Session(lexicon=golden.golden_lexicon())
        try:
            result = session.utter(text, oracle)
            reading = oracle.parse(text).readings[0]
        except Exception:  # pragma: no cover — měřicí sonda
            continue
        predication = result.predication
        if predication is None:
            continue

        ve_cteni = {r.mention.token_index for r in predication.roles}
        for role in predication.roles:
            ve_cteni.update(role.absorbed)
        ztraty = list(_reported_lost(reading, predication))
        doplnky = {polozka[2] for polozka in predication.pending_attribute}

        for token in reading.tokens:
            deprel = (
                token.deprel if token.deprel in RODINY
                else base_deprel(token.deprel)
            )
            if deprel not in RODINY:
                continue
            rodina = RODINY[deprel]
            if (
                predication.second is not None
                and predication.second.predicate == token.lemma
            ):
                stav[rodina]["už obslouženo (druhá predikace)"] += 1
            elif any(
                r.mention.token_index == token.index for r in predication.roles
            ):
                stav[rodina]["už obslouženo (je rolí)"] += 1
            elif any(z.index == token.index for z in ztraty):
                stav[rodina][
                    "ZTRÁTA, hlava JE ve čtení" if token.head in ve_cteni
                    else "ZTRÁTA, hlava MIMO čtení"
                ] += 1
            else:
                stav[rodina]["jinak (pohlceno/hluboko)"] += 1

        for token in ztraty:
            ztrat += 1
            if token.head in doplnky:
                pod_privlastkem += 1
                vet_pod_privlastkem.add(text)
            if token.head in ve_cteni:
                continue
            mimo += 1
            # VRCHOL ŘETĚZU: nejvyšší člen, který sám ve čtení není.
            aktualni = token
            nejvyssi = None
            while aktualni is not None and aktualni.head != 0:
                hlava = _token_at(aktualni.head, reading)
                if hlava is None or hlava.index in ve_cteni:
                    break
                nejvyssi = hlava
                aktualni = hlava
            if nejvyssi is not None:
                vrchol[f"{nejvyssi.deprel} ({nejvyssi.upos})"] += 1

    print("=" * 74)
    print("TŘI RODINY PODLE TOHO, CO S NIMI SYSTÉM DNES DĚLÁ")
    print("=" * 74)
    for rodina in RODINY.values():
        print(f"\n  {rodina} — celkem {sum(stav[rodina].values())}")
        for stavek, kolik in stav[rodina].most_common():
            print(f"     {kolik:4}  {stavek}")

    print("\n" + "=" * 74)
    print(f"VŠECH HLÁŠENÝCH ZTRÁT {ztrat} · z toho HLAVA MIMO ČTENÍ {mimo}")
    print("=" * 74)
    print("\nCO STOJÍ NA VRCHOLU ŘETĚZŮ:")
    for kdo, kolik in vrchol.most_common(8):
        print(f"   {kolik:4}  {kdo}")
    print(
        f"\nZTRÁTY POD DOPLŇKEM PŘÍVLASTKU: {pod_privlastkem} "
        f"ve {len(vet_pod_privlastkem)} větách — tohle je doporučená rodina,"
        "\nprotože mechanismus je hotový (W‑84, W‑92, W‑98) a je to ČTENÍ."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
