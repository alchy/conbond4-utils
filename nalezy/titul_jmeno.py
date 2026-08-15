#!/usr/bin/env python
"""Kolika vět se W‑53 týkala a co se s nimi stalo (zadání kola #92).

    python nalezy/titul_jmeno.py

Reviewer žádal dvě čísla, ne jedno: **kolika vět se to týkalo** a **jestli
některá přešla ze ZAPSÁNO do PTÁ SE** — s tím, že takový přechod se má
pojmenovat jako ZLEPŠENÍ, i když číslo klesne.

**Proč zrovna takhle.** Skript hledá stavbu v ROZBORU (`flat` s `upos`
`PROPN` pod `NOUN`), ne v povrchu věty. Kdyby se hledalo podle slov,
měřil by se seznam titulů, který někdo napsal — a ten by se s korpusem
rozešel dřív, než by si toho někdo všiml. Zásah do jádra to nedělá a
dělat nesmí; rozbor bere z téže služby, kterou používá jádro.

**Nejnovější záznam podle ČASU, ne podle abecedy** — viz `role_rozbor.py`:
tam mě právě abeceda poslala číst starší soubor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.oracle import UDPipeOracle  # noqa: E402

#: Hrana, která z titulu a jména dělá JEDNU ZMÍNKU. `nmod` („Město
#: **Praha**") sem NEPATŘÍ: to je samostatný přívlastek a W‑53 se ho
#: nedotýká. Rozdíl je v rozboru, ne ve stráži — proto se čte odtud.
JEDNA_ZMINKA = ("flat",)


def _temata(zaznam: Path) -> tuple[str, ...]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return tuple(sorted(str(t.get("title")) for t in data.get("topics", ())))


def _zaznamy() -> list[Path]:
    """Záznamy TÉHOŽ MĚŘENÍ, seřazené podle času.

    **Čas nestačí a stálo mě to jedno chybné hlášení.** Ve `mereni/`
    přibyl záznam z jiné sady (historická data conBond2/3) a „poslední
    dva podle času“ na něj sáhly: srovnávaly se dva různé korpusy, takže
    každá věta vyšla jako ZMĚNA a rozdíl 32/32 vypadal jako výsledek.
    Je to potřetí táž rodina chyby — kategorie vybraná podle něčeho, co
    o ní nic neříká (nejdřív abeceda, pak čas).

    Filtruje se proto podle TÉMAT: srovnávat jde jen měření nad touž
    sadou. Kdyby se sada vědomě změnila, tenhle skript raději nenajde
    dvojici, než aby ohlásil rozdíl mezi jablkem a hruškou.
    """
    podle_casu = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not podle_casu:
        return []
    sada = _temata(podle_casu[-1])
    return [z for z in podle_casu if _temata(z) == sada]


def _stavy(zaznam: Path) -> dict[str, dict[str, object]]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return {
        veta["text"]: veta
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
    }


def _revize(zaznam: Path) -> str:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return str(data.get("core", "?")).split(" ")[0]


def ma_titul(oracle: UDPipeOracle, text: str) -> list[str]:
    """Vrátí `titul + jméno` pro každou takovou zmínku ve větě."""
    try:
        reading = oracle.parse(text).readings[0]
    except Exception:  # noqa: BLE001 — nerozebratelná věta se přeskočí
        return []
    podle_indexu = {t.index: t for t in reading.tokens}
    nalezy: list[str] = []
    for token in reading.tokens:
        if token.upos != "NOUN":
            continue
        jmena = [
            t
            for t in reading.tokens
            if t.head == token.index
            and t.deprel.split(":")[0] in JEDNA_ZMINKA
            and t.upos == "PROPN"
        ]
        if jmena:
            nalezy.append(
                token.form + " " + " ".join(t.form for t in sorted(jmena, key=lambda x: x.index))
            )
    del podle_indexu
    return nalezy


def main() -> int:
    zaznamy = _zaznamy()
    if len(zaznamy) < 2:
        raise SystemExit("potřebuju dva záznamy, abych měl co srovnat")
    stary, novy = zaznamy[-2], zaznamy[-1]

    pred, po = _stavy(stary), _stavy(novy)
    oracle = UDPipeOracle()

    print("=" * 72)
    print(f"W‑53 NA KORPUSU   {_revize(stary)} → {_revize(novy)}")
    print("=" * 72)

    dotcene: list[tuple[str, list[str], str, str]] = []
    for text in po:
        tituly = ma_titul(oracle, text)
        if not tituly:
            continue
        dotcene.append(
            (
                text,
                tituly,
                str(pred.get(text, {}).get("verdict", "—")),
                str(po[text].get("verdict", "—")),
            )
        )

    print(f"\nVĚT SE STAVBOU „titul + jméno“ (`flat` PROPN pod NOUN): {len(dotcene)}")
    print(f"z celkem {len(po)} vět korpusu\n")

    zmeny = [d for d in dotcene if d[2] != d[3]]
    for text, tituly, a, b in dotcene:
        znak = "  ← ZMĚNA" if a != b else ""
        print(f"  {a:12} → {b:12}  {' · '.join(tituly)}{znak}")
        if a != b:
            print(f"      {text[:92]}")

    print(f"\nZMĚNILO STAV: {len(zmeny)}")
    zlepseni = [d for d in zmeny if d[2] == "ZAPSÁNO" and d[3] == "PTÁ SE"]
    # Rozklad stavů uvnitř rodiny — bez něj by „0 změn“ mohlo znamenat
    # i „všechny byly odjakživa NEPŘEČTENO“, což je docela jiná zpráva.
    import collections
    print("\nSTAVY UVNITŘ RODINY:")
    for stav, kolik in collections.Counter(d[3] for d in dotcene).most_common():
        print(f"  {stav:14} {kolik}")
    if zlepseni:
        print(
            f"\nZ TOHO ZAPSÁNO → PTÁ SE: {len(zlepseni)} — a je to ZLEPŠENÍ,\n"
            "i když číslo `ZAPSÁNO` klesne: dřív se zapsal výrok o VŠECH\n"
            "nositelích titulu, teď se systém ptá. Zapsaná nepravda je\n"
            "dražší než přiznaná neznalost."
        )

    # CELKOVÝ VERDIKT přes celý korpus, ne jen přes dotčenou rodinu:
    # oprava mohla něco rozbít jinde a to by v rodinové tabulce nebylo
    # vidět vůbec.
    jinde = [
        t
        for t in po
        if t in pred
        and pred[t].get("verdict") != po[t].get("verdict")
        and t not in {d[0] for d in dotcene}
    ]
    print(f"\nZMĚNY MIMO TUHLE RODINU: {len(jinde)}")
    for t in jinde[:10]:
        print(f"  {pred[t].get('verdict')} → {po[t].get('verdict')}  {t[:80]}")

    # ZMĚNA ČTENÍ, NE VERDIKTU. Tohle je ta lekce z W‑43: oprava, která
    # mění TVAR VÝROKU, je ve verdiktu NEVIDITELNÁ — věta se ptala dřív
    # a ptá se pořád, jen se ptá o někom jiném. Kdyby se hlásil jen
    # verdikt, vyšlo by z celého kola „0“ a vypadalo by to, že se
    # nestalo nic.
    # NABÍDKA (W‑55). Třetí patro měření, a bez něj by tohle kolo vyšlo
    # jako nula: W‑55 nemění ani verdikt, ani čtení — mění to, CO SYSTÉM
    # O VĚTĚ ŘEKNE.
    #
    # ČTE SE Z KASKÁDY, NE ZE ZÁZNAMU, a je to nutné: `cb-wiki.py` ukládá
    # `reason` zkrácený na ~160 znaků, takže u vět s dlouhou otázkou se
    # nabídka do záznamu vůbec nevejde. Ze záznamu by vyšlo 2, z kaskády
    # vychází 13 — a to první číslo by neměřilo jádro, ale délku pole.
    from core_semantics.session import Session
    from core_semantics.tests import golden

    print("\nNABÍDKA „titul tvrdí“ (čteno z kaskády, ne ze záznamu):")
    s_nabidka = []
    for text in po:
        session = Session(lexicon=golden.golden_lexicon())
        try:
            vysledek = session.utter(text, oracle)
        except Exception:  # noqa: BLE001 — nerozebratelná věta se přeskočí
            continue
        if vysledek.question and "členství vedle věty" in vysledek.question:
            s_nabidka.append(text)
    print(f"  vět, u kterých systém OHLÁSÍ tvrzení titulu: {len(s_nabidka)}")
    print(f"  z toho uvnitř rodiny: {len([t for t in s_nabidka if t in {d[0] for d in dotcene}])}")

    print("\nZMĚNA ČTENÍ (ne verdiktu):")
    zmena_cteni = [
        d
        for d in dotcene
        if d[0] in pred and pred[d[0]].get("reading") != po[d[0]].get("reading")
    ]
    print(f"  vět, kterým se ZMĚNIL PŘEČTENÝ VÝROK: {len(zmena_cteni)} z {len(dotcene)}")
    for text, tituly, _, _ in zmena_cteni:
        print(f"\n  · {' · '.join(tituly)}")
        print(f"    {text[:92]}")
        print(f"    PŘED: {str(pred[text].get('reading'))[:110]}")
        print(f"    PO:   {str(po[text].get('reading'))[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
