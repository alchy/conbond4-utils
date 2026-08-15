#!/usr/bin/env python
"""Téma z Wikipedie → věty → jak si s nimi conBond4 poradí.

    python cb-wiki.py "Karel Čapek" --vet 40
    python cb-wiki.py --temata            # sada témat z temata.txt
    python cb-wiki.py "Vesmír" --ulozit   # text do data/ (mimo git)

Výstup je přehled po stavech a pak výpis vět. Nic se nikam nezapisuje
do conBondu4 — akceptační doména je rozhodnutí člověka.
"""

from __future__ import annotations

import argparse
import io
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cb_utils.triage import Verdict, sentences_of, triage
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tema", nargs="*", help="název článku na cs.wikipedia")
    parser.add_argument("--vet", type=int, default=30, help="kolik vět na téma")
    parser.add_argument("--ulozit", action="store_true", help="text do data/")
    parser.add_argument("--stav", default="", help="vypsat jen tenhle stav")
    args = parser.parse_args()

    from core_semantics.oracle import UDPipeOracle

    oracle = UDPipeOracle()
    print(f"orákulum: {oracle.provenance}\n")

    total: Counter[str] = Counter()
    for title in _topics(args.tema):
        article = fetch(title)
        if args.ulozit:
            DATA.mkdir(exist_ok=True)
            target = DATA / f"{article.title.replace(' ', '_')}.txt"
            target.write_text(article.text, encoding="utf-8")
        print("=" * 70)
        print(f"{article.title}   ({article.provenance})")
        print("=" * 70)

        seen: list[str] = []
        for block in paragraphs(article):
            for sentence in sentences_of(block, oracle):
                if len(seen) >= args.vet:
                    break
                seen.append(sentence)
            if len(seen) >= args.vet:
                break

        counts: Counter[str] = Counter()
        results = []
        for sentence in seen:
            result = triage(sentence, oracle)
            counts[result.verdict.value] += 1
            total[result.verdict.value] += 1
            results.append(result)

        # NEJBLIŽ PRVNÍ. Řadí se podle toho, na kolik otázek by člověk
        # musel odpovědět — ne podle délky. Věta, která se zapíše sama,
        # je nahoře; encyklopedické souvětí se sedmi nepojmenovanými
        # tvary dole. Je to POŘADÍ, ne výběr: nic se nezahazuje.
        results.sort(key=lambda r: (r.open_questions, len(r.sentence)))
        for result in results:
            if args.stav and result.verdict.value != args.stav:
                continue
            print(result.render())
        print()
        print("  " + " · ".join(f"{k} {v}" for k, v in counts.most_common()))
        print()

    print("=" * 70)
    print("CELKEM  " + " · ".join(f"{k} {v}" for k, v in total.most_common()))
    print("=" * 70)


if __name__ == "__main__":
    main()
