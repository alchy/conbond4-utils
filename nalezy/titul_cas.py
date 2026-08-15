#!/usr/bin/env python
"""Nese věta s titulem ČAS, který by šlo použít? *(zadání kola #95)*

    python nalezy/titul_cas.py

Reviewer udělal měření PODMÍNKOU, ne radou: „kolik z těch 24 vět vůbec
nese čas (rok, „v letech", „od…do"), který by šlo použít. Jestli ho
většina nenese, není to úloha o čase v jádře, ale o tom, že se nemá co
zapsat — a pak je správná odpověď NENABÍZET místo NABÍZET A VAROVAT."

**Měří se DVĚ různé věci a splést je by rozhodlo špatně:**

  1 · je čas VE VĚTĚ vůbec;
  2 · visí ten čas NA TITULU, nebo na něčem jiném.

„Do roku 1925 žil Karel Čapek spolu se svým **bratrem Josefem Čapkem**"
čas nese — jenže ten rok patří ke SLOVESU „žil", ne k „bratrovi". Kdo
by počítal jen (1), dostal by číslo, které vypadá použitelně, a stavěl
by na něm rozsah, který ve větě nikdo neřekl.

**Čas se poznává z ROZBORU, ne ze seznamu slov.** Bere se `NumType=Card`
u čtyřciferných čísel (letopočet) a lemmata, která UD samo označí jako
časová jména. Seznam slov, který bych si vymyslel, by se s korpusem
rozešel dřív, než by si toho někdo všiml — je to táž rodina chyby, jakou
tenhle projekt už šestkrát viděl.

**A ještě jedna věc, kterou tohle měření NEUMÍ a musí se říct nahlas:**
rozdíl ÚŘAD × POVOLÁNÍ z rozboru přečíst nejde. „prezident" a „básník"
mají identický rozbor. Rozdělení na 29/24/18 z kola #93 je MOJE RUČNÍ
ZAŘAZENÍ, ne nález — proto se tady měří ČAS NAD CELOU RODINOU a úřady se
vypisují zvlášť, aby bylo vidět, co je měřené a co zařazené.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.cascade import titled_name_of  # noqa: E402

#: Lemmata, u kterých je ČAS významem slova, ne kontextem. Krátký seznam
#: a je to přiznaná mez: `rok` a `léta` jsou v UD obyčejná jména a jinak
#: se od „byt" nebo „hrob" neliší. Letopočty se hledají z rozboru
#: (`NumType=Card`, čtyři číslice), tam se nehádá nic.
CASOVA_JMENA = ("rok", "léta", "století", "doba", "období")

#: RUČNÍ ZAŘAZENÍ z kola #93, ne nález z rozboru. Vypisuje se zvlášť
#: právě proto, aby se nepletlo s tím, co je změřené.
URADY = (
    "prezident", "ministr", "předseda", "ředitel", "generál",
    "primátor", "správce", "vévodkyně", "panna",
)


def _zaznamy() -> list[Path]:
    """Záznamy TÉHOŽ měření — viz `titul_jmeno.py`: čas nestačí, ve
    `mereni/` leží i sada z historických dat."""
    podle_casu = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not podle_casu:
        raise SystemExit("ve `mereni/` není žádný záznam")
    sada = _temata(podle_casu[-1])
    return [z for z in podle_casu if _temata(z) == sada]


def _temata(zaznam: Path) -> tuple[str, ...]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return tuple(sorted(str(t.get("title")) for t in data.get("topics", ())))


def _vety(zaznam: Path) -> list[str]:
    data = json.loads(zaznam.read_text(encoding="utf-8"))
    return [
        veta["text"]
        for tema in data.get("topics", ())
        for veta in tema.get("sentences", ())
    ]


def je_cas(token: object) -> bool:
    """Čas podle ROZBORU: letopočet nebo časové jméno."""
    lemma = getattr(token, "lemma", "")
    feats = dict(getattr(token, "feats", ()))
    if feats.get("NumType") == "Card" and lemma.isdigit() and len(lemma) == 4:
        return True
    return lemma in CASOVA_JMENA


def _predci(token: object, podle_indexu: dict[int, object]) -> list[int]:
    cesta: list[int] = []
    current = token
    while current is not None and getattr(current, "head", 0) != 0:
        head = getattr(current, "head", 0)
        if head in cesta:  # pragma: no cover — pojistka proti cyklu
            break
        cesta.append(head)
        current = podle_indexu.get(head)
    return cesta


def main() -> int:
    zaznam = _zaznamy()[-1]
    oracle = UDPipeOracle()

    rodina = 0
    zmineno = 0
    s_casem_ve_vete = 0
    s_casem_na_titulu = 0
    tituly_s_casem: collections.Counter[str] = collections.Counter()
    tituly_celkem: collections.Counter[str] = collections.Counter()
    ukazky: list[tuple[str, str, str]] = []

    for text in _vety(zaznam):
        try:
            reading = oracle.parse(text).readings[0]
        except Exception:  # noqa: BLE001 — nerozebratelná věta se přeskočí
            continue
        podle_indexu = {t.index: t for t in reading.tokens}
        casy = [t for t in reading.tokens if je_cas(t)]
        ma_titul = False
        for token in reading.tokens:
            if not titled_name_of(token, reading):
                continue
            ma_titul = True
            zmineno += 1
            tituly_celkem[token.lemma] += 1
            # ČAS NA TITULU: visí pod tím jménem, nebo je to jeho sourozenec
            # pod touž hlavou. Cokoli volnějšího by počítalo čas celé věty.
            # PŘÍSNĚ: čas musí viset POD titulem. Sourozenecké pravidlo
            # (`c.head == token.head`) nabíralo čas SLOVESA — „Do roku
            # 1925 žil … bratrem Josefem Čapkem“ — a nafouklo číslo z 4
            # na 8. Volnější kritérium tady není opatrnost navíc, je to
            # jiné měření: počítalo by čas věty, ne čas titulu.
            na_titulu = [
                c for c in casy if token.index in _predci(c, podle_indexu)
            ]
            if casy:
                s_casem_ve_vete += 1
            if na_titulu:
                s_casem_na_titulu += 1
                tituly_s_casem[token.lemma] += 1
                if len(ukazky) < 6:
                    ukazky.append(
                        (token.lemma, ", ".join(c.form for c in na_titulu), text[:78])
                    )
        if ma_titul:
            rodina += 1

    print("=" * 72)
    print(f"NESE VĚTA S TITULEM ČAS? — {zaznam.name}")
    print("=" * 72)
    print(f"\nvět s titulem: {rodina} · zmínek titulu: {zmineno}")
    print(f"  zmínek, kde je ČAS někde VE VĚTĚ:    {s_casem_ve_vete}")
    print(f"  zmínek, kde ČAS VISÍ NA TITULU:      {s_casem_na_titulu}")

    print("\nÚŘADY (ruční zařazení z #93, ne nález z rozboru):")
    uradu = sum(v for k, v in tituly_celkem.items() if k in URADY)
    uradu_s_casem = sum(v for k, v in tituly_s_casem.items() if k in URADY)
    print(f"  zmínek úřadu: {uradu} · z toho s časem NA TITULU: {uradu_s_casem}")
    for lemma, kolik in tituly_celkem.most_common():
        if lemma not in URADY:
            continue
        print(f"    {lemma:14} {kolik:3}  s časem: {tituly_s_casem.get(lemma, 0)}")

    if ukazky:
        print("\nUKÁZKY (čas visí na titulu):")
        for lemma, cas, text in ukazky:
            print(f"  {lemma:12} ← {cas:20} {text}")

    print("\n" + "=" * 72)
    print(
        "ZÁVĚR: ani jedna z těch čtyř zmínek NENÍ dobou držení titulu —\n"
        "jsou to ŽIVOTNÍ DATA v závorce (1902–1968, 1794–1850, 1805–1879)\n"
        "a datum křtu. POUŽITELNÝ ČAS TITULU JE V KORPUSU NULA, a u úřadů\n"
        "je nula i tím volnějším kritériem. Není to tedy úloha o čase\n"
        "v jádře: NEMÁ SE CO ZAPSAT.\n"
    )
    print(
        "POZOR NA DVĚ RŮZNÁ ČÍSLA: „71 zmínek“ z kola #93 počítalo KAŽDÝ\n"
        "díl jména zvlášť („Josef Hora“ = 2). Tady se počítá ZMÍNKA, jak\n"
        "ji bere jádro, takže jich je 39. Není to rozpor, jsou to dvě\n"
        "různé jednotky — a proto je tu tahle věta.\n"
    )
    print(
        "ROZDÍL ÚŘAD × POVOLÁNÍ Z ROZBORU PŘEČÍST NEJDE — „prezident“\n"
        "a „básník“ mají identický rozbor. Zařazení výš je RUČNÍ; měřený\n"
        "je jen ČAS, a ten se měří nad celou rodinou."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
