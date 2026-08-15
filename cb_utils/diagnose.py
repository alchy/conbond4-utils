"""Ve KTERÉ VRSTVĚ věta uvázla — čteno z toho, co systém sám řekl.

Zásada, na které tenhle modul stojí: **nic se nehádá z povrchu věty.**
Vrstva se určuje ze stopy a z otázky, kterou conBond4 vypsal, protože
ten jediný ví, kde se zastavil. Klasifikátor, který by se díval na text
a odhadoval „tohle bude koreference", by měřil sám sebe.

Vrstvy jsou úmyslně ty, které jmenuje zadání, a **nesmí se slévat**:
každá odpovídá jinému místu v architektuře a jiné opravě.

    segmentace          text se nerozpadl na věty tak, jak parser čeká
    morfologie          tvrdé patro (shoda, pádová mřížka) zahodilo čtení
    rozbor              0 čtení a systém neumí říct proč
    koreference         odkaz na něco mimo větu (on, jeho, ten, určitost)
    role                povrchový tvar bez pojmenované role
    kolize_rolí         dvě určení téhož tvaru na jednom jménu role
    kvantifikace        neví se, o kom to platí (∀ / ∃ / ·)
    konstrukce          neví se, JAKÝ vztah věta tvrdí
    uzavření            návrh na lokální uzavření světa (čeká na člověka)
    zápis               čtení bylo, zápis se vědomě odmítl
    služba              parser nebo síť selhaly

`sole_blocker` je to nejcennější číslo: kolik vět uvázlo **jen na téhle
jediné vrstvě**. Věta s jednou otevřenou věcí ukazuje přesnou hranici
schopnosti; věta se sedmi říká jen to, že je složitá.
"""

from __future__ import annotations

from dataclasses import dataclass

#: (jméno vrstvy, značky ve stopě, značky v otázce)
_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("koreference", ("[URČITOST:",), ("Na koho odkazuje", "Zájmena zatím neumím",
                                      "A na koho odkazuje", "O kterém")),
    ("kolize_rolí", ("[KOLIZE:",), ()),
    ("role", ("[CHYBÍ: co znamená role",), ("Nevím, jakou roli hraje",
                                            "je to tvar, ne význam")),
    ("kvantifikace", ("[CHYBÍ: kvantifikátor", "[NEZAKOTVENO:"),
     ("Nevím, o kom to platí",)),
    ("konstrukce", ("[CHYBÍ: co ta stavba tvrdí",),
     ("Co ta věta tvrdí o vztahu",)),
    ("uzavření", ("[UZAVŘENÍ SVĚTA:",), ("prohlásit za UZAVŘENOU",)),
)


@dataclass(frozen=True, slots=True)
class Diagnosis:
    layers: tuple[str, ...]
    reason: str

    @property
    def sole(self) -> str:
        """Jediná vrstva, nebo prázdno. `sole` je to, co jde spravit."""
        return self.layers[0] if len(self.layers) == 1 else ""


def diagnose(
    *,
    lines: tuple[str, ...],
    question: str,
    read: bool,
    written: bool,
    refused: bool,
    error: str,
) -> Diagnosis:
    if error:
        kind = "segmentace" if "vět" in error and "rozbor umí jednu" in error else "služba"
        return Diagnosis((kind,), error[:120])
    if written:
        return Diagnosis((), "")
    if refused:
        first = next((l.strip() for l in lines if l.strip().startswith("✗")), "")
        return Diagnosis(("zápis",), first[:160])
    trace = " ".join(lines)
    if not read:
        why = next((l.strip() for l in lines if "[PROČ:" in l), "")
        if why:
            return Diagnosis(("morfologie",), why[:160])
        return Diagnosis(("rozbor",), "0 čtení a systém neumí říct proč")
    found: list[str] = []
    for name, marks, asks in _RULES:
        if any(m in trace for m in marks) or any(a in question for a in asks):
            found.append(name)
    if not found:
        return Diagnosis(("rozbor",), (question or trace)[:160])
    return Diagnosis(tuple(found), (question or "")[:160])
