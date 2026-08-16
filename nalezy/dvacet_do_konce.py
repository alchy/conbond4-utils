#!/usr/bin/env python
"""Dvacet korpusových vět DOTAŽENÝCH DO KONCE *(zadání kola #128)*.

    python nalezy/dvacet_do_konce.py

Šest kol se stavělo, aby se systém PTAL poctivě. Nikdo ale nezměřil, co
se stane, když se na ty otázky ODPOVÍDÁ AŽ DO KONCE — korpus má jednu
zapsanou větu z 238 a 58 vět čeká na rozhodnutí, které nikdo nedal.

**Tahle sonda odpovídá, dokud se věta nezapíše, nebo dokud nezbude
otázka, na kterou pravdivá odpověď NEEXISTUJE.** Odpovídá se
MECHANICKY a podle pravidel, která jsou tady napsaná — ne podle toho,
co by u které věty „vyšlo":

  · `→@` na tvar role dostane jméno podle PÁDU A PŘEDLOŽKY, ne podle
    věty; když pravdivé jméno v predikaci UŽ NĚKDO DRŽÍ, je to konec
    (odpověď by byla nepravdivá — W‑73);
  · `→∀` odpovídá `∃`, protože encyklopedický text mluví o jednotlivém
    případu, ne o všech;
  · `→&` odpovídá „každý zvlášť" JEN u sloves, kde to platí; jinak
    „dohromady";
  · na otázku po ODKAZU se odpovídá jen tehdy, když kandidát v předchozí
    větě opravdu stojí.

Věta, u které by odpověď znamenala přilepit tvrzení, které v ní není,
se ZASTAVÍ a zapíše se do seznamu (b) — ten je z celého měření
nejcennější.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

_KORPUS = Path(__file__).resolve().parent.parent / "mereni"
_JADRO = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(_JADRO) not in sys.path:
    sys.path.insert(0, str(_JADRO))

from core_semantics.ast import Entity, QueryStatus  # noqa: E402
from core_semantics.cascade import (  # noqa: E402
    AWAITING_QUANTIFIER,
    CANONICAL_ROLES,
    surface_roles,
)
from core_semantics.engine import Engine  # noqa: E402
from core_semantics.lexicon import Operation  # noqa: E402
from core_semantics.oracle import UDPipeOracle  # noqa: E402
from core_semantics.session import (  # noqa: E402
    Session,
    TurnResult,
    answers_quantifier,
    decides_sharing,
    names_role,
)
from core_semantics.tests import golden  # noqa: E402

#: Kolik vět a kolik tahů na větu, než se to prohlásí za nekonvergující.
KOLIK_VET = 20
STROP_TAHU = 40

#: Jméno role podle TVARU. Je to slovník měřicí sondy, ne jádra —
#: odpovídá za člověka, a proto musí být vidět, podle čeho odpovídá.
JMENA: dict[str, str] = {
    "v+Loc": "kde",
    "v+Loc/Geo": "kde",
    "v+Loc/rok": "kdy",
    "na+Loc": "kde",
    "na+Loc/Geo": "kde",
    "do+Gen": "kam",
    "z+Gen": "odkud",
    "ze+Gen": "odkud",
    "od+Gen": "odkud",
    "k+Dat": "kam",
    "ke+Dat": "kam",
    "po+Loc": "kdy",
    "s+Ins": "jak",
    "se+Ins": "jak",
    "za+Gen": "kdy",
    "podle+Gen": "jak",
    "Gen": "jak",
    "Dat": "komu",
    "Ins": "čím",
    "Ins:arg": "čím",
}

#: Slovesa, u kterých souřadné členy platí o KAŽDÉM ZVLÁŠŤ. Krátký
#: a schválně konzervativní: u čeho si nejsem jistý, odpovídám
#: „dohromady", protože to tvrdí míň.
ZVLAST = ("zahrnovat", "být", "patřit", "psát", "publikovat", "vydávat")


def _jmeno_role(tvar: str, obsazena: set[str]) -> str | None:
    """Pravdivé jméno role, nebo `None`, když ho už někdo drží."""
    jmeno = JMENA.get(tvar)
    if jmeno is None:
        jmeno = JMENA.get(tvar.split("/")[0])
    if jmeno is None or jmeno in obsazena:
        return None
    return jmeno


def _krok(session: Session, result: TurnResult, text: str, oracle: UDPipeOracle) -> tuple[TurnResult | None, str]:
    """Jeden tah odpovědi. Vrací nový výsledek a důvod, když se zastaví."""
    predication = result.predication
    if predication is None:
        return None, "NEPŘEČTENO — věta se nedá přečíst"
    if predication.pending_name:
        return None, "JMÉNO NEÚPLNÉ — díl jména se složit nedá (W‑75)"
    obsazena = {r.name for r in predication.roles}
    for tvar in surface_roles(predication):
        jmeno = _jmeno_role(tvar, obsazena)
        if jmeno is None:
            return None, f"ROLE „{tvar}“ — pravdivé jméno je obsazené nebo neznám"
        return (
            session.play(
                names_role(f"Je to {jmeno}.", oracle.parse(text).readings[0], tvar, jmeno)
            ),
            "",
        )
    if predication.pending_share:
        role, tvar, _ = predication.pending_share[0]
        zvlast = predication.predicate in ZVLAST
        return (
            session.play(
                decides_sharing(
                    "Každý zvlášť." if zvlast else "Dohromady.",
                    predication,
                    oracle.parse(text).readings[0],
                    distributive=zvlast,
                )
            ),
            "",
        )
    # KVANTIFIKÁTOR SE POZNÁ PODLE `pending`, NE PODLE `awaiting`.
    # První verze téhle sondy se ptala jen na `AWAITING_QUANTIFIER`
    # a šest vět kvůli tomu ohlásila jako „není na co odpovědět“,
    # ačkoli jádro otázku POLOŽILO. Byla to vada NÁSTROJE, ne jádra —
    # a je to potřetí, co měřicí vrstva ukázala jiné číslo než skutek.
    for role in predication.roles:
        if role.pending is not None and role.quantifier is None:
            return (
                session.play(
                    answers_quantifier("Některého.", predication, role.pending, Operation.EXISTS)
                ),
                "",
            )
    # ZTRACENÝ ČLEN SE ČTE Z HLÁŠENÍ, NE Z `turn.lost` PŘEDCHOZÍHO TAHU.
    # Tah odpovědi nese vlastní `lost`, takže po `→∀` vypadala věta jako
    # „není na co odpovědět“, ačkoli v hlášení stálo `[ZAHOZENO: …]`.
    # Je to táž past jako B‑25, jen v měřicí vrstvě.
    zahozene = [line for line in result.lines if "ZAHOZENO" in line]
    if zahozene:
        return None, "ZTRACENÝ ČLEN — role pro něj v té větě není: " + zahozene[0][:96]
    if result.statement_id is None:
        return None, "NEZAPSÁNO a už není na co odpovědět"
    return None, ""


def main() -> int:
    zaznamy = sorted(_KORPUS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    data = json.loads(zaznamy[-1].read_text(encoding="utf-8"))
    vety = [
        s["text"]
        for t in data["topics"]
        for s in t["sentences"]
        if s["verdict"] == "PTÁ SE"
    ][:KOLIK_VET]

    oracle = UDPipeOracle()
    zapsane: list[tuple[str, int, str, tuple[str, ...]]] = []
    zastavene: list[tuple[str, str]] = []

    print("=" * 74)
    print(f"DVACET VĚT DO KONCE — záznam {zaznamy[-1].name}")
    print("=" * 74)

    for text in vety:
        session = Session(lexicon=golden.golden_lexicon())
        try:
            result: TurnResult | None = session.utter(text, oracle)
        except Exception as exc:  # pragma: no cover — měřicí sonda
            zastavene.append((text, f"CHYBA {type(exc).__name__}"))
            continue
        tahu = 1
        duvod = ""
        while result is not None and tahu < STROP_TAHU:
            if result.statement_id is not None:
                break
            dalsi, duvod = _krok(session, result, text, oracle)
            if dalsi is None:
                result = None if duvod else result
                break
            result = dalsi
            tahu += 1
        if result is not None and result.statement_id is not None:
            zapsane.append((text, tahu, str(result.predication), result.statements))
            print(f"\n✓ {text[:66]}\n    tahů {tahu} · {result.predication}")
            print(f"    zapsáno: {', '.join(result.statements)}")
        else:
            zastavene.append((text, duvod or "strop tahů"))
            print(f"\n✗ {text[:66]}\n    {duvod or 'strop tahů'}")

    print("\n" + "=" * 74)
    print(f"(a) ZAPSÁNO {len(zapsane)} z {len(vety)}")
    if zapsane:
        tahy = [t for _, t, _, _ in zapsane]
        print(f"    tahů: medián {statistics.median(tahy):.0f} · nejhorší {max(tahy)}")
    print(f"\n(b) ZASTAVENO {len(zastavene)} — a TOHLE JE TEN SEZNAM:")
    for text, duvod in zastavene:
        print(f"    · {duvod}\n        {text[:64]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
