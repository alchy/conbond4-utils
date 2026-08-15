#!/usr/bin/env python
"""Dva běhy nad týmž korpusem — co se změnilo a PROČ.

    python nalezy/diff_behu.py starý.json nový.json
    python nalezy/diff_behu.py starý.json nový.json --vety

Krok 6 zadání v malém. Celkové procento tady nestačí a je to hlavní
věc, kterou tenhle skript hlídá: běh, kde se deset vět nově zapsalo
a deset jiných přestalo zapisovat, vypadá v součtu jako **beze změny**.

Proto se porovnává **po větách** a odděleně:

    nově zapsané          přibyla znalost
    přestalo se zapisovat REGRESE, nebo vědomé zpřísnění — a musí být
                          poznat které, takže se vypisuje důvod
    nově přečtené         ubylo NEPŘEČTENO
    nově nepřečtené       regrese ve čtení
    otázky                seznamem, ne počtem: „ubyla jedna a přibyla
                          jiná" je v součtu neviditelné

Věty se párují **textem**, ne pořadím. Pořadí je přesně ta identita,
na které se zlatá sada conBondu2 už jednou rozbila.
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def nacti(cesta: Path) -> tuple[dict, dict]:
    zaznam = json.loads(cesta.read_text(encoding="utf-8"))
    vety = {
        veta["text"]: veta
        for dokument in zaznam.get("documents", [])
        for veta in dokument["sentences"]
    }
    return zaznam, vety


def hlavicka(jmeno: str, zaznam: dict) -> None:
    print(f"{jmeno}")
    for klic in ("korpus", "oracle", "core", "core_na_konci", "utils"):
        if zaznam.get(klic):
            print(f"   {klic:14} {zaznam[klic]}")


def main() -> None:
    argy = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(argy) != 2:
        raise SystemExit(__doc__)
    stary_zaznam, stare = nacti(Path(argy[0]))
    novy_zaznam, nove = nacti(Path(argy[1]))
    hlavicka(f"STARÝ  {Path(argy[0]).name}", stary_zaznam)
    hlavicka(f"NOVÝ   {Path(argy[1]).name}", novy_zaznam)

    spolecne = sorted(set(stare) & set(nove))
    print(f"\nvět: starý {len(stare)} · nový {len(nove)} · společných {len(spolecne)}")
    jen_stare = len(stare) - len(spolecne)
    jen_nove = len(nove) - len(spolecne)
    if jen_stare or jen_nove:
        # Rozdílná množina vět znamená, že se změnil VSTUP, ne systém —
        # a pak se stavy porovnávat nesmějí, aniž se to řekne.
        print(f"  POZOR: jen ve starém {jen_stare} · jen v novém {jen_nove}"
              f" — porovnávají se jen společné")

    prechody: Counter[tuple[str, str]] = Counter()
    for text in spolecne:
        prechody[(stare[text]["verdict"], nove[text]["verdict"])] += 1

    print("\nPŘECHODY STAVŮ")
    for (byl, je), kolik in sorted(prechody.items(), key=lambda x: -x[1]):
        znak = " " if byl == je else "→"
        print(f"  {znak} {byl:12} → {je:12} {kolik:5}")

    def vypis(nadpis: str, dvojice, ukaz_duvod: bool = True) -> None:
        if not dvojice:
            return
        print(f"\n{nadpis}   ({len(dvojice)})")
        limit = len(dvojice) if "--vety" in sys.argv else 8
        for text in dvojice[:limit]:
            print(f"  » {text[:96]}")
            if ukaz_duvod:
                duvod = nove[text].get("reason") or nove[text].get("reading") or ""
                print(f"      {duvod[:150]}")
        if limit < len(dvojice):
            print(f"  … a dalších {len(dvojice) - limit} (--vety je vypíše)")

    vypis(
        "PŘESTALO SE ZAPISOVAT — regrese, nebo vědomé zpřísnění?",
        [t for t in spolecne
         if stare[t]["verdict"] == "ZAPSÁNO" and nove[t]["verdict"] != "ZAPSÁNO"],
    )
    vypis(
        "NOVĚ ZAPSANÉ",
        [t for t in spolecne
         if stare[t]["verdict"] != "ZAPSÁNO" and nove[t]["verdict"] == "ZAPSÁNO"],
    )
    vypis(
        "NOVĚ NEPŘEČTENÉ — regrese ve čtení",
        [t for t in spolecne
         if stare[t]["verdict"] != "NEPŘEČTENO" and nove[t]["verdict"] == "NEPŘEČTENO"],
    )
    vypis(
        "PŘESTALO BÝT NEPŘEČTENÉ",
        [t for t in spolecne
         if stare[t]["verdict"] == "NEPŘEČTENO" and nove[t]["verdict"] != "NEPŘEČTENO"],
        ukaz_duvod=False,
    )

    # OTÁZKY SEZNAMEM. Součet by schoval výměnu jedné otázky za jinou.
    ma_stary = any(stare[t].get("questions") for t in spolecne)
    ma_novy = any(nove[t].get("questions") for t in spolecne)
    if not (ma_stary and ma_novy):
        # Chybějící pole NENÍ „ubylo nula otázek". Záznam z doby před
        # zavedením seznamu otázek se v téhle ose porovnat nedá a tvrdit
        # opak by znamenalo vyrobit rozdíl z vlastní změny formátu.
        print("\nOTÁZKY — nelze porovnat:"
              f" seznam otázek nese {'jen nový' if ma_novy else 'jen starý'} záznam")
        return
    pribylo: Counter[str] = Counter()
    ubylo: Counter[str] = Counter()
    for text in spolecne:
        a = set(stare[text].get("questions") or [])
        b = set(nove[text].get("questions") or [])
        for q in b - a:
            pribylo[q.split(" (")[0]] += 1
        for q in a - b:
            ubylo[q.split(" (")[0]] += 1
    if pribylo or ubylo:
        print("\nOTÁZKY — podle druhu, ne počtem")
        for jmeno, tabulka in (("ubylo", ubylo), ("přibylo", pribylo)):
            print(f"  {jmeno}:")
            for otazka, kolik in tabulka.most_common(8):
                print(f"    {kolik:5}  {otazka[:100]}")


if __name__ == "__main__":
    main()
