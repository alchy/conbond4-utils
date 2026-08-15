# Zadání pro Agenta 3 — Builder měřicí vrstvy (conbond4-utils)

Pracuješ v `conbond4-utils`. Protějškem ti je **Reviewer** (Agent 2),
který audituje conBond4 i tenhle repozitář. Střídáte se přes stavový
soubor stejně jako Builder jádra.

---

## 0 · Protokol

**Stav:** `conbond4-utils/.agent_state.json`

```json
{"current_turn": "BUILDER_UTILS" | "REVIEWER",
 "status": "READY_FOR_REVIEW" | "PASS_NEXT_PHASE" | "FAIL" | "PARTIAL",
 "last_action": "…"}
```

Když dokončíš kolo, zapiš `{"current_turn": "REVIEWER", "status":
"READY_FOR_REVIEW"}` a do `last_action` napiš, **co jsi udělal, co jsi
změřil a čím to doložíš**. Čísla uváděj z běhu, ne z odhadu.

**Tvoje dráha:** cokoli v `conbond4-utils/` **kromě** `REVIEW-UTILS.md`
a `.agent_state.json` — ty patří Revieweru.

**PŘÍSNÝ ZÁKAZ:** nikdy needituj nic v `conbond4/`. Ani
`core_semantics/`, ani `tests/`, ani `docs/`. Měřicí vrstva **nesmí
měnit to, co měří** — jinak přestane být měřením. Když narazíš na vadu
jádra, **popiš ji a dolož reprodukcí**; opraví ji Builder jádra.

**PARTIAL je plnohodnotná odpověď.** Ohlásit „tohle je hotové, tohle ne
a tady je proč" je lepší než dodělat něco naslepo. Reviewer to tak bere.

---

## 1 · K čemu ta vrstva je

**Není to ETL, které vyrábí data pro conBond4.** Je to **měřicí hranice
mezi přirozeným jazykem a formálním jádrem**: co conBond4 z textu
bezpečně přečetl, co zapsal, co pochopil jen jako kandidáta, na co se
potřebuje zeptat, co odmítl a co nepřečetl — a **proč**.

Samotné číslo `ZAPSÁNO` nic nedokazuje. Zvednout ho z 0 na 20 % jde
i osekáním korpusu na snadné věty. **Řídit se dá jen rozkladem po
jazykových třídách**: která konstrukce se nově čte bezpečně, která
pořád potřebuje dialog, která je odmítnutá, která padá.

Reviewer z toho musí umět říct ne „přidej víc NLP", ale
*„řeš anaforické zájmeno s jednoznačným antecedentem, protože ta třída
tvoří 18 % NEPŘEČTENO a je přenositelná na dialogový text."*

---

## 2 · Pravidla, která se neporušují

1. **Zdrojový text se nepřepisuje.** Nikdy neupravuj větu proto, aby
   prošla. Ruční oprava konkrétní věty kvůli PASS **skryje skutečnou
   mezeru** — a to je jediná věc, kterou tenhle nástroj nesmí udělat.
2. **Předzpracování jen obecné.** Přípustná je normalizace, kterou by
   šlo pustit na libovolný obdobný text. Nepřípustná je oprava jedné
   věty. Když normalizuješ, **původní text zůstává v reportu vedle**,
   jako samostatná vrstva — musí být vidět, co přišlo ze zdroje a co
   udělal preprocessing.
3. **Zájmena, elipsa, koordinace, pády, shoda, určité popisy, `je`,
   `jsou`, `byli`, `byla` NEJSOU nekvalitní data.** Jsou to legitimní
   testovací požadavky. Když je conBond4 neumí, je to **capability gap
   nebo blocker**, který se změří — ne špína, která se odstraní.
4. **Pět stavů se nikdy neslévá do jednoho skóre.** `ZAPSÁNO`,
   `PTÁ SE`, `NEPŘEČTENO`, `ODMÍTNUTO`, `CHYBA` znamenají různé věci
   a vedou k různým opravám. `PTÁ SE` **není chyba** — dialogový systém
   smí právem narazit na chybějící premisu a vyžádat si ji.
5. **Měření nepřidává sémantiku.** Jsi observability vrstva, ne druhý
   inference engine. Nic v `conbond4-utils` nesmí ovlivnit rozhodnutí
   conBondu4.
6. **Reprodukovatelnost.** U každého zdroje eviduj téma, revizi nebo
   jiný stabilní identifikátor, datum, počet vět, stav každé věty
   a důvod. Bez toho nejde po změně jádra rozeznat „systém se zlepšil"
   od „změnil se vstup".
7. **Cizí text do gitu nepatří**, pokud to není licenčně nutné. Zdroj
   a licence do `ZDROJ.md`, data do `data/` mimo git.

---

## 3 · Program práce — v tomhle pořadí

**Nezakládej vlastní framework dřív, než projdeš ty staré.** conBond2
a conBond3 mají empiricky ověřený způsob, jak porozumění zobrazovat, a
ten je historický artefakt projektu, ne materiál k přepsání.

### Krok 1 — přečti staré frameworky

`github.com/alchy/conBond2` a `github.com/alchy/conBond3`. Reviewer už
udělal první průchod; ověř si ho a jdi hlouběji. Co je zatím nalezené:

| conBond2 | co to je |
|---|---|
| `data/raw/` | **65 článků, 208 064 slov** — Wikipedie CC BY-SA + 5 ručně psaných; provenience v `ZDROJ.md`. Obsahuje `karel_čapek`, `božena_němcová`, `pes_domácí`, `kočka_domácí`, `kůň_domácí`, `koza_domácí`, `králík_domácí` |
| `data/gold/otazky.json` | **682 generovaných otázek**: `text`, `dok`, `veta`, `rozsah`, `typ`, `entita`, `odpoved` |
| `data/gold/etalon.json` | **40 ručně psaných**: `q`, `expect` (podřetězce), `mode` = `answer` / **`unsure`**, `kind`, `dok` |
| `data/gold/conbond.json` | **95 položek z ještě staršího conBondu** — kontinuita už jednou proběhla |
| `scripts/mereni.py` | **dvoustupňová metrika** *zásah pole* × *zúžení*, měřená **křížově** |
| `scripts/baseline.py` | text → věty → rozbor → **koreference** → zápis |
| `pole.html`, `pole2.html`, `js/` | HTML prohlížeč pole |

conBond3: `cb_field/tests/data/` (`etalon-otazky.jsonl`, `korpus/`,
`testbed-kdo-kde-kdy.txt`), `cb_field/viewer.html`, `TEST_STRATEGY.md`.

**Čtyři věci, které se z toho nesmí ztratit** (Reviewerův nález):
`mode: unsure` jako plnohodnotný režim (systém **má mlčet**);
`expect` jako **podřetězce**, ne přesná shoda; **dvoustupňová** metrika;
a `baseline.py`, který pro‑drop řeší **aktivacemi viditelnými v datech**
(`Kor=prodrop`, `Ent=…`) a **vypisuje, kolik případů zasáhl a kolik
potvrdila shoda rodu** — bez přidávání slov do textu.

### Krok 2 — popiš, co je diagnosticky cenné

Ne co tam je, ale **co vývojáři skutečně pomáhalo**. Ostatní zahoď.

### Krok 3 — navrhni mapování starého měření na conBond4

conBond4 má jiné jádro: verdikty `A`/`N`/`U`/`CONFLICT`, důkaz s citací,
dialogové tahy, kaskádu s patry. Přenášej **principy a datový model**,
ne implementaci. Mapování předlož Revieweru **dřív, než ho postavíš**.

### Krok 4 — minimální reprodukovatelný runner

Nad **historickým korpusem conBond2**, ne nad novým. Wikipedie navíc je
rozšíření, ne náhrada. Zachovej **celou relevantní sadu** — nevybírej
si jen to, co conBond4 zvládne; explicitně ukaž, co zvládá, co jen
částečně, co odmítá a co nepřečte.

### Krok 5 — HTML baseline

Hlavní výstup. **Diagnostická mapa, ne log převedený do HTML** a ne
prezentační demo. U každé věty musí být dohledatelné:

- původní text (a normalizace zvlášť, když nějaká byla)
- syntaktický rozbor a relevantní jazykové struktury
- kandidátní čtení a **rozhodnutí kaskády** (které patro co zahodilo)
- pokus o převod do interní reprezentace, vzniklé entity a vztahy
- chybějící premisy, důvod dotazu, důvod odmítnutí, důvod nepřečtení
- vazba na **důkaz** — ať jde rozlišit *„parser rozuměl, inference to
  neuměla použít"* od *„parser vyrobil špatné čtení"* od *„chybí
  znalost"*

K tomu agregace: skóre, rozpis po tématech, rozpis po typech problémů,
nejhorší věty. **Nikdy jeden FAIL místo pěti stavů.**

Baseline **není cíl**, je to měřicí nula. Nevylepšuj ji preprocessingem
ani výběrem snadných vět. Když z 236 vět není žádná `ZAPSÁNO`, je to
legitimní a důležitý výsledek — důležitější než číslo je ukázat **proč**.

### Krok 6 — teprve pak snapshot a diff

Týž korpus po změně jádra, porovnání dvou běhů: nově přečtené věty, nově
zapsané znalosti, nově vzniklé otázky, zmizelá `NEPŘEČTENO`, **nové
regrese**, změny typu rozhodnutí. Ne jen celkové procento.

---

## 4 · Kdy je framework hotový

Když spolehlivě odpoví na čtyři otázky:

1. **Co systém z textu skutečně pochopil?**
2. **Čemu nerozuměl?**
3. **Proč tomu nerozuměl?** (v které vrstvě — segmentace, morfologie,
   závislostní rozbor, koreference, identifikace entity, syntaktická
   interpretace, lexikální mapování, převod do AST, inference, dialogové
   doplnění premisy)
4. **Zlepšilo se to po změně jádra — a bez regresí?**

---

## 5 · Co Reviewer bude na tvé práci měřit

- **Není to log v HTML?** Musí jít z reportu zjistit, proč jedna věta
  skončila jako `NEPŘEČTENO`, **aniž by se musel reprodukovat celý běh**.
- **Nesplývají stavy?** Pět stavů, pět významů.
- **Je to reprodukovatelné?** Táž revize, týž výsledek.
- **Nezasahuje měření do jádra?** `conbond4/` beze změny.
- **Neoptimalizoval jsi na jednu větu?** Metrika musí být třídová.
- **Neztratilo se, co bylo cenné v conBond2/3?** Zvlášť `unsure`
  a dvoustupňovost.
- **Je vidět, co udělal preprocessing?** Původní text zůstává.

Reviewer vrací `FAIL` i tehdy, když je kód v pořádku, ale **měření
tvrdí víc, než doloží**. „Vypadá to jako pokrytí a není to pokrytí" je
nejčastější vada, kterou v tomhle projektu nacházíme — v testech
i v metrikách.

---

## 6 · Současný stav repozitáře

Hotové a funkční, ale postavené **před** tímhle zadáním, takže je to
kandidát na přestavbu podle kroků 1–3, ne hotová věc:

- `cb_utils/wiki.py` — článek z Wikipedie na holý text přes oficiální
  API, s revizí v provenienci
- `cb_utils/triage.py` — věta → jeden z pěti stavů, v čerstvém sezení
- `cb_utils/diagnose.py` — **v které vrstvě věta uvázla**, čteno ze
  stopy a otázky, kterou conBond4 sám vypsal (nic se nehádá z povrchu)
- `cb-wiki.py` — CLI, rozklad po vrstvách, JSON záznam

První měření (4 témata, 238 vět, `mereni/2026-08-15.json`):

```
CELKEM  PTÁ SE 187 · NEPŘEČTENO 49 · CHYBA 2 · ZAPSÁNO 0

vrstva          vyskytuje se   sám blokuje
role            186 (78.2 %)   35 (14.7 %)
kvantifikace    151 (63.4 %)    1 ( 0.4 %)
morfologie       29 (12.2 %)   29 (12.2 %)
rozbor           20 ( 8.4 %)   20 ( 8.4 %)
koreference      12 ( 5.0 %)    0 ( 0.0 %)
konstrukce       10 ( 4.2 %)    0 ( 0.0 %)
segmentace        2 ( 0.8 %)    2 ( 0.8 %)
```

`sám blokuje` = kolik vět uvázlo **jen na téhle jediné vrstvě**. Je to
nejcennější sloupec: věta s jednou otevřenou věcí ukazuje přesnou
hranici schopnosti, věta se sedmi říká jen, že je složitá.

**Nález, který stojí za ověření hned:** `morfologie` zahazuje
**gramatické české věty** —

```
» Matka sbírala folklor.   → NEVÍM, jak to čtu
     [PROČ: shoda čísla — přísudek Plur,Sing, podmět musí být týž]
» Povodeň zasáhla dům.     → totéž
```

Tichá ztráta dobrého vstupu není bezpečné mlčení. Doloží‑li se to na
celém korpusu, je to **blocker pro jádro** — a tvoje vrstva je přesně
to, co k tomu má dodat důkaz.
