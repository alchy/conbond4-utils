#!/usr/bin/env python
"""Protipříklad k N‑10: ptá se jádro → seznam otázek není prázdný.

    python nalezy/otazka_neni_nula.py [záznam.json]
    python nalezy/otazka_neni_nula.py --simulace [záznam.json]

Zadání Revieweru znělo **protipříklad, ne součet**: projít všechny věty,
kde se jádro ptá, a ukázat, že ani jedna nemá prázdný seznam — a naopak
ukázat, že věta, kde jádro mlčí, prázdný seznam **má**. Bez té druhé
poloviny by šlo vadu jen otočit na druhou stranu a nazvat to opravou.

Kontroluje se obojí a **z jednoho zdroje**: z toho, co jádro řeklo.

    ptá se       = v otázce jádra je otazník
    mlčí         = otázka je prázdná, nebo v ní otazník není
                   („Tuhle větu přečíst neumím: …" je vysvětlení)

`--simulace` spustí nové pravidlo nad **starým** záznamem, aby šlo
odhadnout dopad dřív, než se přeměří. Předpověď a měření se pak dají
porovnat — a když se rozejdou, je to nález, ne detail.
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cb_utils.triage import open_items  # noqa: E402

from cb_utils.zaznamy import vyber  # noqa: E402


def vety_zaznamu(zaznam: dict) -> list[dict]:
    return [v for d in zaznam.get("documents", []) for v in d["sentences"]]


def pta_se(veta: dict) -> bool:
    """Ptá se jádro? Rozhoduje **otazník v otázce jádra**, ne stav."""
    return "?" in (veta.get("question") or "")


def kontrola(vety: list[dict], klic: str) -> int:
    """Obě poloviny protipříkladu. Vrací počet porušení."""
    ptaji = [v for v in vety if pta_se(v)]
    mlci = [v for v in vety if not pta_se(v)]
    prazdne_pri_otazce = [v for v in ptaji if not v.get(klic)]
    plne_pri_mlceni = [v for v in mlci if v.get(klic)]

    print(f"\n  vět celkem            {len(vety):5}")
    print(f"  jádro se ptá          {len(ptaji):5}")
    print(f"  jádro mlčí            {len(mlci):5}")
    print(f"  ✗ ptá se, seznam prázdný      {len(prazdne_pri_otazce):5}"
          f"   (musí být 0)")
    print(f"  ✗ mlčí, seznam neprázdný      {len(plne_pri_mlceni):5}"
          f"   (musí být 0)")
    for veta in prazdne_pri_otazce[:5]:
        print(f"      » {veta['text'][:80]}")
        print(f"        otázka: {(veta.get('question') or '')[:110]}")
    for veta in plne_pri_mlceni[:5]:
        print(f"      » {veta['text'][:80]}")
        print(f"        seznam: {veta[klic][0][:110]}")
    return len(prazdne_pri_otazce) + len(plne_pri_mlceni)


def simulace(vety: list[dict]) -> None:
    """Nové pravidlo nad starým záznamem — předpověď před přeměřením."""
    stary_soucet = sum(v.get("open_questions", 0) for v in vety)
    novy_soucet = 0
    prazdne = 0
    druhy: Counter[str] = Counter()
    for veta in vety:
        nove = open_items((), veta.get("question") or "")
        novy_soucet += len(nove)
        if pta_se(veta) and not nove:
            prazdne += 1
        for polozka in nove:
            druhy[polozka.split(":", 1)[0]] += 1
    print("\nSIMULACE NOVÉHO PRAVIDLA NAD STARÝM ZÁZNAMEM")
    print(f"  součet otevřených věcí  starý {stary_soucet:5}"
          f"  →  nový {novy_soucet:5}"
          f"   ({novy_soucet - stary_soucet:+})")
    print(f"  vět, kde se ptá a seznam by byl prázdný: {prazdne}")
    print("  podle druhu:")
    for druh, kolik in druhy.most_common():
        print(f"    {kolik:5}  {druh}")


def main() -> None:
    cesta = vyber(sys.argv[1:])
    zaznam = json.loads(cesta.read_text(encoding="utf-8"))
    vety = vety_zaznamu(zaznam)
    print(f"záznam: {cesta.name}")
    print(f"jádro:  {zaznam.get('core', '?')}")

    if "--simulace" in sys.argv:
        simulace(vety)
        return

    poruseni = kontrola(vety, "questions")
    # Zlatá sada je součást téhož záznamu a platí pro ni totéž.
    polozky = zaznam.get("etalon", {}).get("polozky", [])
    if polozky:
        pta = [p for p in polozky if "?" in (p.get("question") or "")]
        print(f"\n  zlatá sada: {len(polozky)} položek,"
              f" jádro se ptá u {len(pta)}")
    print(f"\n  PORUŠENÍ CELKEM: {poruseni}"
          f"   {'— protipříklad drží' if poruseni == 0 else '— NEDRŽÍ'}")
    sys.exit(1 if poruseni else 0)


if __name__ == "__main__":
    main()
