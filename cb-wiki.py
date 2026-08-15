#!/usr/bin/env python
"""Téma z Wikipedie → věty → KDE PŘESNĚ conBond4 uvázl.

    python cb-wiki.py "Karel Čapek" --vet 40
    python cb-wiki.py --temata-souboru          # sada z temata.txt
    python cb-wiki.py --json mereni/2026-08-15.json

Není to ETL, které by vyrábělo data pro conBond4. Je to **měřicí hranice
mezi přirozeným jazykem a formálním jádrem**: co se dnes bezpečně
přečte, co si systém právem vyžádá dialogem, co vědomě odmítne a co ho
překvapí. Pět stavů se **nikdy neslévá do jednoho skóre** — každý
znamená jinou věc a vede k jiné opravě.

Samotné číslo `ZAPSÁNO` nic nedokazuje. Zvednout ho z 0 na 20 % jde
i tak, že se korpus osekne na jednoduché věty. Co se řídit dá, je
**rozklad po jazykových třídách**: která konstrukce se nově čte
bezpečně, která pořád potřebuje dialog, která je odmítnutá a která
padá. Proto je hlavní výstup tabulka vrstev, ne součet.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cb_utils.revize import revision
from cb_utils.triage import CONBOND4, Result, Verdict, sentences_of, triage
from cb_utils.wiki import fetch, paragraphs

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
TOPICS = HERE / "temata.txt"


def _topics(explicit: list[str]) -> list[str]:
    if explicit:
        return explicit
    if not TOPICS.exists():
        raise SystemExit(f"chybí {TOPICS} — seznam témat, jedno na řádek")
    return [
        line.strip()
        for line in TOPICS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _table(results: list[Result], title: str) -> None:
    """Rozklad po vrstvách. `sám` = kolik vět uvázlo JEN na téhle věci."""
    total = len(results)
    if not total:
        return
    hit: Counter[str] = Counter()
    sole: Counter[str] = Counter()
    kinds: Counter[tuple[str, str]] = Counter()
    for result in results:
        for layer in result.layers:
            hit[layer] += 1
        if result.sole:
            sole[result.sole] += 1
            if result.kind:
                kinds[(result.sole, result.kind)] += 1
    print(f"\n{title}   (vět {total})")
    print(f"  {'vrstva':16} {'vyskytuje se':>13} {'sám blokuje':>12}")
    for layer, count in hit.most_common():
        share = 100.0 * count / total
        alone = sole.get(layer, 0)
        alone_share = 100.0 * alone / total
        print(
            f"  {layer:16} {count:5} ({share:4.1f} %) {alone:5} ({alone_share:4.1f} %)"
        )
        # Druh UVNITŘ vrstvy. Bez něj splyne „shoda opravdu neplatí"
        # s „rys má dvě hodnoty a porovnává se jako řetězec" — a to
        # jsou dvě různé opravy v jádře, ne jedno číslo.
        for (name, kind), how_many in sorted(kinds.items()):
            if name == layer:
                print(f"  {'':16} {'':13} {how_many:5}  · {kind}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tema", nargs="*", help="název článku na cs.wikipedia")
    parser.add_argument("--vet", type=int, default=30, help="kolik vět na téma")
    parser.add_argument("--ulozit", action="store_true", help="text do data/")
    parser.add_argument("--stav", default="", help="vypsat jen tenhle stav")
    parser.add_argument("--sam", default="", help="jen věty blokované touhle vrstvou")
    parser.add_argument("--json", default="", help="záznam měření do souboru")
    parser.add_argument("--tise", action="store_true", help="jen tabulky")
    args = parser.parse_args()

    from core_semantics.oracle import UDPipeOracle

    oracle = UDPipeOracle()
    print(f"orákulum: {oracle.provenance}\n")

    # IDENTITA BĚHU je trojí: co přišlo na vstup (revize článku), kdo to
    # rozebral (model orákula) a kdo to četl (revize jádra). Bez té třetí
    # vypadá změna jádra jako nestabilní měření — přesně to se stalo mezi
    # prvním a druhým během (viz cb_utils/revize.py).
    record: dict = {
        "oracle": oracle.provenance,
        "core": revision(CONBOND4),
        "utils": revision(HERE),
        "sentences_per_topic": args.vet,
        "topics": [],
    }
    print(f"jádro:    {record['core']}")
    print(f"měření:   {record['utils']}\n")
    everything: list[Result] = []
    total: Counter[str] = Counter()

    for title in _topics(args.tema):
        article = fetch(title)
        if args.ulozit:
            DATA.mkdir(exist_ok=True)
            (DATA / f"{article.title.replace(' ', '_')}.txt").write_text(
                article.text, encoding="utf-8"
            )
        print("=" * 72)
        print(f"{article.title}   ({article.provenance})")
        print("=" * 72)

        seen: list[str] = []
        for block in paragraphs(article):
            for sentence in sentences_of(block, oracle):
                if len(seen) >= args.vet:
                    break
                seen.append(sentence)
            if len(seen) >= args.vet:
                break

        results = [triage(sentence, oracle) for sentence in seen]
        everything.extend(results)
        counts: Counter[str] = Counter(r.verdict.value for r in results)
        total.update(counts)

        # NEJBLIŽ PRVNÍ: podle počtu otevřených věcí, ne podle délky.
        results.sort(key=lambda r: (r.open_questions, len(r.sentence)))
        if not args.tise:
            for result in results:
                if args.stav and result.verdict.value != args.stav:
                    continue
                if args.sam and result.sole != args.sam:
                    continue
                print(result.render())
        print()
        print("  " + " · ".join(f"{k} {v}" for k, v in counts.most_common()))
        _table(results, "  rozklad")
        print()

        record["topics"].append(
            {
                "title": article.title,
                "provenance": article.provenance,
                "sentences": [
                    {
                        "text": r.sentence,
                        "verdict": r.verdict.value,
                        "open_questions": r.open_questions,
                        "layers": list(r.layers),
                        "sole": r.sole,
                        "kind": r.kind,
                        "questions": list(r.questions),
                        "reading": r.reading,
                        "reason": r.detail,
                    }
                    for r in results
                ],
            }
        )

    print("=" * 72)
    print("CELKEM  " + " · ".join(f"{k} {v}" for k, v in total.most_common()))
    _table(everything, "ROZKLAD PŘES VŠECHNA TÉMATA")
    print("=" * 72)

    if args.json:
        target = Path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"\nzáznam: {target}  — reprodukovatelné podle revize v provenienci")


if __name__ == "__main__":
    main()
