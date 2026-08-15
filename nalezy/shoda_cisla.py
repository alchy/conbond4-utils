#!/usr/bin/env python
"""Reprodukce nálezu: patro shody čísla zahazuje gramatické české věty.

    python nalezy/shoda_cisla.py            # minimální páry, tři třídy
    python nalezy/shoda_cisla.py --korpus   # týž jev na měřeném korpusu

Jedna věta nedokazuje nic. Dokazuje to **minimální pár**: dvě věty téže
stavby, které se liší jedinou věcí — a jedna projde, druhá ne. Když
padne celá třída takových párů a kontrolní skupina projde, není příčina
ve složitosti věty, ale v tom jednom rozdílu.

Třídy, které z korpusu vypadly, jsou tři a **každá potřebuje jinou
opravu**:

  A · dvojhodnotový rys — příčestí na `-la` je tvarově femininum
      singuláru („žena psala") nebo neutrum plurálu („města psala").
      Rozbor to poctivě vrátí jako `Number=Plur,Sing`. Patro porovnává
      hodnotu rysu jako ŘETĚZEC, takže `"Sing" != "Plur,Sing"`, a čtení
      zahodí — přestože jedna z těch dvou hodnot je ta správná.

  B · koordinovaný podmět — „Karel a Josef **byli** bratři." Přísudek je
      v plurálu podle celé koordinace, ale rozbor dává jako `nsubj`
      první člen v singuláru; zbytek visí na něm jako `conj`. Shoda se
      počítá proti jednomu členu místo proti celé skupině.

  C · kvantifikovaný podmět — „Přišlo několik **hostů**." Čeština má
      u počitatelných výrazů přísudek v neutru singuláru a jméno
      v genitivu plurálu. Shoda čísla tu z principu neplatí; požadovat
      ji znamená zahodit každou větu typu „mnoho / několik / pět".

Ticho po nich není bezpečné mlčení: je to **ztráta dobrého vstupu**,
o které se dole neví, protože věta skončí ve stejné škatuli jako věta
opravdu nesrozumitelná.

**Tenhle skript do jádra nesahá a nesmí.** Pošle věty a vypíše, co
jádro samo vrátilo — rysy z rozboru, počet kandidátů a stopu kaskády.
Zařazení do tříd A/B/C dělá měřicí vrstva a dělá ho **z jmenovek
rozboru** (`Number`, `Case`, `conj`), ne z povrchu věty a ne z jádra;
je to popis nálezu, ne druhé čtení. Opravu dělá Builder jádra.
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

from cb_utils.triage import CONBOND4, Verdict  # noqa: E402  (nastavuje sys.path k jádru)

from core_semantics.cascade import _predicate_head, cascade, generate  # noqa: E402
from core_semantics.oracle import Reading, UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402
import core_semantics.tests.golden as golden  # noqa: E402

#: (jméno třídy, věta, která PROJÍT MÁ, věta téže stavby, která padá)
TRIDY: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        "A · dvojhodnotový rys (příčestí -la)",
        (
            ("Petr četl knihu.", "Žena psala dopis."),
            ("Muž nesl kufr.", "Matka sbírala folklor."),
            ("Karel napsal román.", "Povodeň zasáhla dům."),
            ("Pes chytil myš.", "Kočka chytila myš."),
        ),
    ),
    (
        "B · koordinovaný podmět",
        (
            ("Petr četl knihu.", "Petr a Pavel četli knihu."),
            ("Karel byl bratr.", "Karel a Josef byli bratři."),
        ),
    ),
    (
        "C · kvantifikovaný podmět (genitiv množství)",
        (
            ("Přišel host.", "Přišlo několik hostů."),
            ("Existuje teorie.", "Existuje několik teorií."),
            ("Člověk choval psy.", "Mnoho lidí chovalo psy."),
        ),
    ),
)

#: Kontrolní skupina: jednoznačné tvary v singuláru i plurálu. Kdyby
#: padalo i tohle, není příčina v těch třech rozdílech, ale jinde.
KONTROLA: tuple[str, ...] = (
    "Dítě spalo.",
    "Město rostlo.",
    "Psi štěkali.",
)


def zjisti(oracle: UDPipeOracle, veta: str) -> dict:
    """Co jádro o větě samo řekne. Nic se nedopočítává."""
    utterance = oracle.parse(veta)
    if not utterance.readings:
        return {"veta": veta, "chyba": "orákulum nevrátilo čtení", "stopa": []}
    reading = utterance.readings[0]
    head = _predicate_head(reading)
    verdict = cascade(
        reading, tiers=Session(lexicon=golden.golden_lexicon()).tiers()
    )
    return {
        "veta": veta,
        "reading": reading,
        "přísudek": head[0].form if head else "",
        "Number": (head[0].feat("Number") if head else "") or "",
        "kandidátů": len(generate(reading)),
        "zbylo": len(verdict.survivors),
        "rozhodnuto": verdict.decided is not None,
        "stopa": list(verdict.trace),
    }


def trida(reading: Reading, number: str) -> str:
    """Do které třídy případ patří — podle JMENOVEK ROZBORU.

    Pořadí je záměrné: dvojhodnotový rys se pozná na přísudku a je to
    vada porovnání, kdežto B a C jsou chybějící schopnosti. Kdyby se
    slily, vypadalo by to jako jedna oprava a jsou to tři.

    Podmět se bere jako **potomek přísudku**, ne první `nsubj` ve větě.
    Tuhle chybu udělal už conBond2 (`baseline.py`, „podmět KOŘENE, ne
    libovolný podmět"): souvětí má skoro vždy vedlejší větu s vlastním
    podmětem, takže první `nsubj` je často z jiné klauzule — a zařazení
    pak měří skladbu souvětí, ne příčinu pádu.
    """
    if "," in number:
        return "A dvojhodnotový rys"
    head = _predicate_head(reading)
    if head is None:
        return "jiné"
    anchor = head[1]
    subjects = [
        t
        for t in reading.tokens
        if t.head == anchor.index and t.deprel.startswith("nsubj")
    ]
    if not subjects:
        return "jiné"
    subject = subjects[0]
    if any(t.head == subject.index and t.deprel == "conj" for t in reading.tokens):
        return "B koordinovaný podmět"
    if len(subjects) > 1:
        return "B koordinovaný podmět"
    if subject.feat("Case") == "Gen":
        return "C kvantifikovaný podmět"
    return "jiné"


def minimalni_pary(oracle: UDPipeOracle) -> tuple[int, int]:
    padlo = spatne = 0
    for jmeno, pary in TRIDY:
        print(f"\n{jmeno}\n")
        for prochazi, pada in pary:
            for veta in (prochazi, pada):
                r = zjisti(oracle, veta)
                znak = "✓" if r.get("rozhodnuto") else "✗"
                print(f"  {znak} {veta:30} Number={r['Number']:11}"
                      f" kandidátů {r['kandidátů']} → zbylo {r['zbylo']}")
                for step in r["stopa"]:
                    if "PROČ" in step:
                        print(f"        {step}")
            r_pada = zjisti(oracle, pada)
            r_prochazi = zjisti(oracle, prochazi)
            if not r_pada["rozhodnuto"]:
                padlo += 1
            if not r_prochazi["rozhodnuto"]:
                spatne += 1
            print()
    print("KONTROLA — jednoznačné tvary mají projít\n")
    for veta in KONTROLA:
        r = zjisti(oracle, veta)
        znak = "✓" if r.get("rozhodnuto") else "✗"
        print(f"  {znak} {veta:30} Number={r['Number']:11}"
              f" kandidátů {r['kandidátů']} → zbylo {r['zbylo']}")
        if not r["rozhodnuto"]:
            spatne += 1
    return padlo, spatne


def korpus(oracle: UDPipeOracle) -> None:
    """Týž jev na tom, co se opravdu měřilo — ne na vymyšlených větách.

    Bere poslední záznam z `mereni/`, projde věty, které skončily jako
    NEPŘEČTENO na shodě čísla, a zařadí je do tříd.
    """
    zaznamy = sorted((HERE.parent / "mereni").glob("*.json"))
    if not zaznamy:
        print("v mereni/ není žádný záznam — pusť napřed cb-wiki.py --json")
        return
    zaznam = json.loads(zaznamy[-1].read_text(encoding="utf-8"))
    print(f"\nKORPUS — {zaznamy[-1].name}\n  orákulum: {zaznam['oracle']}")
    for tema in zaznam["topics"]:
        print(f"  zdroj:    {tema['provenance']}")
    print()
    vsech = neprecteno = 0
    tridy: Counter[str] = Counter()
    ukazky: dict[str, str] = {}
    for tema in zaznam["topics"]:
        for veta in tema["sentences"]:
            vsech += 1
            if veta["verdict"] != Verdict.UNREAD.value:
                continue
            neprecteno += 1
            if "shoda čísla" not in veta["reason"]:
                continue
            r = zjisti(oracle, veta["text"])
            if "reading" not in r:
                tridy["orákulum nevrátilo čtení"] += 1
                continue
            jmeno = trida(r["reading"], r["Number"])
            tridy[jmeno] += 1
            ukazky.setdefault(
                jmeno, f"{veta['text'][:96]}   [{r['přísudek']} Number={r['Number']}]"
            )
    zahozeno = sum(tridy.values())
    print(f"  vět celkem                {vsech:4}")
    print(f"  NEPŘEČTENO                {neprecteno:4}"
          f"  ({100.0 * neprecteno / max(vsech, 1):.1f} % korpusu)")
    print(f"  z toho na shodě čísla     {zahozeno:4}"
          f"  ({100.0 * zahozeno / max(neprecteno, 1):.1f} % NEPŘEČTENO,"
          f" {100.0 * zahozeno / max(vsech, 1):.1f} % korpusu)")
    print()
    for jmeno, kolik in sorted(tridy.items()):
        print(f"    {kolik:4}  {jmeno}")
        if jmeno in ukazky:
            print(f"          » {ukazky[jmeno]}")


def main() -> None:
    oracle = UDPipeOracle()
    print(f"orákulum: {oracle.provenance}")
    print(f"jádro:    {CONBOND4}")
    padlo, spatne = minimalni_pary(oracle)
    celkem = sum(len(p) for _, p in TRIDY)
    print(f"\n  padlo {padlo} z {celkem} párů;"
          f" kontrolních a protějších vět selhalo: {spatne}")
    if "--korpus" in sys.argv:
        korpus(oracle)


if __name__ == "__main__":
    main()
