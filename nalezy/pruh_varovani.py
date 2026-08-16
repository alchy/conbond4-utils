#!/usr/bin/env python
"""Zkouška na červený pruh v mapě — v OBOU směrech.

    python nalezy/pruh_varovani.py

Reviewer ověřil pruh jen **negativně**: v čistém běhu správně chybí.
To ale neříká, že se objeví, když má — a varování, které se neobjeví,
je horší než žádné, protože se na něj spoléhá.

Zkouší se proto čtyři případy nad **vymyšlenými záznamy**, ne nad
během: čistý (pruh nesmí být) a tři různé důvody, proč běh není
k zopakování (pruh musí být a musí říct který).

Vymyšlené záznamy jsou tu záměr. Kdyby zkouška čekala, až bude jádro
zrovna rozdělané, nešlo by ji pustit na požádání — a co nejde pustit
na požádání, se přestane pouštět.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("cb_html", HERE.parent / "cb-html.py")
assert _spec and _spec.loader
cb_html = importlib.util.module_from_spec(_spec)
# `cb-html.py` si při načtení přebalí `sys.stdout`. Vlastní přebalení
# proto až POTOM — jinak se to moje zahodí, zavře pod sebou buffer
# a první `print` spadne na „I/O operation on closed file".
_spec.loader.exec_module(cb_html)

# `reconfigure`, ne přebalení: `cb-html.py` si `sys.stdout` přebalí samo
# a druhý wrapper nad týmž bufferem skončí tak, že si ty dva pod sebou
# ten buffer zavřou („I/O operation on closed file").
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZAKLAD = {
    "korpus": "github.com/alchy/conBond2@418d7f7",
    "oracle": "udpipe2 model=test",
    "utils": "aaaaaaa 2026-08-16 10:00 měřicí vrstva",
    "core": "bbbbbbb 2026-08-16 10:00 jádro",
    "core_na_konci": "bbbbbbb 2026-08-16 10:00 jádro",
    "documents": [
        {
            "name": "zkouška",
            "sentences": [
                {
                    "text": "Petr je v Praze.",
                    "verdict": "PTÁ SE",
                    "questions": ["role: Nevím, co znamená „v+Loc“?"],
                    "open_questions": 1,
                    "layers": ["role"],
                    "sole": "role",
                    "tvar": "věta",
                    "reading": "◐ přečteno",
                    "trace": [],
                    "parse": [],
                    "reason": "",
                }
            ],
        }
    ],
}

PRIPADY: tuple[tuple[str, dict, str], ...] = (
    ("čistý běh", {}, ""),
    (
        "jádro rozdělané",
        {"core": "bbbbbbb 2026-08-16 10:00 jádro +dirty:1234abcd",
         "core_na_konci": "bbbbbbb 2026-08-16 10:00 jádro +dirty:1234abcd"},
        "rozdělané",
    ),
    (
        "jádro se během běhu změnilo",
        {"core_na_konci": "ccccccc 2026-08-16 10:30 jiné jádro"},
        "během běhu změnilo",
    ),
    (
        "měřicí vrstva rozdělaná",
        {"utils": "aaaaaaa 2026-08-16 10:00 měřicí vrstva +dirty:99887766"},
        "měřicí vrstva",
    ),
)


def main() -> None:
    spatne = 0
    for jmeno, zmena, ceka in PRIPADY:
        zaznam = {**ZAKLAD, **zmena}
        stranka = cb_html.postav(zaznam, Path("vymyšleno.json"))
        ma_pruh = "Tenhle běh nejde zopakovat" in stranka
        sedi = (ma_pruh and ceka in stranka) if ceka else not ma_pruh
        spatne += not sedi
        print(f"  {'✓' if sedi else '✗'} {jmeno:32}"
              f" pruh {'je' if ma_pruh else 'není':5}"
              f" {'(čekáno: ' + (ceka or 'žádný') + ')'}")
        if not sedi and ceka:
            print("      pruh chybí nebo neříká důvod — varování, které se"
                  " neobjeví, je horší než žádné")

    print(f"\n  PORUŠENÍ: {spatne}"
          f"   {'— zkouška drží' if not spatne else '— NEDRŽÍ'}")
    sys.exit(1 if spatne else 0)


if __name__ == "__main__":
    main()
