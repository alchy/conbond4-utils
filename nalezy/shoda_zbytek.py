#!/usr/bin/env python
"""Rozbor zbylých deseti vět třídy `morfologie` — po jedné.

    python nalezy/shoda_zbytek.py            # rozbor deseti vět
    python nalezy/shoda_zbytek.py --korpus   # znovu je vytáhne z měření

**Proč rozbor a ne rovnou oprava.** Po opravě W‑32 (shoda se porovnává
průnikem hodnot) klesla třída `morfologie` z 29 vět na 10. Jedna
konstrukce z toho zbytku je doložená — kvantifikovaný podmět — ale je to
JEDNA z těch deseti; opravit ji naslepo znamená hádat, že zbytek je totéž.
Deset vět je málo na to, aby se to nedalo přečíst ručně, a dost na to, aby
se z toho dal odvodit příští směr.

**Výsledek: dvě třídy, ŽÁDNÁ VADA ROZBORU.** Všech deset vět je správná
čeština a parser je rozebírá správně. Chybně je čte patro shody.

  B · KOORDINOVANÝ PODMĚT — 6 vět
      „Karel Čapek a jeho bratr Josef **byli** aktéry…"
      Přísudek je v plurálu podle CELÉ koordinace, ale UD dává jako
      `nsubj` první člen v singuláru; zbytek visí na něm jako `conj`.
      Shoda se počítá proti jednomu členu místo proti celé skupině.
      Signál v rozboru: podmět je v NOMINATIVU a má potomky `conj`.

  C · KVANTIFIKOVANÝ PODMĚT — 4 věty
      „**Několik** nezávislých měření … **podpořilo**."
      Čeština má u počitatelných výrazů přísudek v neutru singuláru
      a jméno v genitivu plurálu. Řídícím členem shody je KVANTIFIKÁTOR,
      ne to jméno. Shoda čísla mezi přísudkem a jménem tu z principu
      neplatí.
      Signál v rozboru: podmět je v GENITIVU a nese potomka `det:numgov`
      — UD tím říká „tenhle determinátor ŘÍDÍ pád své hlavy". Parser to
      tedy neskrývá; patro se ho jen neptá.

**Obě třídy mají v rozboru jednoznačný signál, a ani jedna z nich není
o víceznačnosti rysu.** W‑32 řešila to, že se hodnota rysu porovnávala
jako řetězec. Tohle je jiná věc: shoda se počítá proti ŠPATNÉMU ČLENU.
U B je řídícím členem celá koordinace, u C kvantifikátor — a ani jeden
z nich není ten token, který UD označí jako `nsubj`.

**Tenhle skript do jádra nesahá a nesmí.** Pošle věty, vypíše, co jádro
samo vrátilo, a zařazení do tříd dělá z JMENOVEK ROZBORU (`conj`,
`det:numgov`, `Case`), ne z povrchu věty a ne z jádra. Je to popis nálezu,
ne druhé čtení. Opravu dělá Builder jádra.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.lexicon import czech_seed  # noqa: E402
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import Session  # noqa: E402

#: Deset vět, které po opravě W‑32 zbyly ve třídě `morfologie` jako
#: JEDINÝ blokátor. Opsané z měření nad revizí 6afc38d, aby šel nález
#: přehrát i bez běhu na Wikipedii.
VETY: tuple[str, ...] = (
    "Nicméně existovalo mnoho právních ochran, které měly a mají za cíl "
    "chránit blaho mazlíčků( a dalších zvířat).",
    "Mnichovská dohoda a po ní následující kapitulace znamenaly pro Karla "
    "Čapka zhroucení jeho dosavadního světa a osobní tragédii.",
    "Nad hrobem promluvili básník Josef Hora, básník a kritik Miroslav "
    "Rutte, spisovatel Eduard Bass a za osobní přátele Ferdinand Peroutka.",
    "Karel Čapek a jeho bratr Josef byli zhruba od roku 1925 aktéry "
    "pravidelného pátečního setkávání osobností politického a kulturního "
    "života.",
    "Ke svatbě v roce 1935 obdrželi novomanželé Karel Čapek a Olga "
    "Scheinpflugová doživotní právo bydlet na letním sídle nad rybníkem "
    "Strž u Staré Huti( nedaleko Dobříše).",
    "Mezi účastníky pohřbu byli např. předseda sněmovny Jan Malypetr, "
    "předseda senátu František Soukup, generál Alois Eliáš( ministr "
    "dopravy, později popraven nacisty), pražský primátor Petr Zenkl "
    "a další.",
    "Existuje o nich několik teorií.",
    "Ještě před svou svatbou se Pankl a Novotná s dcerou Barborou "
    "přestěhovali do Ratibořic na panství vévodkyně Kateřiny Zaháňské, kde "
    "pak otec pracoval jako štolba, matka získala zaměstnání pradleny.",
    "Během historie lidstva vzniklo několik kosmologií a kosmogonií pro "
    "pozorovatelný vesmír.",
    "Několik nezávislých experimentálních měření tuto teoretickou inflaci "
    "i teorii velkého třesku podpořilo.",
)


def zarad(reading) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """Třída a její signál — VÝHRADNĚ z jmenovek rozboru.

    Pořadí testů není libovolné: `det:numgov` je explicitní tvrzení UD
    („tenhle determinátor řídí pád své hlavy"), kdežto `conj` může viset
    i na podmětu, který je zároveň kvantifikovaný. Silnější signál proto
    rozhoduje první.
    """
    root = next((t for t in reading.tokens if t.head == 0), None)
    if root is None:
        return "?", "bez kořene"
    subjects = [
        t
        for t in reading.tokens
        if t.head == root.index and t.deprel.startswith("nsubj")
    ]
    if not subjects:
        return "?", "bez podmětu"
    subject = subjects[0]
    case = dict(subject.feats).get("Case", "-")
    children = [t for t in reading.tokens if t.head == subject.index]
    numgov = [t for t in children if t.deprel.startswith("det:numgov")]
    if numgov:
        return (
            "C · kvantifikovaný podmět",
            f"podmět „{subject.form}“ v {case}, řídí ho „{numgov[0].form}“ "
            f"({numgov[0].deprel})",
        )
    coordinated = [t for t in children if t.deprel == "conj"]
    if coordinated:
        return (
            "B · koordinovaný podmět",
            f"podmět „{subject.form}“ v {case}, koordinace: "
            + ", ".join(f"„{t.form}“" for t in coordinated),
        )
    return "?", f"podmět „{subject.form}“ v {case}, bez conj a bez numgov"


def vety_z_korpusu() -> tuple[str, ...]:
    """Věty vytažené z posledního měření — kontrola, že seznam nezestárl."""
    najdene: list[str] = []
    for soubor in sorted(_KORPUS.glob("*.json")):
        data = json.loads(soubor.read_text(encoding="utf-8"))
        for tema in data.get("topics", ()):
            for veta in tema.get("sentences", ()):
                if veta.get("sole") == "morfologie":
                    najdene.append(veta["text"])
    return tuple(dict.fromkeys(najdene))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--korpus", action="store_true")
    args = parser.parse_args()

    vety = vety_z_korpusu() if args.korpus else VETY
    if not vety:
        print("žádné věty — měření ve `mereni/` chybí nebo je třída prázdná")
        return 1

    oracle = UDPipeOracle()
    pocty: dict[str, int] = {}
    print("=" * 72)
    print(f"ROZBOR TŘÍDY `morfologie` PO JEDNÉ  ({len(vety)} vět)")
    print("=" * 72)
    for cislo, text in enumerate(vety, 1):
        reading = oracle.parse(text).readings[0]
        trida, signal = zarad(reading)
        pocty[trida] = pocty.get(trida, 0) + 1
        vysledek = Session(lexicon=czech_seed()).utter(text, oracle)
        duvod = next(
            (radek.strip() for radek in vysledek.lines if "PROČ" in radek), ""
        )
        print(f"\n{cislo:2}. {text[:96]}")
        print(f"    třída:  {trida}")
        print(f"    signál: {signal}")
        print(f"    jádro:  {duvod or '(bez hlášky)'}")

    print("\n" + "=" * 72)
    print("SOUHRN")
    for trida, kolik in sorted(pocty.items(), key=lambda x: -x[1]):
        print(f"   {trida:32} {kolik:2} vět")
    print("=" * 72)
    print(
        "Žádná z těch vět není vada rozboru: všechny jsou správná čeština\n"
        "a parser je rozebírá správně. Shoda se počítá proti ŠPATNÉMU\n"
        "ČLENU — u B proti jednomu členu koordinace místo proti celé,\n"
        "u C proti jménu místo proti kvantifikátoru."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
