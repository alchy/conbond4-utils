"""Ve KTERÉ VRSTVĚ věta uvázla — čteno z toho, co systém sám řekl.

Zásada, na které tenhle modul stojí: **nic se nehádá z povrchu věty.**
Vrstva se určuje ze stopy a z otázky, kterou conBond4 vypsal, protože
ten jediný ví, kde se zastavil. Klasifikátor, který by se díval na text
a odhadoval „tohle bude koreference", by měřil sám sebe.

Vrstvy jsou úmyslně ty, které jmenuje zadání, a **nesmí se slévat**:
každá odpovídá jinému místu v architektuře a jiné opravě.

    segmentace          text se nerozpadl na věty tak, jak parser čeká
    morfologie          tvrdé patro (shoda, pádová mřížka) zahodilo čtení
    kořen               rozbor nemá kořen, ze kterého by šel přísudek
    role_nenalezena     přísudek nemá ani jeden pojmenovatelný člen
    rozbor              0 čtení; důvod jádra beze změny, nebo mlčení
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


#: Co jádro samo řekne, když z věty nevznikne ANI JEDNO čtení
#: (`cascade.why_nothing`). Klíč je doslovný kus té věty, hodnota jméno
#: vrstvy. **Nic se nehádá z povrchu věty** — čte se odpověď jádra.
#:
#: Dřív se tahle větev zahazovala a všech dvacet případů z prvního běhu
#: dostalo hlášku „0 čtení a systém neumí říct proč". To bylo tvrzení
#: o jádře, které NEPLATILO: jádro důvod řeklo, jen ho měřicí vrstva
#: nepřečetla, protože ho hledala výhradně v řádcích `[PROČ:`. Měření,
#: které jádru podsune mlčení, je horší než měření žádné.
_NO_READING: tuple[tuple[str, str], ...] = (
    ("rozbor nemá kořen", "kořen"),
    ("dvě určení mají týž tvar", "kolize_rolí"),
    ("dva jádrové členy dostaly touž roli", "kolize_rolí"),
    ("nemá ani jeden člen, který bych uměl pojmenovat", "role_nenalezena"),
)

#: Které tvrdé patro čtení zahodilo. Taky doslova ze stopy jádra —
#: „morfologie" je pro řízení práce moc hrubá: shoda čísla a pádová
#: mřížka jsou dvě různé opravy.
_HARD: tuple[tuple[str, str], ...] = (
    ("shoda čísla", "shoda_čísla"),
    ("pádová mřížka", "pádová_mřížka"),
)


@dataclass(frozen=True, slots=True)
class Diagnosis:
    layers: tuple[str, ...]
    reason: str
    #: Jemnější druh UVNITŘ vrstvy, taky ze slov jádra. Vrstva říká, kde
    #: se to opravuje; druh říká co. Zvlášť proto, že se vrstvy sčítají
    #: napříč běhy a přejmenovat je by rozbilo srovnání se starším během.
    kind: str = ""

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
            kind = next((k for mark, k in _HARD if mark in why), "")
            return Diagnosis(("morfologie",), why[:160], kind)
        # Jádro má pro „ani jedno čtení" vlastní vysvětlení
        # (`cascade.why_nothing`) a posílá ho v OTÁZCE, ne v řádku
        # `[PROČ:`. Čte se odtud doslova; kdyby se sem začalo hádat
        # z povrchu věty, měřila by tahle vrstva sama sebe.
        said = question or next(
            (l.strip() for l in lines if "přečíst neumím" in l), ""
        )
        for mark, layer in _NO_READING:
            if mark in said:
                return Diagnosis((layer,), said[:200], "bez_čtení")
        if said:
            return Diagnosis(("rozbor",), said[:200], "bez_čtení")
        return Diagnosis(("rozbor",), "0 čtení a systém neřekl proč", "mlčení")
    found: list[str] = []
    for name, marks, asks in _RULES:
        if any(m in trace for m in marks) or any(a in question for a in asks):
            found.append(name)
    if not found:
        return Diagnosis(("rozbor",), (question or trace)[:160])
    return Diagnosis(tuple(found), (question or "")[:160])
