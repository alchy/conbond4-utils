#!/usr/bin/env python
"""Kolik významů nese genitivní přívlastek — rozbor 19 vět (W‑39).

    python nalezy/genitiv_vyznamy.py

**Hypotéza k ověření** (zadání kola #78): systém má tah `→'`
(`names_owner`) pro přivlastnění. Padá genitivní přívlastek celý do něj,
nebo se dělí na víc významů?

**Odpověď: dělí se, a hypotéza neplatí.** Přivlastnění je z těch významů
jen jeden a ani ne nejčastější. Doložené dvojice `hlava — genitiv` ze
19 vět měřeného korpusu se rozpadají takhle:

  1 · PŘEDMĚT DĚJE (objektový genitiv) — „chov **zvířat**", „vlastnictví
      **mazlíčka**", „hledání **viníků**", „pozorování **vesmíru**",
      „vznik **cukrovky**". Hlava je DĚJ a genitiv je to, k čemu ten děj
      míří.

  2 · PŮVODCE DĚJE (subjektový genitiv) — „péče **majitele**", „přínos
      **Němcové**", „vývoj **astronomie**", „svatba **otce**". Táž
      stavba jako 1, opačný směr.

  3 · NOSITEL VLASTNOSTI — „hmotnost **zvířat**", „původ
      **spisovatelky**", „osud **vesmíru**".

  4 · ČÁST Z CELKU (partitivní) — „polovina **domu**", „polovina
      **roku**", „typy **psů**".

  5 · MÍRA A DRUH — „míra **péče**", „proces **výběru**", „třída
      **terapie**".

  Z · NENÍ TO PŘÍVLASTEK — „Hradci **Králové**" je jedno víceslovné
      jméno, které rozbor rozdělil na hlavu a `nmod`.

**Proč to rozhoduje o tvaru opravy.** Dvojice 1 a 2 mají TÝŽ POVRCH
a opačný význam: „přínos Němcové" je to, čím přispěla ONA, kdežto „popis
Němcové" je popis JEJÍ. Z tvaru se to rozlišit nedá — je to táž třída
dvojznačnosti jako holá spona (`member` × `subset`), a platí na ni týž
závěr: **navrhnout a zeptat se, nikdy nedosadit.**

**Druhý nález, strukturní a možná důležitější.** Genitivní přívlastek
visí pod JMÉNEM, ne pod přísudkem: „Druhou polovinu **domu** obýval
bratr." má `domu` jako `nmod` pod `polovinu`. Není to tedy role
predikace — predikace nese role SLOVESA, a `domu` není argument
„obývat". Proto se dnes hlásí jako ZTRACENÝ ČLEN a proto by „dát mu jméno
role" byla oprava špatného tvaru: ono to role není. Je to vztah dvou
JMEN uvnitř jedné fráze, tedy druhý výrok vedle věty — přesně ten tvar,
jaký už má přivlastnění (`→'` zapisuje větu a k ní vztah).

**Tenhle skript do jádra nesahá a nesmí.** Čte záznam měření a vypisuje
doložené dvojice; zařazení do významů je POPIS NÁLEZU, který udělal
člověk nad daty, a je tu proto zapsané ručně — na rozdíl od rodin
v `role_rozbor.py`, které jdou odvodit z jmenovek rozboru. Kdyby se
tvářilo jako strojové, tvrdilo by to víc, než čím je.
"""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_TVAR = re.compile(r"„([^„\"]+)“ \(([^)]+)\)")

#: `genitiv → (význam, hlava)`. Zapsáno RUČNĚ z doložených vět; strojově
#: to z rozboru nejde, a předstírat opak by bylo tvrzení navíc.
VYZNAMY: dict[str, tuple[str, str]] = {
    "zvířat": ("1 · předmět děje", "chov"),
    "mazlíčků": ("1 · předmět děje", "chov"),
    "mazlíčka": ("1 · předmět děje", "vlastnictví"),
    "viníků": ("1 · předmět děje", "hledání"),
    "cukrovky": ("1 · předmět děje", "vznik"),
    "vzniku": ("1 · předmět děje", "riziko"),
    "pozorování": ("1 · předmět děje", "nepřesnosti"),
    "majitele": ("2 · původce děje", "péče"),
    "Němcové": ("2 · původce děje", "přínos"),
    "astronomie": ("2 · původce děje", "vývoj"),
    "otce": ("2 · původce děje", "svatba"),
    "spisovatelky": ("3 · nositel vlastnosti", "původ"),
    "Boženy": ("3 · nositel vlastnosti", "původ"),
    "vesmíru": ("3 · nositel vlastnosti", "osud"),
    "domu": ("4 · část z celku", "polovina"),
    "roku": ("4 · část z celku", "polovina"),
    "psů": ("4 · část z celku", "typy"),
    "péče": ("5 · míra a druh", "míra"),
    "výběru": ("5 · míra a druh", "proces"),
    "terapie": ("5 · míra a druh", "třída"),
    "Králové": ("Z · není přívlastek", "Hradci"),
}


def _posledni_zaznam() -> Path:
    """Nejnovější podle ČASU, ne podle abecedy — viz `role_rozbor.py`."""
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not zaznamy:
        raise SystemExit("ve `mereni/` není žádný záznam")
    return zaznamy[-1]


def main() -> int:
    zaznam = _posledni_zaznam()
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    vety = [
        veta
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
        if veta.get("sole") == "role"
    ]

    nalezene: list[tuple[str, str]] = []
    for veta in vety:
        for slovo, tvar in _TVAR.findall(veta.get("reason") or ""):
            if tvar.split(">")[-1] == "nmod+Gen":
                nalezene.append((slovo, veta["text"]))

    s_vyznamem = {slovo for slovo, _ in nalezene if slovo in VYZNAMY}
    print("=" * 72)
    print(f"GENITIVNÍ PŘÍVLASTEK — kolik významů  ({zaznam.name})")
    print("=" * 72)
    print(f"doložených výskytů: {len(nalezene)} · z toho zařazených: {len(s_vyznamem)}")

    podle = collections.defaultdict(list)
    for slovo, _ in nalezene:
        if slovo in VYZNAMY:
            vyznam, hlava = VYZNAMY[slovo]
            podle[vyznam].append(f"{hlava} {slovo}")

    print("\nVÝZNAM                        výskytů   doložené dvojice")
    for vyznam, dvojice in sorted(podle.items()):
        unikat = sorted(set(dvojice))
        print(f"   {vyznam:28} {len(dvojice):3}    {', '.join(unikat)}")

    nezarazene = sorted({slovo for slovo, _ in nalezene} - s_vyznamem)
    if nezarazene:
        print(f"\nnezařazeno ({len(nezarazene)}): {', '.join(nezarazene)}")

    print("\n" + "=" * 72)
    print(
        "ZÁVĚR: významů je PĚT a hypotéza „všechno je přivlastnění“ neplatí.\n"
        "Dvojice 1 a 2 mají TÝŽ POVRCH a opačný směr („přínos Němcové“ ×\n"
        "„popis Němcové“), takže se z tvaru rozlišit nedají — je to táž\n"
        "třída dvojznačnosti jako holá spona a platí na ni týž závěr:\n"
        "NAVRHNOUT A ZEPTAT SE, NIKDY NEDOSADIT.\n"
        "\n"
        "STRUKTURNĚ: genitiv visí pod JMÉNEM, ne pod přísudkem, takže to\n"
        "vůbec není role predikace — je to vztah dvou jmen uvnitř fráze,\n"
        "tedy druhý výrok vedle věty, jako u přivlastnění (`→'`)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
