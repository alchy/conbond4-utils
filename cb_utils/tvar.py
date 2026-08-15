"""Co to na vstupu vůbec bylo — věta, nadpis, nebo položka seznamu.

Vrstva `tvar` stojí **před** vším ostatním a je tu proto, že jinak se
plete *„conBond4 tuhle větu neumí přečíst"* s *„tohle vůbec nebyla
věta"*. To jsou dva různé nálezy a slévat je znamená, že měření lže:
první je mezera schopnosti, druhý vlastnost zdroje.

Tři pravidla, která se drží:

1. **Označit, nemazat.** Přesně jako `Vyp=proza` / `Vyp=seznam`
   v conBondu2 — *„pole má být obraz textu a v článku ta bibliografie
   je; zahodit půlku korpusu by navíc změnilo všechna dosud naměřená
   čísla."* Označený řádek **nezmizí ze jmenovatele**, dostane svůj
   řádek v reportu.
2. **Původní řetězec zůstává.** Do záznamu jde vždycky to, co přišlo
   ze zdroje, ne to, co z toho udělalo předzpracování.
3. **Pravidlo je obecné**, ne seznam konkrétních vět. Rozhoduje tvar
   řádku a **jmenovky rozboru** (má kořen určité sloveso?), tedy něco,
   co jde pustit na libovolný obdobný text.

Poslední bod je důležitý i proti sobě samému: „nemá určité sloveso"
**není** totéž co „conBond4 to nepřečte". Jsou věty bez slovesa, které
jsou plnohodnotné výpovědi, a naopak. Proto je `tvar` **samostatná osa**
vedle stavu, ne jeho náhrada — v reportu se kříží, nesčítají.
"""

from __future__ import annotations

import re
from enum import Enum

#: Nadpis sekce v holém textu Wikipedie i v `data/raw/` conBondu2.
_NADPIS = re.compile(r"^\s*=+.*=+\s*$")
#: Odrážka, číslovaný bod, tabulkový řádek.
_POLOZKA = re.compile(r"^\s*([*#|•\-–—]|\d+[.)])\s+")
#: Nadpis s dvojtečkou — „Toxické rostliny: Určité druhy …". Levá strana
#: je krátká a bez určitého slovesa; je to popiska odstavce, ne věta.
_POPISKA = re.compile(r"^[^.:!?]{2,40}:\s+\S")


class Tvar(Enum):
    VETA = "věta"
    NADPIS = "nadpis"
    POLOZKA = "položka"
    POPISKA = "popiska"
    BEZ_SLOVESA = "bez slovesa"


#: Kořeny, které nesou určité sloveso. `cop` sem patří: „X byl prozaik"
#: je výpověď, i když kořenem je jméno — conBond2 na tom doplatil (viz
#: `je_jmenny_prisudek` v jeho `baseline.py`).
_SLOVESO = ("VERB", "AUX")


def z_radku(radek: str) -> Tvar | None:
    """Tvar poznatelný **z řádku samotného**, bez rozboru.

    Vrací `None`, když z řádku nic určit nejde — pak rozhoduje rozbor.
    """
    if _NADPIS.match(radek):
        return Tvar.NADPIS
    if _POLOZKA.match(radek):
        return Tvar.POLOZKA
    if _POPISKA.match(radek):
        return Tvar.POPISKA
    return None


def z_rozboru(upos_kořene: str, má_sponu: bool) -> Tvar:
    """Tvar podle rozboru: má věta určité sloveso, nebo sponu?

    Bere se **z jmenovek rozboru**, ne z povrchu — je to táž zásada jako
    v `diagnose.py`. Klasifikátor, který by se díval na text a hádal
    „tohle asi není věta", by měřil sám sebe.
    """
    if upos_kořene in _SLOVESO or má_sponu:
        return Tvar.VETA
    return Tvar.BEZ_SLOVESA


def urči(radek: str, upos_kořene: str, má_sponu: bool) -> Tvar:
    """Tvar řádku. Povrch má přednost: nadpis zůstává nadpisem, i když
    v něm rozbor kořen se slovesem najde."""
    z_povrchu = z_radku(radek)
    if z_povrchu is not None:
        return z_povrchu
    return z_rozboru(upos_kořene, má_sponu)
