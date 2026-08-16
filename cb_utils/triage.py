"""Co si conBond4 s větou počne — MĚŘENO, ne odhadnuto.

Každá věta jde přes `Session.utter` ve VLASTNÍM sezení, takže se výsledky
neovlivňují navzájem. Vrací se pět stavů, které se nesmí slít:

| stav | znamená |
|---|---|
| `ZAPSÁNO` | přečteno a uloženo do báze — kandidát na doménu |
| `PTÁ SE` | přečteno neúplně, systém se ptá — taky kandidát, jen s tahem |
| `DVOJZNAČNÉ` | přečteno **víc způsoby**, systém se ptá který |
| `NEPŘEČTENO` | 0 čtení; patro řeklo proč |
| `ODMÍTNUTO` | čtení bylo, ale zápis se odmítl (kruh, ireflexivita…) |
| `CHYBA` | parser nebo služba selhaly |

**Stavů je šest, a ten šestý je vědomé rozhodnutí.** Pět jich bylo
v zadání, ale pět bylo rozhodnutí, ne dogma — a slévat „větě nerozumím"
s „rozumím jí dvěma způsoby a ptám se kterým" znamená ztratit obojí.
První je mez schopnosti a opravuje se v generátoru nebo v patrech; druhé
je **položená otázka**, tedy plnohodnotný tah dialogu, a opravuje se
odpovědí nebo naučeným vzorem. Do kola #3 padaly obě do `NEPŘEČTENO`
s `open_questions = 0`, takže věta, kde se systém aktivně ptal, se
v součtu tvářila jako věta, kde mlčel.

**Nic se nevybírá za člověka.** Skript netvrdí, která věta „je dobrá do
sady" — doména je rozhodnutí, ne výstup filtru. Tohle jen říká, kde
dnes systém stojí, a to je materiál k rozhodnutí.
"""

from __future__ import annotations

import re
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

from cb_utils.diagnose import AMBIGUOUS_MARK, Diagnosis, diagnose


class Verdict(Enum):
    WRITTEN = "ZAPSÁNO"
    ASKS = "PTÁ SE"
    AMBIGUOUS = "DVOJZNAČNÉ"
    UNREAD = "NEPŘEČTENO"
    REFUSED = "ODMÍTNUTO"
    ERROR = "CHYBA"


@dataclass(frozen=True, slots=True)
class Result:
    sentence: str
    verdict: Verdict
    reading: str
    detail: str
    #: Kolik věcí systém u té věty NEVÍ — délka `questions`. **Je to
    #: počítané, ne odhadnuté**: „složitost" se tady neměří délkou ani
    #: počtem čárek, ale tím, na kolik otázek by člověk musel odpovědět,
    #: než se věta zapíše. Nula znamená „zapsalo se to samo".
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
    #: Otevřené věci jako SEZNAM, nezkrácené — ať jdou dva běhy porovnat
    #: strojově, ne součtem. „Ubyla jedna otázka a přibyla jiná" je
    #: v součtu neviditelné a v seznamu je to vidět hned.
    questions: tuple[str, ...] = ()
    #: Čekající odkazy z `TurnResult.references` — `scope|role|tvar` a
    #: **co systém nabídl**. Prázdná nabídka je jiný stav než nabídka,
    #: ze které si nikdo nevybral: první říká „nemám z čeho", druhý
    #: „mám, ale nerozhodl jsem". Sčítat je by zakrylo, co dělá kontext.
    references: tuple[str, ...] = ()
    #: `QueryStatus` u tázací věty — `A` / `N` / `U` / `CONFLICT`.
    #: Prázdné u oznamovací: **stav dotazu a stav čtení jsou dvě různé
    #: osy** a slít je do jednoho čísla by znamenalo ztratit obojí.
    status: str = ""
    #: Co se u ZAPSANÉ věty **doopravdy zapsalo** — W‑67. Do kola #6
    #: nesla zapsaná věta jen formuli čtení a nešlo ověřit nic dalšího:
    #: ani pod jakým id to leží, ani co se z toho odvodilo, ani jak se
    #: zmínky zakotvily. „Zapsáno" bez toho, CO se zapsalo, je jediný
    #: stav, u kterého report mlčí — a přitom je to ten, kvůli kterému
    #: se celá vrstva měří.
    written_id: str = ""
    #: Věty programu, které tahle promluva do báze přidala, i s
    #: reifikacemi (`role(...)`, `member(...)`) — tedy včetně toho, co
    #: jádro odvodilo samo.
    program: tuple[str, ...] = ()
    #: Celý výstup jádra u zapsané věty: zakotvení zmínek i řádek zápisu.
    #: Jen u zapsaných — u 800 tázaných vět by to záznam nafouklo o věci,
    #: které už nese `trace` a `questions`.
    zapis: tuple[str, ...] = ()
    #: Rozbor v podobě `tvar/UPOS/deprel`, aby šlo z reportu porovnat
    #: čtení s větou, aniž se rozbor pouští znovu. Tady se pozná
    #: „rozbor vyrobil špatné čtení" od „rozbor rozuměl, jádro to
    #: neumělo použít".
    parse: tuple[str, ...] = ()

    @property
    def stav(self) -> str:
        """Stav pro agregace — se **fasetou u zapsané věty**.

        Rozhodnuto **dřív, než přišel první částečný zápis** (jádro ho
        chystá): „zapsáno, a přesto se ptá" **není sedmý stav**, jsou to
        **dvě osy**, které se ale nikde nesčítají do jednoho čísla.

        Proč ne nový stav: osa stavů odpovídá na *co se s větou stalo*,
        a částečný zápis JE zápis — báze se změnila a to je fakt, který
        ta osa nese. Kolik ještě chybí, je otázka druhé osy, kterou jsme
        dvě kola čistili (`questions`); pojmenovat ji zpátky do stavu by
        znamenalo slít je znovu.

        Proč to přesto nestačí nechat na `questions`: holé `ZAPSÁNO 46`,
        kde je dvanáct vět zapsaných jen zčásti, tvrdí víc, než platí.
        Proto se `ZAPSÁNO` v **každé** agregaci štěpí na dvě fasety —
        jeden stav, dvě čísla, nikdy jedno.
        """
        if self.verdict is Verdict.WRITTEN and self.open_questions:
            return "ZAPSÁNO · s otázkami"
        if self.verdict is Verdict.WRITTEN:
            return "ZAPSÁNO · úplně"
        return self.verdict.value

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


#: Jedna otevřená věc = jeden **otazník, kterým končí tah**. Dělí se
#: proto jen za otazníkem, po kterém začíná další věta (velké písmeno)
#: nebo končí text — otazník uvnitř uvozovek („Kolik?") je součást
#: citovaného slova, ne konec otázky. Bez téhle podmínky se 80 otázek
#: rozpadlo v půlce na „) — do čtení se nedostalo. Jak se ta role
#: jmenuje?", což je půlka věty, ne otevřená věc.
_HRANICE = re.compile(r"\?(?=\s+[A-ZÁ-ŽČĎĚŇŘŠŤŮÚÝŽ]|\s*$)")

#: **Jádro se ptá i bez otazníku.** „Věta nemá podmět — … Řekni to
#: prosím jménem." je výzva, ne vysvětlení: dá se na ni odpovědět, a to
#: je celý rozdíl proti „Tuhle větu přečíst neumím: …". Dokud se
#: rozhodovalo jen podle otazníku, měly dvě věty z 836 prázdný seznam,
#: přestože po nich jádro něco chtělo — zbytek N‑10 o dvě věty dál.
_VYZVY: tuple[str, ...] = (
    "Řekni to prosím jménem",
    "Věta nemá podmět",
)


def je_otazka(text: str) -> bool:
    """Ptá se jádro tímhle textem? Otazník, nebo známá výzva."""
    return "?" in text or any(v in text for v in _VYZVY)

#: Druh otevřené věci podle toho, ČÍM ZAČÍNÁ otázka jádra. Slouží ke
#: strojovému porovnání dvou běhů — text otázky nese jména konkrétních
#: slov, takže sám o sobě se mezi větami neporovná.
_DRUHY: tuple[tuple[str, str], ...] = (
    ("Nevím, jakou roli hraje", "role"),
    ("Nevím, co znamená", "role"),
    ("Nevím, o kom to platí", "kvantifikace"),
    ("Na koho odkazuje", "koreference"),
    ("A na koho odkazuje", "koreference"),
    ("O kterém", "koreference"),
    ("Zájmena zatím neumím", "koreference"),
    ("Co ta věta tvrdí o vztahu", "konstrukce"),
    ("prohlásit za UZAVŘENOU", "uzavření"),
    ("Věta nemá podmět", "podmět"),
    ("Řekni to prosím jménem", "zakotvení"),
    # Pořadí rozhoduje: v jednom tahu jádra může stát koordinační
    # výklad („Z rozboru to poznat nejde…") a teprve za ním skutečná
    # otázka na vztažnou větu. Ptá se to poslední, tak se podle toho
    # položka jmenuje.
    ("A koho se týká ta vztažná věta", "vztažná_věta"),
    ("Věta jmenuje víc členů v roli", "koordinace"),
    ("Z rozboru to poznat nejde", "koordinace"),
    ("Co ten přívlastek v genitivu tvrdí", "přívlastek"),
    ("Co ten přívlastek tvrdí", "přívlastek"),
    ("Zapíšu to jako vztah vedle věty", "přívlastek"),
    ("Ta věta tvrdí ještě tohle", "konstrukce"),
    ("Tvar je ", "konstrukce"),
    (AMBIGUOUS_MARK, "dvojznačnost"),
)


def _druh(text: str) -> str:
    """Druh otevřené věci. `jiné` je **signál, ne odpadní koš**: jádro
    umí novou otázku a měření pro ni ještě nemá jméno, takže se má
    doplnit. Tabulka po každém kole jádra zestárne — sledovat počet
    `jiné` je způsob, jak to poznat dřív než z reportu."""
    for zacatek, jmeno in _DRUHY:
        if zacatek in text:
            return jmeno
    return "jiné"


def open_items(lines: tuple[str, ...], question: str) -> tuple[str, ...]:
    """Otevřené věci jako **seznam**, a **z OTÁZKY, ne ze stopy**.

    Dvě předchozí verze se spletly každá jinak a obě stejným způsobem —
    počítaly něco jiného, než na co se systém ptal:

    * první počítala výskyty `CHYBÍ:` a `NEZAKOTVENO:` v řádcích, takže
      dvojznačné čtení („Čtu to jako A / B — které z toho?") vyšlo jako
      **nula** otevřených věcí, ačkoli je to položená otázka;
    * druhá k tomu přidala dvojznačnost, ale pořád četla **stopu**.
      A stopa nemusí nést hranatou značku: 108 z 669 tázaných vět mělo
      prázdný seznam, přestože se jádro ptalo. Táž otázka („Nevím, jakou
      roli hraje…") se v korpusu objevila 237×, započítala se 134× a
      nezapočítala 103× — nerozhodovala věta ani otázka, ale náhoda,
      jestli u ní zrovna stála značka. A u vět, kde se stopa a otázka
      lišily, seznam **pojmenovával něco jiného**, než na co se systém
      ptal.

    Zdroj je proto jediný: **otázka jádra**. Když se jádro ptá, seznam
    není prázdný; když mlčí, prázdný je.

    **Rozpad otázky na položky:** jedna položka = jeden **otazník**.
    Jádro skládá otázku z tahů, které samy končí otazníkem („… Jak se ta
    role jmenuje? Nevím, o kom to platí — … nebo o tom konkrétním (·)?"),
    takže dělení za otazníkem sedí na tahy, ne na věty. Text **před**
    otazníkem se drží celý, protože v něm je, o kterém slově řeč.

    Co otazník nemá, není otázka: „Tuhle větu přečíst neumím: přísudek
    nemá ani jeden člen, který bych uměl pojmenovat." je **vysvětlení**
    a odpovědět na něj nejde. Takové věty mají prázdný seznam právem a je
    to ten druhý směr téhož pravidla.

    Ke každé položce se lepí **druh** (`role`, `kvantifikace`,
    `koreference`, …), aby šly dva běhy porovnat strojově: samotný text
    otázky nese jména konkrétních slov, takže se mezi větami neporovná.
    """
    zdroj = question
    if not zdroj:
        # `_utter_many` vypíše otázku jen do řádků, do `question` ji
        # nedá — bez téhle zálohy by dvojznačnost z víc rozborů zase
        # spadla na nulu.
        zdroj = " ".join(l.strip().lstrip("? ") for l in lines if "?" in l)
    out: list[str] = []
    zacatek = 0
    kusy: list[str] = []
    for hranice in _HRANICE.finditer(zdroj):
        kusy.append(zdroj[zacatek : hranice.end()])
        zacatek = hranice.end()
    # Zbytek za posledním otazníkem je položka jen tehdy, když je to
    # VÝZVA („Řekni to prosím jménem."). Vysvětlení bez otazníku
    # položka není — na „Tuhle větu přečíst neumím" se odpovědět nedá.
    zbytek = zdroj[zacatek:].strip()
    if zbytek and any(v in zbytek for v in _VYZVY):
        kusy.append(zbytek)
    for kus in kusy:
        text = kus.strip()
        if not text:
            continue
        polozka = f"{_druh(text)}: {text}"
        # Táž otevřená věc se u dvojznačné věty objeví jednou za každé
        # kandidátní čtení. Pro člověka je to JEDNA otázka, takže se
        # opakování slučuje — jinak by dvojznačnost nafoukla i počet.
        if polozka not in out:
            out.append(polozka)
    return tuple(out)


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


def nove_sezeni() -> Session:
    return Session(lexicon=golden.golden_lexicon())


def triage(sentence: str, oracle: UDPipeOracle, session: Session | None = None) -> Result:
    """Jedna věta. **Čerstvé sezení, pokud se nepředá jiné.**

    Výchozí chování zůstává „každá věta ve vlastním sezení", protože
    v něm se věty neovlivňují a měření tak neměří pořadí. Dokumentový
    běh je vědomá výjimka: jedno sezení na dokument, věty v pořadí, aby
    zájmeno mělo kam sáhnout. Obojí je legitimní měření, jen měří něco
    jiného — a proto se to nesmí míchat v jednom záznamu.
    """
    session = session or nove_sezeni()
    try:
        result = session.utter(sentence, oracle)
    except (SegmentationError, OracleError) as error:
        d = diagnose(lines=(), question="", read=False, written=False,
                     refused=False, error=str(error))
        return Result(sentence, Verdict.ERROR, "", d.reason,
                      layers=d.layers, sole=d.sole, kind=d.kind)
    lines = tuple(result.lines)
    reading = _first(lines, "✓ přečteno", "◐ přečteno", "→ NEVÍM, jak")
    question = result.question or ""
    questions = open_items(lines, question)
    d = diagnose(
        lines=lines,
        question=question,
        read=result.predication is not None,
        written=bool(result.statement_id),
        refused=bool(_first(lines, "✗")),
        error="",
    )
    # Vše klíčem, ne pořadím: pole v `Result` přibývají a poziční volání
    # by po každém přidání tiše posunulo význam argumentů.
    common = {
        "layers": d.layers,
        "sole": d.sole,
        "kind": d.kind,
        "open_questions": len(questions),
        "questions": questions,
        "trace": tuple(result.trace),
        "question": question,
        "status": result.status.value if result.status is not None else "",
        "parse": parse_of(sentence, oracle),
        "references": tuple(
            f"{o.scope}|{o.role}|{o.form}|{','.join(o.candidates)}"
            for o in getattr(result, "references", ())
        ),
    }
    if result.statement_id:
        return Result(
            sentence, Verdict.WRITTEN, reading, "",
            **{
                **common,
                "layers": (),
                "sole": "",
                "kind": "",
                "written_id": result.statement_id,
                # Sezení je čerstvé na každou větu, takže `program()` je
                # přesně to, co přidala TAHLE promluva — ne co se
                # nasbíralo za běh.
                "program": tuple(session.program()),
                "zapis": lines,
            },
        )
    if _first(lines, "✗"):
        return Result(sentence, Verdict.REFUSED, reading, d.reason, **common)
    if result.predication is None:
        # Dvojznačné čtení je OTÁZKA, ne mlčení — vlastní stav.
        stav = (
            Verdict.AMBIGUOUS
            if d.sole == "dvojznačnost"
            else Verdict.UNREAD
        )
        return Result(sentence, stav, reading, d.reason, **common)
    return Result(sentence, Verdict.ASKS, reading, d.reason, **common)


def sentences_of(text: str, oracle: UDPipeOracle) -> tuple[str, ...]:
    """Rozdělení na věty dělá TÁŽ služba, která pak větu rozebírá.

    Vlastní dělič by se s parserem rozešel — a to je přesně ten druh
    tichého rozdílu, který se pozná až na výsledcích.
    """
    return tuple(u.text for u in oracle.segment(text))
