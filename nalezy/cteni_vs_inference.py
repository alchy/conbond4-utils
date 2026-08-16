#!/usr/bin/env python
"""Tři různé vady, které se z jednoho čísla nedají rozeznat.

    python nalezy/cteni_vs_inference.py [záznam.json]

Report, ze kterého jde zjistit jen „věta neprošla", je počítadlo.
Zadání žádá, aby z něj šlo rozeznat **rozbor rozuměl, jádro to neumělo
použít** od **rozbor vyrobil špatné čtení** a od **chybí znalost** —
protože každá z těch tří vede jinam:

    rozbor rozuměl, jádro nedotáhlo  → oprava v jádře (role, kvantifikace)
    rozbor vyrobil špatné čtení      → oprava v kaskádě nebo v patrech
    chybí znalost                    → doplnit bázi, dialogem nebo ručně

**Rozhoduje se ze záznamu, ne z nového běhu.** Každá věta v něm nese
rozbor (`parse`, tvar/UPOS/deprel) i vybrané čtení (`reading`), takže
se dá porovnat, KOMU jádro dalo roli podmětu, s tím, koho za podmět
označil rozbor. Když se to rozejde, čtení je špatně — a je to vidět bez
toho, aby se cokoli pouštělo znovu.

**Mez metody, a je podstatná.** Párování jde přes tvar a lemma, a čeština
je ohýbá tak, že to občas nesedne: „∀jezdecký_kůň" se s tokenem „koně"
nespáruje (kůň/koně) a zbyde přívlastek „Jezdečtí" jako `amod`, takže
věta vypadá jako špatné čtení a není. Proto se ta kategorie jmenuje
**kandidát**, ne nález, a `--vse` je tu od toho, aby si je člověk prošel.
Z dvanácti kandidátů prvního běhu jich ruční kontrolou obstály čtyři —
zbytek byla tahle vada párování. Číslo, které si nikdo neprošel, by
tvrdilo víc, než ukazuje.
"""

from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cb_utils.zaznamy import vyber  # noqa: E402

#: „◐ přečteno, neúplné  pohřbený(kde:vyšehradský_hřbitov, kdo:on)"
_ROLE = re.compile(r"(\w+):([^,()]+)")
#: „Povodeň/NOUN/nsubj→2"
_TOKEN = re.compile(r"^(.+)/([A-Z]+)/([^→]+)→(\d+)$")

#: Které role kaskády mají v rozboru odpovídat kterým závislostem.
#: Víc než jedna hodnota proto, že „kdo" může být `nsubj` i `nsubj:pass`.
#:
#: `flat` je u obou schválně: víceslovné jméno („Alois Jirásek") drží
#: rozbor jako `nsubj` + `flat` a čtení z nich skládá jeden uzel, takže
#: role sedí na obě části. Bez toho by každé jméno o dvou slovech
#: vypadalo jako špatné čtení — první verze tohohle skriptu to tak měla
#: a nahlásila 127 „špatných čtení", z nichž většina byla artefakt
#: párování. Měřicí nástroj, který si vyrobí vlastní falešný nález, je
#: horší než žádný.
_OCEKAVANE: dict[str, tuple[str, ...]] = {
    "kdo": ("nsubj", "nsubj:pass", "root", "cop", "flat", "appos", "conj"),
    "co": ("obj", "iobj", "xcomp", "ccomp", "flat", "appos", "conj"),
}
#: Značky kvantifikátoru a určenosti, které čtení lepí před jméno.
_ZNACKY = "·∃∀"


def _tokeny(parse: list[str]) -> list[tuple[str, str, str]]:
    out = []
    for polozka in parse:
        m = _TOKEN.match(polozka)
        if m:
            out.append((m.group(1), m.group(2), m.group(3)))
    return out


def _role_ve_cteni(reading: str) -> dict[str, str]:
    if "(" not in reading:
        return {}
    uvnitr = reading[reading.index("(") + 1 : reading.rindex(")")]
    return {m.group(1): m.group(2).strip() for m in _ROLE.finditer(uvnitr)}


def _sedi(hodnota: str, tvar: str) -> bool:
    """Čtení nese lemma a složeniny (`vyšehradský_hřbitov`), rozbor tvar.

    Značky kvantifikátoru (`·`, `∃`, `∀`) se ořezávají — jsou to
    rozhodnutí jádra o určenosti, ne součást jména, a dokud se neořezly,
    „·Alois_Jirásek" se s tokenem „Alois" nespároval vůbec.
    """
    ocesane = hodnota.lower().replace("_", " ")
    kusy = [k.strip(_ZNACKY) for k in ocesane.split()]
    t = tvar.lower().strip(_ZNACKY)
    # Krátké tvary se nepárují: `z`, `k`, `v` jsou předložky a shoda na
    # prvním písmenu z nich udělá „kdo: začít sedí na token `z`". Druhá
    # verze skriptu na tom vyrobila dalších pár falešných nálezů.
    if len(t) < 3:
        return False
    return any(t.startswith(k[:4]) or k.startswith(t[:4]) for k in kusy if len(k) > 2)


def zarad(veta: dict) -> tuple[str, str]:
    """(kategorie, vysvětlení) — všechno ze záznamu, nic z nového běhu."""
    if veta["verdict"] == "NEPŘEČTENO":
        return "nepřečteno", veta["reason"][:90]
    role = _role_ve_cteni(veta.get("reading", ""))
    tokeny = _tokeny(veta.get("parse", []))
    if not role or not tokeny:
        return "nerozhodnuto", "čtení nebo rozbor v záznamu chybí"
    # Sponová věta („X byl prozaik") má kořenem JMÉNO, ne sloveso, takže
    # jméno v roli `co` na kořeni je správně. conBond2 na tomhle doplatil
    # obráceně — koreference se na jmenný přísudek vůbec nepodívala.
    spona = any(d == "cop" for _, _, d in tokeny)
    # TRPNÝ ROD: „Ledové šelfy byly spatřeny" — konatel chybí a `co`
    # (patiens) nese `nsubj:pass`. Bez téhle výjimky vypadala každá
    # trpná věta jako špatné čtení a kandidátů skočilo z 12 na 78,
    # ačkoli se změnilo jádro, ne správnost těch čtení.
    trpny = any(d in ("nsubj:pass", "aux:pass", "expl:pass") for _, _, d in tokeny)
    for jmeno, ocekavane in _OCEKAVANE.items():
        if spona:
            ocekavane = (*ocekavane, "root")
        if trpny and jmeno == "co":
            ocekavane = (*ocekavane, "nsubj:pass")
        if trpny and jmeno == "kdo":
            ocekavane = (*ocekavane, "obl:agent")
        hodnota = role.get(jmeno)
        if not hodnota:
            continue
        shody = [d for tvar, _, d in tokeny if _sedi(hodnota, tvar)]
        if not shody:
            continue
        if not any(d.split(":")[0] in [o.split(":")[0] for o in ocekavane]
                   for d in shody):
            return (
                "kandidát na špatné čtení",
                f"role „{jmeno}: {hodnota}“ sedí na token,"
                f" který rozbor označil jako {', '.join(sorted(set(shody)))}",
            )
    if veta["verdict"] == "PTÁ SE":
        return (
            "jádro nedotáhlo",
            f"čtení sedí s rozborem, uvázlo na: {'+'.join(veta['layers'])}",
        )
    return "zapsáno", veta.get("reading", "")[:90]


def main() -> None:
    cesta = vyber(sys.argv[1:])
    zaznam = json.loads(cesta.read_text(encoding="utf-8"))
    print(f"záznam:   {cesta.name}")
    print(f"korpus:   {zaznam.get('korpus', '?')}")
    print(f"jádro:    {zaznam.get('core', '?')}\n")

    vety = [v for d in zaznam.get("documents", []) for v in d["sentences"]]
    pocty: Counter[str] = Counter()
    ukazky: dict[str, list[tuple[str, str, dict]]] = {}
    for veta in vety:
        kategorie, proc = zarad(veta)
        pocty[kategorie] += 1
        ukazky.setdefault(kategorie, [])
        if len(ukazky[kategorie]) < 2:
            ukazky[kategorie].append((veta["text"], proc, veta))

    print(f"{'kategorie':18} {'kolik':>6}   podíl")
    for kategorie, kolik in pocty.most_common():
        print(f"{kategorie:18} {kolik:>6}   {100.0 * kolik / max(len(vety), 1):4.1f} %")

    if "--vse" in sys.argv:
        # Všechny kandidáty na špatné čtení, ať jdou ověřit ručně. Číslo,
        # které si nikdo neprošel, je odhad — a tenhle skript páruje
        # heuristicky, takže odhad být nesmí.
        print("\nVŠICHNI KANDIDÁTI NA ŠPATNÉ ČTENÍ")
        for veta in vety:
            kategorie, proc = zarad(veta)
            if kategorie != "kandidát na špatné čtení":
                continue
            print(f"\n   věta:   {veta['text'][:120]}")
            print(f"   čtení:  {veta.get('reading', '')[:120]}")
            print(f"   proč:   {proc}")

    for kategorie in ("kandidát na špatné čtení", "jádro nedotáhlo", "zapsáno", "nepřečteno"):
        for text, proc, veta in ukazky.get(kategorie, []):
            print(f"\n── {kategorie.upper()}")
            print(f"   věta:   {text[:100]}")
            print(f"   čtení:  {veta.get('reading', '')[:100]}")
            print(f"   rozbor: {' '.join(veta.get('parse', []))[:160]}")
            print(f"   proč:   {proc}")


if __name__ == "__main__":
    main()
