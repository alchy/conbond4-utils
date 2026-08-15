"""Co si conBond4 s větou počne — MĚŘENO, ne odhadnuto.

Každá věta jde přes `Session.utter` ve VLASTNÍM sezení, takže se výsledky
neovlivňují navzájem. Vrací se pět stavů, které se nesmí slít:

| stav | znamená |
|---|---|
| `ZAPSÁNO` | přečteno a uloženo do báze — kandidát na doménu |
| `PTÁ SE` | přečteno neúplně, systém se ptá — taky kandidát, jen s tahem |
| `NEPŘEČTENO` | 0 čtení; patro řeklo proč |
| `ODMÍTNUTO` | čtení bylo, ale zápis se odmítl (kruh, ireflexivita…) |
| `CHYBA` | parser nebo služba selhaly |

**Nic se nevybírá za člověka.** Skript netvrdí, která věta „je dobrá do
sady" — doména je rozhodnutí, ne výstup filtru. Tohle jen říká, kde
dnes systém stojí, a to je materiál k rozhodnutí.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

CONBOND4 = Path(__file__).resolve().parent.parent.parent / "conbond4"
if str(CONBOND4) not in sys.path:  # pragma: no cover — cesta k jádru
    sys.path.insert(0, str(CONBOND4))

from core_semantics.oracle import OracleError, SegmentationError, UDPipeOracle
from core_semantics.session import Session
import core_semantics.tests.golden as golden

from cb_utils.diagnose import Diagnosis, diagnose


class Verdict(Enum):
    WRITTEN = "ZAPSÁNO"
    ASKS = "PTÁ SE"
    UNREAD = "NEPŘEČTENO"
    REFUSED = "ODMÍTNUTO"
    ERROR = "CHYBA"


@dataclass(frozen=True, slots=True)
class Result:
    sentence: str
    verdict: Verdict
    reading: str
    detail: str
    #: Kolik věcí systém u té věty NEVÍ — čekající kvantifikátory plus
    #: nepojmenované tvary. **Je to počítané, ne odhadnuté**: „složitost"
    #: se tady neměří délkou ani počtem čárek, ale tím, na kolik otázek
    #: by člověk musel odpovědět, než se věta zapíše. Nula znamená
    #: „zapsalo se to samo".
    open_questions: int = 0
    #: Ve KTERÉ VRSTVĚ věta uvázla. Prázdné u zapsané věty.
    layers: tuple[str, ...] = ()
    #: Jediná vrstva, nebo prázdno — věta, která uvázla JEN na jedné
    #: věci, ukazuje přesnou hranici schopnosti a je nejcennější.
    sole: str = ""
    #: Jemnější druh uvnitř vrstvy, slovy jádra (`shoda_čísla`,
    #: `pádová_mřížka`, `bez_čtení`, `mlčení`). Vrstva říká, KDE se to
    #: opravuje; druh říká CO — a bez něj splyne dvacet vět shozených
    #: dvojznačným rysem s devíti, kde shoda opravdu neplatí.
    kind: str = ""
    #: Stopa kaskády: **které patro co zahodilo**, doslova. Bez ní se
    #: z reportu nedá zjistit, proč věta skončila, jak skončila, jinak
    #: než zopakováním celého běhu — a to je přesně to, co report má
    #: ušetřit.
    trace: tuple[str, ...] = ()
    #: Otázka, kterou jádro položilo. Prázdná neznamená „nemá otázku",
    #: znamená „neptalo se".
    question: str = ""
    #: `QueryStatus` u tázací věty — `A` / `N` / `U` / `CONFLICT`.
    #: Prázdné u oznamovací: **stav dotazu a stav čtení jsou dvě různé
    #: osy** a slít je do jednoho čísla by znamenalo ztratit obojí.
    status: str = ""
    #: Rozbor v podobě `tvar/UPOS/deprel`, aby šlo z reportu porovnat
    #: čtení s větou, aniž se rozbor pouští znovu. Tady se pozná
    #: „rozbor vyrobil špatné čtení" od „rozbor rozuměl, jádro to
    #: neumělo použít".
    parse: tuple[str, ...] = ()

    def render(self) -> str:
        gap = f" ({self.open_questions}×?)" if self.open_questions else ""
        what = f" {{{'+'.join(self.layers)}}}" if self.layers else ""
        what += f"/{self.kind}" if self.kind else ""
        head = f"[{self.verdict.value:11}]{gap}{what} {self.sentence}"
        body = f"\n              {self.reading}" if self.reading else ""
        tail = f"\n              {self.detail}" if self.detail else ""
        return head + body + tail


def _first(lines: tuple[str, ...], *prefixes: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefixes):
            return stripped
    return ""


def parse_of(sentence: str, oracle: UDPipeOracle) -> tuple[str, ...]:
    """Rozbor jako `tvar/UPOS/deprel→hlava`, bez rysů.

    Do záznamu patří proto, že bez něj nejde z reportu poznat **špatné
    čtení** od chybějící schopnosti: predikace „kdo: inflace" je vidět
    jako vadná teprve vedle rozboru, kde `inflace` visí jako `obj`.
    Rysy se sem nedávají — je jich moc a to podstatné z nich nese stopa
    kaskády, která je cituje sama.
    """
    try:
        utterance = oracle.parse(sentence)
    except OracleError:
        return ()
    if not utterance.readings:
        return ()
    return tuple(
        f"{t.form}/{t.upos}/{t.deprel}→{t.head}" for t in utterance.readings[0].tokens
    )


def triage(sentence: str, oracle: UDPipeOracle) -> Result:
    """Jedna věta, jedno čerstvé sezení."""
    session = Session(lexicon=golden.golden_lexicon())
    try:
        result = session.utter(sentence, oracle)
    except SegmentationError as error:
        d = diagnose(lines=(), question="", read=False, written=False,
                     refused=False, error=f"{error}")
        return Result(sentence, Verdict.ERROR, "", d.reason, 0, d.layers,
                      d.sole, d.kind)
    except OracleError as error:
        d = diagnose(lines=(), question="", read=False, written=False,
                     refused=False, error=str(error))
        return Result(sentence, Verdict.ERROR, "", d.reason, 0, d.layers,
                      d.sole, d.kind)
    lines = tuple(result.lines)
    reading = _first(lines, "✓ přečteno", "◐ přečteno", "→ NEVÍM, jak")
    open_questions = sum(1 for line in lines if "CHYBÍ:" in line or "NEZAKOTVENO:" in line)
    question = result.question or ""
    d = diagnose(
        lines=lines,
        question=question,
        read=result.predication is not None,
        written=bool(result.statement_id),
        refused=bool(_first(lines, "✗")),
        error="",
    )
    common = {
        "trace": tuple(result.trace),
        "question": question,
        "status": result.status.value if result.status is not None else "",
        "parse": parse_of(sentence, oracle),
    }
    if result.statement_id:
        return Result(sentence, Verdict.WRITTEN, reading, "", 0, (), "", "",
                      **common)
    if _first(lines, "✗"):
        return Result(sentence, Verdict.REFUSED, reading, d.reason,
                      open_questions, d.layers, d.sole, d.kind, **common)
    if result.predication is None:
        return Result(sentence, Verdict.UNREAD, reading, d.reason,
                      open_questions, d.layers, d.sole, d.kind, **common)
    return Result(sentence, Verdict.ASKS, reading, d.reason,
                  open_questions, d.layers, d.sole, d.kind, **common)


def sentences_of(text: str, oracle: UDPipeOracle) -> tuple[str, ...]:
    """Rozdělení na věty dělá TÁŽ služba, která pak větu rozebírá.

    Vlastní dělič by se s parserem rozešel — a to je přesně ten druh
    tichého rozdílu, který se pozná až na výsledcích.
    """
    return tuple(u.text for u in oracle.segment(text))
