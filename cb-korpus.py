#!/usr/bin/env python
"""Historický korpus conBondu2 → KDE PŘESNĚ conBond4 uvázl.

    python cb-korpus.py                       # dokumenty zlaté sady
    python cb-korpus.py --vet 40              # strop vět na dokument
    python cb-korpus.py --dokument pes_domácí
    python cb-korpus.py --dvakrat             # kontrola determinismu
    python cb-korpus.py --etalon              # jen zlatá sada otázek

Krok 4 zadání. Proti `cb-wiki.py` se liší třemi věcmi a každá je záměr:

**Korpus je zmražený.** Wikipedie se mezi dvěma běhy změní a měřicí nula
se pohne; commit v conBondu2 ne. Identita běhu je proto **revize
korpusu × revize jádra × model orákula** a je celá v záznamu.

**Sada se nekrátí na to, co conBond4 zvládne.** Kdo měří jen věty, které
projdou, měří vlastní výběr. Věta, která padne, dostane v záznamu vlastní
řádek s důvodem — to je celý smysl. Strop na dokument existuje kvůli
délce běhu, je **stejný pro všechny dokumenty** (nevybírá podle
obtížnosti) a kolik vět zůstalo neměřených, se **vypíše**; mlčky se
neuřízne nic.

**Tvar vstupu je vlastní osa.** Nadpis a položka seznamu se **označí**,
ne smažou (`cb_utils/tvar.py`) — „tohle nebyla věta" je jiný nález než
„neuměl jsem to přečíst" a ze jmenovatele nezmizí ani jedno.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cb_utils import tvar as tvar_mod
from cb_utils.atribuce import zapis as zapis_atribuci
from cb_utils.triage import OracleError  # noqa: E402  (nastavuje cestu k jádru)
from cb_utils.korpus import Korpus, klic, odstavce, porid
from cb_utils.revize import identity
from cb_utils.triage import (
    CONBOND4,
    Result,
    Verdict,
    nove_sezeni,
    sentences_of,
    triage,
)

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MERENI = HERE / "mereni"

#: Kolik vět na dokument, když se strop nezadá. Není to výběr podle
#: obtížnosti — bere se **od začátku dokumentu** a stejně u všech.
VYCHOZI_STROP = 40


def _dokumenty_zlate_sady(korpus: Korpus) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Dokumenty, ke kterým existuje ruční zlatá sada, a **co nesedlo**.

    Proč zrovna tyhle: `etalon.json` a `conbond.json` jsou **ručně psané
    otázky s očekáváním**, tedy jediné místo, kde je v conBondu2 zapsané,
    co má systém z textu umět. Měřit korpus, ke kterému žádné očekávání
    není, jde taky — ale tohle je ta relevantní sada.

    Páruje se přes `korpus.klic` (předpona zdroje, diakritika, tečky),
    protože doslovnou shodou by ze 32 odkazů sedlo jen 14 a osm textů by
    ze sady **tiše** vypadlo. Co nesedne ani tak, se vrací zvlášť a vypíše
    se — nespojený odkaz je nález, ne důvod k mlčení.
    """
    odkazy: set[str] = set()
    for sada, pole in (("etalon", "dok"), ("conbond", "src")):
        for polozka in korpus.zlata(sada):
            jmeno = polozka.get(pole)
            if jmeno:
                odkazy.add(str(jmeno))
    podle_klice = {klic(jmeno): jmeno for jmeno in korpus.dokumenty()}
    nalezene: set[str] = set()
    nespojene: list[str] = []
    for odkaz in sorted(odkazy):
        # Odkaz smí nést i dva dokumenty („bible_genesis+bible_skutky").
        casti = [c for c in odkaz.split("+") if c]
        sedlo = [podle_klice[klic(c)] for c in casti if klic(c) in podle_klice]
        if sedlo:
            nalezene.update(sedlo)
        else:
            nespojene.append(odkaz)
    return tuple(sorted(nalezene)), tuple(nespojene)


def _zaznam_vety(result: Result, radek: str, tvar: str) -> dict:
    return {
        "text": result.sentence,
        # PŮVODNÍ ŘÁDEK vedle věty, ne místo ní: segmentace je taky
        # předzpracování a musí být vidět, co z čeho vzniklo.
        "radek": radek if radek != result.sentence else "",
        "tvar": tvar,
        "verdict": result.verdict.value,
        # Faseta zvlášť: `ZAPSÁNO · s otázkami` je pořád ZAPSÁNO, ale
        # holé `ZAPSÁNO 46` by u částečných zápisů tvrdilo víc, než platí.
        "stav": result.stav,
        "written_id": result.written_id,
        "program": list(result.program),
        "zapis": list(result.zapis),
        "status": result.status,
        "open_questions": result.open_questions,
        # Seznam, ne jen číslo: dva běhy se pak porovnají položkou po
        # položce a „ubyla jedna otázka, přibyla jiná" není neviditelné.
        "questions": list(result.questions),
        "layers": list(result.layers),
        "sole": result.sole,
        "kind": result.kind,
        "reading": result.reading,
        "reason": result.detail,
        "question": result.question,
        "trace": list(result.trace),
        "parse": list(result.parse),
        "references": list(result.references),
    }


def _tvar_vety(radek: str, result: Result) -> str:
    """Tvar z řádku a z rozboru. Rozbor se čte z `result.parse`, aby se
    nepouštěl znovu — je to `tvar/UPOS/deprel→hlava`."""
    koren = ""
    spona = False
    for polozka in result.parse:
        try:
            _, upos, zbytek = polozka.split("/", 2)
            deprel = zbytek.split("→", 1)[0]
        except ValueError:  # pragma: no cover — rozbor bez tvaru
            continue
        if deprel == "root":
            koren = upos
        if deprel == "cop":
            spona = True
    return tvar_mod.urči(radek, koren, spona).value


def zmer_dokument(
    korpus: Korpus, jmeno: str, oracle, delic, strop: int, *, po_dokumentech: bool = False
) -> tuple[list[Result], list[dict], int]:
    """Jeden dokument. Vrací výsledky, záznamy a **kolik vět zbylo
    neměřených** — ať je strop vidět, ne domýšlený.

    `delic` je orákulum, které umí `segment` — keš nad ním umí jen
    `parse`. Dělič a rozbor jsou schválně **táž služba**: vlastní dělič
    by se s parserem rozešel a rozdíl by se poznal až na výsledcích.
    """
    results: list[Result] = []
    zaznamy: list[dict] = []
    radky = odstavce(korpus.text(jmeno))
    hotovo = 0
    # JEDNO SEZENÍ NA DOKUMENT, nebo čerstvé na každou větu. Rozdíl je
    # celý smysl dokumentového běhu: zájmeno má kam sáhnout jen tehdy,
    # když předchozí věta v sezení zůstala.
    sezeni = nove_sezeni() if po_dokumentech else None
    for poradi, radek in enumerate(radky):
        if strop and len(results) >= strop:
            break
        hotovo = poradi
        try:
            vety = sentences_of(radek, delic)
        except OracleError as error:
            # JEN chyba služby. Širší `except` by tu spolkl i překlep
            # v tomhle souboru a vydával ho za výpadek parseru — a to je
            # přesně ten druh tichého rozdílu, který měření nesmí dělat.
            print(f"    ! segmentace selhala: {str(error)[:80]}")
            continue
        for veta in vety:
            result = triage(veta, oracle, sezeni)
            results.append(result)
            zaznamy.append(_zaznam_vety(result, radek, _tvar_vety(radek, result)))
    else:
        hotovo = len(radky)
    # Zbytek se počítá v ŘÁDCÍCH, ne ve větách: kolik vět v nich je, by
    # se muselo zjistit rozborem, a rozebírat text jen kvůli číslu, které
    # se stejně neměří, znamená platit za nic. Číslo je tedy dolní odhad
    # a je to v něm napsané.
    return results, zaznamy, len(radky) - hotovo


def tabulka(results: list[Result], titulek: str) -> None:
    """Rozklad po vrstvách. `sám` = kolik vět uvázlo JEN na téhle věci."""
    total = len(results)
    if not total:
        return
    hit: Counter[str] = Counter()
    sole: Counter[str] = Counter()
    kinds: Counter[tuple[str, str]] = Counter()
    for result in results:
        for layer in result.layers:
            hit[layer] += 1
        if result.sole:
            sole[result.sole] += 1
            if result.kind:
                kinds[(result.sole, result.kind)] += 1
    print(f"\n{titulek}   (vět {total})")
    print(f"  {'vrstva':18} {'vyskytuje se':>13} {'sám blokuje':>12}")
    for layer, count in hit.most_common():
        alone = sole.get(layer, 0)
        print(
            f"  {layer:18} {count:5} ({100.0 * count / total:4.1f} %)"
            f" {alone:5} ({100.0 * alone / total:4.1f} %)"
        )
        for (name, kind), how_many in sorted(kinds.items()):
            if name == layer:
                print(f"  {'':18} {'':13} {how_many:5}  · {kind}")


#: Značka jádra pro **ztracený člen** — člen věty, který se do čtení
#: vůbec nedostal. Podle měření z kola #8 je to hranice zápisu: otevřená
#: otázka zápis neblokuje, ztracený člen ano (zapsaných se ztrátou 0,
#: tázaných 499).
ZTRATA = "do čtení se nedostalo"


def _druhy(result: Result) -> set[str]:
    return {q.split(":", 1)[0] for q in result.questions}


def _rozpad(results: list[Result], odsazeni: str = "  ") -> None:
    """Podle druhu · na větu · **kolik visí jen na jedné věci**.

    To poslední číslo je to podstatné: říká, co je jedna oprava a co
    rodina. Bez něj se z „44 částečných" ani z „636 tázaných" nepozná,
    jestli je to jedna věc, nebo tolik různých, kolik je vět.
    """
    druhy: Counter[str] = Counter(
        q.split(":", 1)[0] for r in results for q in r.questions
    )
    kombinace: Counter[str] = Counter(
        " + ".join(sorted(_druhy(r))) or "(jádro nic neřeklo)" for r in results
    )
    sam: Counter[str] = Counter(
        next(iter(_druhy(r))) for r in results if len(_druhy(r)) == 1
    )
    print(f"{odsazeni}podle druhu (věta jich může mít víc):")
    for druh, kolik in druhy.most_common():
        print(f"{odsazeni}  {kolik:5}  {druh}")
    print(f"{odsazeni}jen na jedné věci: {sum(sam.values())} z {len(results)}"
          f"  —  " + " · ".join(f"{k} {v}" for k, v in sam.most_common()))
    print(f"{odsazeni}na větu:")
    for kombo, kolik in kombinace.most_common(8):
        print(f"{odsazeni}  {kolik:5}  {kombo}")
    if len(kombinace) > 8:
        print(f"{odsazeni}  … a {len(kombinace) - 8} dalších kombinací")


def tabulka_otevrenych(results: list[Result]) -> None:
    """Na čem visí věty, které se nezapsaly celé.

    Dvě skupiny zvlášť, protože jsou od zápisu **různě daleko**:
    částečný zápis už v bázi je a chybí mu doplnění; `PTÁ SE` v bázi
    není. A uvnitř `PTÁ SE` ještě jednou zvlášť podle ztraceného členu —
    věta bez ztráty je od zápisu nejblíž, protože tu hranici drží
    ztracený člen, ne otevřená otázka.
    """
    castecne = [r for r in results if r.verdict is Verdict.WRITTEN and r.questions]
    if castecne:
        print(f"\nCO CHYBÍ ČÁSTEČNÝM ZÁPISŮM   (vět {len(castecne)})")
        _rozpad(castecne)

    ptaji = [r for r in results if r.verdict is Verdict.ASKS]
    if not ptaji:
        return
    se_ztratou = [r for r in ptaji if any(ZTRATA in q for q in r.questions)]
    bez_ztraty = [r for r in ptaji if r not in se_ztratou]
    print(f"\nNA ČEM VISÍ „PTÁ SE“   (vět {len(ptaji)})")
    _rozpad(ptaji)
    print(f"\n  ze ztraceným členem   {len(se_ztratou):5}"
          f"   — hranice zápisu, tu drží ztráta, ne otázka")
    print(f"  jen otevřená otázka   {len(bez_ztraty):5}"
          f"   — OD ZÁPISU NEJBLÍŽ")
    if bez_ztraty:
        _rozpad(bez_ztraty, odsazeni="    ")


def tabulka_tvaru(zaznamy: list[dict]) -> None:
    """Tvar × stav. **Kříží se, nesčítají.** Nadpis, který se nepřečetl,
    není mezera schopnosti; věta, která se nepřečetla, ano."""
    krizem: Counter[tuple[str, str]] = Counter()
    for z in zaznamy:
        krizem[(z["tvar"], z["stav"])] += 1
    tvary = sorted({t for t, _ in krizem})
    # I tady stav S FASETOU: kdyby se křížová tabulka počítala z holého
    # verdiktu, částečné zápisy by v ní splynuly s úplnými — a je to
    # jedna z mála tabulek, do které se člověk dívá jako první.
    poradi = [
        "ZAPSÁNO · úplně", "ZAPSÁNO · s otázkami",
        *(v.value for v in Verdict if v is not Verdict.WRITTEN),
    ]
    stavy = [s for s in poradi if any(x == s for _, x in krizem)]
    # Sloupec je široký podle NEJDELŠÍHO JMÉNA STAVU, ne podle čísla:
    # „ZAPSÁNO · s otázkami" se do třinácti znaků nevejde a hlavička se
    # slepí do „ZAPSÁNO · úplněZAPSÁNO · s otázkami".
    sirka = max(13, *(len(s) + 2 for s in stavy))
    print(f"\nTVAR VSTUPU × STAV   (vět {len(zaznamy)})")
    print(f"  {'tvar':14}" + "".join(f"{s:>{sirka}}" for s in stavy) + f"{'celkem':>9}")
    for t in tvary:
        radek = "".join(f"{krizem[(t, s)]:>{sirka}}" for s in stavy)
        celkem = sum(krizem[(t, s)] for s in stavy)
        print(f"  {t:14}{radek}{celkem:>9}")


def etalon(korpus: Korpus, oracle) -> dict:
    """Zlatá sada otázek — **celá, včetně `unsure` a `clarify`**.

    Tři režimy z conBondu2 se mapují na to, co conBond4 umí vrátit:

        answer   → má přijít `A` nebo `N` a odpověď má obsahovat `expect`
        unsure   → má přijít `U`; **mlčení je splnění, ne selhání**
        clarify  → má přijít otázka, ne verdikt

    Vyhodnocuje se **podřetězcem**, ne přesnou shodou (conBond2:
    „trvat na hranici úseku znamená měřit tokenizaci, ne odpověď").

    Nic se do báze nezapisuje, takže dnes tu nemůže vyjít nic jiného než
    `U` a nepřečtené otázky. **Je to legitimní výsledek měřicí nuly** —
    a je vidět, kolik z těch `U` je „nevím" a kolik „ani jsem tu otázku
    nepřečetl", což jsou dvě různé věci.
    """
    polozky: list[dict] = []
    for sada, klic in (("etalon", "dok"), ("conbond", "src")):
        for p in korpus.zlata(sada):
            polozky.append(
                {
                    "sada": sada,
                    "q": p["q"],
                    "expect": p.get("expect") or [],
                    "mode": p.get("mode") or "",
                    "kind": p.get("kind") or "",
                    "dok": str(p.get(klic) or ""),
                }
            )
    podle_rezimu: Counter[tuple[str, str]] = Counter()
    zaznamy: list[dict] = []
    for p in polozky:
        result = triage(p["q"], oracle)
        precteno = result.verdict is not Verdict.UNREAD
        vysledek = (
            result.status
            or ("nepřečteno" if not precteno else result.verdict.value)
        )
        # Splnění se posuzuje podle REŽIMU, ne podle jednoho skóre.
        if p["mode"] == "unsure":
            splneno = result.status == "U"
        elif p["mode"] == "clarify":
            splneno = bool(result.question)
        else:
            splneno = result.status in ("A", "N")
        podle_rezimu[(p["mode"] or "bez režimu", vysledek)] += 1
        zaznamy.append(
            {
                **p,
                "vysledek": vysledek,
                "splneno": splneno,
                "question": result.question,
                "reason": result.detail,
                "layers": list(result.layers),
            }
        )
    print(f"\nZLATÁ SADA   (položek {len(zaznamy)})")
    print(f"  {'režim':12} {'výsledek':14} {'kolik':>6}")
    for (rezim, vysledek), kolik in sorted(podle_rezimu.items()):
        print(f"  {rezim:12} {vysledek:14} {kolik:>6}")
    for rezim in ("answer", "unsure", "clarify"):
        z = [x for x in zaznamy if x["mode"] == rezim]
        if z:
            splneno = sum(1 for x in z if x["splneno"])
            print(f"  {rezim:12} splněno {splneno} z {len(z)}")
    return {"polozky": zaznamy}


def pockej_na_ciste(minut: int) -> str:
    """Počká, až bude jádro na commitu **bez rozdělané práce**.

    Běh nad rozdělaným stromem není měření, je to odhad s razítkem:
    čísla nepatří žádnému commitu, takže se k nim nikdo nemůže vrátit.
    Dokud to hlídala jen kázeň, procházelo to — proto to hlídá nástroj.

    Vrací identitu, nad kterou se smí měřit. Když se nedočká, **nic se
    nezměří**: prázdný záznam je lepší než záznam, který se tváří jako
    revize a není jí.
    """
    konec = time.monotonic() + minut * 60
    hlaseno = ""
    while True:
        jadro, _ = identity(CONBOND4)
        if "+dirty:" not in jadro:
            return jadro
        if time.monotonic() > konec:
            raise SystemExit(
                f"jádro je {minut} minut rozdělané ({jadro}) — neměřím.\n"
                f"Běh nad rozdělaným stromem by vydal čísla, která nepatří "
                f"žádnému commitu; radši nic než razítko, které neplatí."
            )
        if jadro != hlaseno:
            hlaseno = jadro
            zbyva = (konec - time.monotonic()) / 60
            print(f"  čekám na čisté jádro ({zbyva:.0f} min): {jadro}")
        time.sleep(20)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dokument", action="append", default=[],
                        help="jméno dokumentu; opakovatelné")
    parser.add_argument("--vet", type=int, default=VYCHOZI_STROP,
                        help="strop vět na dokument, 0 = bez stropu")
    parser.add_argument("--revize", default="",
                        help="pin revize korpusu conBond2")
    parser.add_argument("--json", default="", help="záznam měření do souboru")
    parser.add_argument("--dvakrat", action="store_true",
                        help="spustit dvakrát a porovnat počty")
    parser.add_argument("--etalon", action="store_true",
                        help="jen zlatá sada otázek")
    parser.add_argument("--po-dokumentech", action="store_true",
                        help="jedno sezení na dokument místo na větu — "
                             "zájmeno pak má kam sáhnout")
    parser.add_argument("--nad-cistym", type=int, default=0, metavar="MINUT",
                        help="počkat, až bude jádro na commitu bez rozdělané "
                             "práce, a běh zopakovat, když se strom během "
                             "měření změní")
    parser.add_argument("--bez-etalonu", action="store_true",
                        help="vynechat zlatou sadu")
    args = parser.parse_args()

    from core_semantics.oracle import CachingOracle, UDPipeOracle

    zdroj = UDPipeOracle()
    # Keš je tu kvůli tomu, že se každá věta rozebírá dvakrát: jednou
    # kaskádou uvnitř sezení a jednou kvůli rozboru do záznamu. Na
    # výsledek nemá vliv — klíčem je provenience i text.
    oracle = CachingOracle(zdroj)

    if args.nad_cistym:
        pockej_na_ciste(args.nad_cistym)

    korpus = porid(DATA / "conBond2", revize=args.revize)
    ze_zlate, nespojene = _dokumenty_zlate_sady(korpus)
    jmena = tuple(args.dokument) or ze_zlate

    # Hodnota, která se porovnává, a poznámka pro člověka jsou DVĚ POLE.
    # Dokud se počet nesledovaných souborů držel uvnitř revize, hlásil
    # `core_na_konci` změnu jádra kvůli jednomu `__pycache__` (W‑78).
    jadro, jadro_pozn = identity(CONBOND4)
    mereni, mereni_pozn = identity(HERE)
    record: dict = {
        "korpus": korpus.provenance,
        "oracle": zdroj.provenance,
        "core": jadro,
        "core_poznamka": jadro_pozn,
        "utils": mereni,
        "utils_poznamka": mereni_pozn,
        "strop_vet_na_dokument": args.vet,
        # Režim sezení patří do identity běhu stejně jako revize: „jedno
        # sezení na dokument" a „čerstvé na každou větu" měří něco
        # jiného a jejich čísla se nesmějí porovnávat jako dva běhy
        # téhož.
        "rezim_sezeni": "dokument" if args.po_dokumentech else "věta",
        "documents": [],
    }
    print(f"korpus:   {record['korpus']}")
    print(f"orákulum: {record['oracle']}")
    print(f"jádro:    {record['core']} {jadro_pozn}".rstrip())
    print(f"měření:   {record['utils']} {mereni_pozn}".rstrip())
    print(f"dokumentů: {len(jmena)}   strop {args.vet or 'bez stropu'}")
    if nespojene and not args.dokument:
        # Nespojený odkaz se NEZAMLČUJE. Zlatá sada odkazuje na text,
        # který v tomhle korpusu není — je to nález o sadě, ne o systému.
        print(f"  odkazy zlaté sady bez dokumentu: {len(nespojene)}"
              f" — {', '.join(nespojene)}")
    record["gold_bez_dokumentu"] = list(nespojene)
    print()

    everything: list[Result] = []
    vsechny_zaznamy: list[dict] = []
    total: Counter[str] = Counter()
    neizmereno = 0

    if not args.etalon:
        for jmeno in jmena:
            zacatek = time.perf_counter()
            results, zaznamy, zbylo = zmer_dokument(korpus, jmeno, oracle, zdroj, args.vet,
                                     po_dokumentech=args.po_dokumentech)
            everything.extend(results)
            vsechny_zaznamy.extend(zaznamy)
            neizmereno += zbylo
            counts = Counter(r.stav for r in results)
            total.update(counts)
            konec = time.perf_counter() - zacatek
            zbytek = f" · NEMĚŘENO {zbylo} řádků" if zbylo else ""
            print(f"  {jmeno:26} {len(results):4} vět  "
                  + " · ".join(f"{k} {v}" for k, v in counts.most_common())
                  + f"{zbytek}   ({konec:.0f} s)")
            record["documents"].append(
                {"name": jmeno, "measured": len(results), "unmeasured": zbylo,
                 "sentences": zaznamy}
            )

        print("\n" + "=" * 72)
        print("CELKEM  " + " · ".join(f"{k} {v}" for k, v in total.most_common()))
        if neizmereno:
            print(f"  NEMĚŘENO {neizmereno} řádků nad stropem {args.vet} vět"
                  f" na dokument — strop je stejný pro všechny dokumenty"
                  f" a bere se od začátku, nevybírá podle obtížnosti")
        tabulka(everything, "ROZKLAD PŘES VŠECHNY DOKUMENTY")
        tabulka_otevrenych(everything)
        tabulka_tvaru(vsechny_zaznamy)
        print("=" * 72)

    if not args.bez_etalonu:
        record["etalon"] = etalon(korpus, oracle)

    record["counts"] = dict(total)
    record["unmeasured"] = neizmereno
    # REVIZE JÁDRA ZNOVU, NA KONCI. Builder jádra pracuje souběžně a
    # pracovní strom se během běhu mění; záznam, který stampuje jen
    # začátek, by pak tvrdil identitu, kterou půlka měření neměla.
    # Poznat to jde jen tak, že se stav zjistí dvakrát.
    record["core_na_konci"], record["core_poznamka_na_konci"] = identity(CONBOND4)
    if record["core_na_konci"] != record["core"]:
        print("\n  POZOR: jádro se BĚHEM měření změnilo —"
              " záznam není nad jedním stavem kódu")
        print(f"    začátek: {record['core']}")
        print(f"    konec:   {record['core_na_konci']}")
        if args.nad_cistym:
            # Se `--nad-cistym` se takový záznam NEUKLÁDÁ. Uložit ho a
            # připsat varování už jsme zkusili: soubor pak leží v repu,
            # kreslí se z něj mapa a varování si nikdo nepřečte.
            raise SystemExit(
                "  záznam se neukládá — pusť to znovu, až bude jádro stát"
            )

    if args.dvakrat:
        print("\nKONTROLA DETERMINISMU — druhý běh nad touž revizí\n")
        druhy: Counter[str] = Counter()
        druhe_vrstvy: Counter[str] = Counter()
        for jmeno in jmena:
            results, _, _ = zmer_dokument(korpus, jmeno, oracle, zdroj, args.vet,
                                     po_dokumentech=args.po_dokumentech)
            druhy.update(r.stav for r in results)
            for r in results:
                for layer in r.layers:
                    druhe_vrstvy[layer] += 1
        prvni_vrstvy: Counter[str] = Counter()
        for r in everything:
            for layer in r.layers:
                prvni_vrstvy[layer] += 1
        shoda = druhy == total and druhe_vrstvy == prvni_vrstvy
        print(f"  stavy   {'SHODA' if druhy == total else 'ROZDÍL'}: {dict(druhy)}")
        print(f"  vrstvy  {'SHODA' if druhe_vrstvy == prvni_vrstvy else 'ROZDÍL'}")
        if not shoda:
            print(f"    běh 1: {dict(prvni_vrstvy)}")
            print(f"    běh 2: {dict(druhe_vrstvy)}")
        record["determinismus"] = {
            "shoda": shoda,
            "beh1": dict(total),
            "beh2": dict(druhy),
        }

    if args.json:
        cil = Path(args.json)
        cil.parent.mkdir(parents=True, exist_ok=True)
        cil.write_text(
            json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"\nzáznam: {cil}")
        # ATRIBUCE SE PŘEPÍŠE HNED TEĎ, ne někdy potom. Záznam nese cizí
        # text pod CC BY-SA a povinnost uvést zdroj vzniká zápisem, ne
        # rozhodnutím ji doplnit. Generuje se ze VŠECH záznamů ve složce,
        # takže nemůže zestárnout tím, že někdo přidá dokument.
        licence = zapis_atribuci(cil.parent, korpus.provenance)
        print(f"atribuce: {licence}")


if __name__ == "__main__":
    main()
