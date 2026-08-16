"""Atribuce textů, které leží v záznamech měření.

Záznam nese **celé věty** korpusu conBondu2, a ty pocházejí z české
Wikipedie pod **CC BY‑SA**. Držet je v gitu je vědomé rozhodnutí (viz
`ZDROJ.md`): bez věty se ze záznamu nedá zjistit, na co se systém ptal,
a to je jediné, k čemu ta vrstva je. Rozhodnutí ale nese povinnost —
uvést zdroj a licenci, a to **po dokumentech**, ne jedním řádkem
„conBond2@418d7f7".

Soubor se generuje ze záznamů, ne píše rukou. Ručně psaná atribuce
zestárne přesně tak, jak zestaraly cesty v `nalezy/`: přibude dokument
a nikdo si nevšimne.

**Odvozený odkaz se pozná od doloženého.** conBond2 si u článků URL
nedrží, takže se skládá z názvu souboru — a u toho, kde se skládá,
je to napsané. Tvrdit „zdroj je tenhle" tam, kde je to dohad, by bylo
totéž jako měřit odhadem.
"""

from __future__ import annotations

import json
from pathlib import Path

WIKI = "https://cs.wikipedia.org/wiki/"

#: Ručně psané texty conBondu2 — **žádný vnější zdroj** (jejich
#: `data/raw/ZDROJ.md`). Nesmí se jim přilepit odkaz na Wikipedii; to by
#: byla atribuce naopak, tedy tvrzení o původu, který neexistuje.
VLASTNI: tuple[str, ...] = (
    "fyzika_gravitace",
    "příroda_česká",
    "rodina_novákovi",
    "vztahy_příbuzenské",
    "poznámky_domácnost",
    "skot",
)

#: Kde se název článku z názvu souboru odvodit nedá.
VYJIMKY: dict[str, str] = {
    "rur": "R.U.R.",
    "bílá_nemoc": "Bílá nemoc",
    "válka_s_mloky": "Válka s mloky",
}

#: Dokumenty o OSOBÁCH. Wikipedie píše velké písmeno v obou částech
#: jména („Alois Jirásek"), kdežto u obecného názvu jen v prvním slově
#: („Kočka domácí") — a rozlišit to z názvu souboru nejde. Je to proto
#: **výčet, ne heuristika**: neznámý dvouslovný dokument dostane
#: opatrnější variantu s malým druhým slovem, což je vidět a dá se
#: opravit; hádající pravidlo by tiše vyrábělo špatné odkazy.
OSOBY: tuple[str, ...] = (
    "alois_jirásek",
    "bohumil_hrabal",
    "božena_němcová",
    "egon_hostovský",
    "františek_halas",
    "jaroslav_hašek",
    "josef_čapek",
    "josef_škvorecký",
    "karel_čapek",
    "milan_kundera",
    "ota_pavel",
    "václav_havel",
    "vladislav_vančura",
)


def titul(dokument: str) -> str:
    """Název článku odvozený z názvu souboru."""
    if dokument in VYJIMKY:
        return VYJIMKY[dokument]
    slova = dokument.split("_")
    if dokument in OSOBY:
        return " ".join(s.capitalize() for s in slova)
    return " ".join([slova[0].capitalize(), *slova[1:]])


def odkaz(dokument: str) -> str:
    return WIKI + titul(dokument).replace(" ", "_")


def dokumenty_zaznamu(mereni: Path) -> dict[str, list[str]]:
    """Jaký dokument leží v jakých záznamech. Čte se ze **všech**
    záznamů, ne z toho posledního — v repu jsou i starší běhy a jejich
    věty tam leží taky."""
    kde: dict[str, list[str]] = {}
    for cesta in sorted(mereni.glob("korpus-*.json")):
        try:
            zaznam = json.loads(cesta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # pragma: no cover
            continue
        for dokument in zaznam.get("documents", []):
            kde.setdefault(dokument["name"], []).append(cesta.name)
    return kde


def zapis(mereni: Path, korpus: str) -> Path:
    """Vygeneruje `mereni/LICENCE.md`. Vrací cestu."""
    kde = dokumenty_zaznamu(mereni)
    z_wiki = sorted(d for d in kde if d not in VLASTNI)
    vlastni = sorted(d for d in kde if d in VLASTNI)

    radky = [
        "# Licence a atribuce textů v záznamech",
        "",
        "Záznamy v téhle složce (`korpus-*.json`) a mapa `baseline.html`",
        "obsahují **celé věty** z korpusu conBondu2. Většina těch textů",
        "pochází z **české Wikipedie** a je pod licencí",
        "**CC BY-SA 4.0** — <https://creativecommons.org/licenses/by-sa/4.0/>.",
        "",
        "Co z toho plyne pro toho, kdo si repozitář forkne: tenhle adresář",
        "je **odvozené dílo** a šíří se dál pod touž licencí, s uvedením",
        "zdroje. Zbytek repozitáře (kód, dokumentace, zlaté sady) je vlastní",
        "dílo projektu a licence Wikipedie se ho netýká.",
        "",
        f"Korpus: `{korpus}` (soubory `data/raw/*.txt`).",
        "",
        "## Z české Wikipedie, CC BY-SA 4.0",
        "",
        "Odkaz je **odvozený z názvu souboru** — conBond2 si u článků URL",
        "nedrží. U několika článků je název ručně opravený (`R.U.R.`), jinde",
        "může odkaz mířit na rozcestník; je to atribuce, ne katalog.",
        "",
        "| dokument | článek | odkaz | v záznamech |",
        "|---|---|---|---|",
    ]
    for dokument in z_wiki:
        radky.append(
            f"| `{dokument}` | {titul(dokument)} | <{odkaz(dokument)}> |"
            f" {len(kde[dokument])} |"
        )
    if vlastni:
        radky += [
            "",
            "## Psané ručně v conBondu2 — bez vnějšího zdroje",
            "",
            "Podle `data/raw/ZDROJ.md` conBondu2. **Odkaz na Wikipedii se jim",
            "nepřilepuje** — to by byla atribuce naopak, tedy tvrzení o původu,",
            "který neexistuje.",
            "",
            "| dokument | v záznamech |",
            "|---|---|",
        ]
        for dokument in vlastni:
            radky.append(f"| `{dokument}` | {len(kde[dokument])} |")
    radky += [
        "",
        "---",
        "",
        "Soubor **se generuje** (`cb_utils/atribuce.py`) při každém zápisu",
        "záznamu. Ručně psaná atribuce by zestárla hned s dalším dokumentem —",
        "a atribuce, která nezahrnuje všechno, co v repu leží, je horší než",
        "žádná, protože vypadá jako splněná povinnost.",
        "",
    ]
    cil = mereni / "LICENCE.md"
    cil.write_text("\n".join(radky), encoding="utf-8")
    return cil
