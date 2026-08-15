"""Historický korpus conBondu2 — text, zlaté sady, revize.

Krok 4 zadání staví měření nad **korpusem conBondu2**, ne nad novou
Wikipedií. Má to jednu vlastnost, kterou živý zdroj mít nemůže: je
**zmražený**. Článek na Wikipedii se mezi dvěma běhy změní a měřicí
nula se pod rukama pohne; commit v cizím repozitáři ne.

**Do gitu se nestahuje.** `data/` je v `.gitignore`, texty jsou pod
CC BY‑SA (viz `ZDROJ.md`). Submodul by je vtáhl do každého klonu, což
je přesně to, čemu se ZDROJ.md brání — proto klon skriptem, který si
kdokoli pustí sám a dojde k témuž stavu podle revize.

Identita korpusu je **revize conBondu2**, ne revize jednotlivých
článků: články v něm už žádnou vlastní revizi nenesou, jsou to soubory
v repozitáři. Kdo chce dohledat, odkud text je, najde to v jejich
`data/raw/ZDROJ.md`.
"""

from __future__ import annotations

import json
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ODKUD = "https://github.com/alchy/conBond2.git"
TIMEOUT_S = 300.0


class KorpusError(Exception):
    """Korpus se nepodařilo pořídit."""


@dataclass(frozen=True, slots=True)
class Korpus:
    koren: Path
    revize: str

    @property
    def provenance(self) -> str:
        return f"github.com/alchy/conBond2@{self.revize}"

    def dokumenty(self) -> tuple[str, ...]:
        """Jména dokumentů (bez `.txt`), setříděná — pořadí je součást
        reprodukovatelnosti."""
        raw = self.koren / "data" / "raw"
        return tuple(sorted(p.stem for p in raw.glob("*.txt")))

    def text(self, jmeno: str) -> str:
        cesta = self.koren / "data" / "raw" / f"{jmeno}.txt"
        if not cesta.exists():
            raise KorpusError(f"dokument {jmeno!r} v korpusu není")
        return cesta.read_text(encoding="utf-8")

    def zlata(self, jmeno: str) -> list[dict]:
        """`etalon` (40 ručních), `conbond` (95 ze staršího conBondu),
        `otazky` (682 generovaných)."""
        cesta = self.koren / "data" / "gold" / f"{jmeno}.json"
        if not cesta.exists():
            raise KorpusError(f"zlatá sada {jmeno!r} v korpusu není")
        return json.loads(cesta.read_text(encoding="utf-8"))


#: Předpony, kterými zlaté sady odkazují na zdroj místo na dokument.
_PREDPONY = ("wiki_", "wikisofia_", "wikipedie_")


def klic(jmeno: str) -> str:
    """Jméno dokumentu na porovnatelný klíč.

    **Zlatá sada a korpus se rozešly ve jménech.** `etalon.json`
    a `conbond.json` odkazují na 32 dokumentů, ale doslovnou shodou jich
    v `data/raw/` sedí jen 14. Zbytek jsou tři různé věci a jen jedna
    z nich je „ten text tam opravdu není":

        wiki_pes_domácí     → pes_domácí        předpona zdroje
        rodina_novakovi     → rodina_novákovi   diakritika
        wiki_r.u.r.         → rur               tečky ve zkratce
        bible_genesis       → —                 text v korpusu NENÍ

    Kdyby se porovnávalo doslova, osm dokumentů by ze sady tiše vypadlo
    a měřilo by se míň, než se tvrdí. Kdyby se naopak spojovalo
    volně, začaly by se lepit různé texty. Klíč je proto úzký a **co
    nesedne, se vypíše** — nespojené položky nemizí, dostanou svůj řádek.
    """
    text = jmeno.strip().lower()
    for predpona in _PREDPONY:
        if text.startswith(predpona):
            text = text[len(predpona) :]
    text = unicodedata.normalize("NFKD", text)
    return "".join(z for z in text if z.isalnum())


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT_S,
    )


def porid(kam: Path, *, revize: str = "") -> Korpus:
    """Klon (nebo aktualizace) korpusu a jeho revize.

    `revize` prázdná znamená „co je na dálku", vyplněná znamená
    **pin**: měření po změně jádra má běžet nad TÝMŽ korpusem, jinak se
    nedá rozeznat zlepšení systému od změny vstupu.
    """
    if not (kam / ".git").exists():
        kam.parent.mkdir(parents=True, exist_ok=True)
        done = _git("clone", "--filter=blob:none", ODKUD, str(kam))
        if done.returncode != 0:
            raise KorpusError(f"klon selhal: {done.stderr.strip()[:200]}")
    if revize:
        done = _git("-C", str(kam), "checkout", "--quiet", revize)
        if done.returncode != 0:
            raise KorpusError(
                f"revize {revize!r} v korpusu není: {done.stderr.strip()[:200]}"
            )
    head = _git("-C", str(kam), "rev-parse", "--short", "HEAD")
    if head.returncode != 0:
        raise KorpusError(f"revizi nelze zjistit: {head.stderr.strip()[:200]}")
    return Korpus(koren=kam, revize=head.stdout.strip())


#: Řádky, které v `data/raw/` nejsou próza. Pravidlo je **obecné** a je
#: to totéž, co dělal `baseline.py` conBondu2 (`NEPATRI`): nadpis sekce,
#: odrážka, mřížka, tabulkový řádek. Nezahazuje se nic **uvnitř** věty
#: a nesmaže se ani ten řádek — jen se pozná, co to je (`cb_utils/tvar.py`).
def odstavce(text: str) -> tuple[str, ...]:
    """Řádky textu bez prázdných. **Nic se nefiltruje.**

    Rozhodnutí, co je věta a co nadpis nebo položka seznamu, dělá až
    `tvar.py` a **označuje** to, nemaže. Kdyby se filtrovalo tady,
    zmizely by ty řádky ze jmenovatele a měření by tvrdilo pokrytí,
    které nemá.
    """
    return tuple(radek.strip() for radek in text.split("\n") if radek.strip())
