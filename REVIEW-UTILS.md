# conbond4-utils — audit měřicí vrstvy

## Status: 🟢 PASS — přeměřeno nad čistým jádrem, a kázeň nahradil nástroj

**Kolo #6.** Commity `0c3aa8d`, `7c27dcd`, `edbca3d`, `9fcc847`.

**Architectural Health Score: 9,7 / 10** (bylo 9,6).

---

## Přejímka položku po položce — ověřeno mnou

```
core == core_na_konci          6be9329 …  OBĚ STRANY BEZ +dirty      ✔
měřicí vrstva                  7c27dcd    bez +dirty                 ✔
counts přepočitatelné po větách  666 · 124 · 34 · 7 · 5 = 836        ✔
determinismus                  shoda ve stavech i vrstvách           ✔
N‑10                           ptá se 679 → prázdný 0 · mlčí 157 → neprázdný 0
mapa nese tři revize           korpus · jádro · vrstva               ✔
otevřených věcí                1904
```

**Nejlepší rozhodnutí kola: kázeň nahradil nástroj.** `--nad-cistym`
počká na čistý commit a **když se strom během měření změní, ZÁZNAM SE
NEULOŽÍ**. To „neuložit" je správně a tvůj důvod platí doslova:
*soubor pak leží v repu, kreslí se z něj mapa a varování si nikdo
nepřečte.*

**A žes počkal i sám na sebe** — první pokus měl čisté jádro, ale
rozdělanou měřicí vrstvu, a ten záznam jsi nechal jako `‑1051`, aby
bylo vidět, že se hlídá obojí — **to je ta část, kterou bych ti
neuměl vymyslet.**

**Červený pruh v mapě jsem ověřil jen negativně:** v tomhle běhu
**správně chybí**. Že se objeví, když má, jsem nezkoušel — **doplň k němu
zkoušku**, ať to nezůstane na slově.

**Tabulku „stav podle délky věty" jsem přepočítal proti `‑1052`, jak jsi
chtěl — vychází ZNAK ZA ZNAKEM stejně:**

```
0–5  133/21   6–10  180/9   11–15  162/0   16–25  240/3   26–40  96/1   41+  25/0
medián zapsané věty 5 slov  ·  medián korpusu 14
```

**Závěr z #132 tedy drží** — a drží **na platném běhu**, což je rozdíl,
který se dal zjistit jedině přeměřením.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Nic nového.** Otevřené: **W‑67** (prázdný `reason` u `ZAPSÁNO`, dnes
34 z 836) — souhlas, že je další v pořadí.

---

## Rozhodnutí, které sis vyžádal: LICENCE ZÁZNAMŮ

**Ptáš se správně a je dobře, žes to nezamlčel.** Záznamy v `mereni/`
nesou **celé věty cizího textu** (Wikipedie, CC BY‑SA) ve veřejném
repozitáři.

**Rozhoduji variantu 1 — text zůstane, atribuce se doplní** — a důvod
je věcný: **bez věty se ze záznamu nedá zjistit, na co se systém ptal**,
a to je jediné, k čemu ta vrstva je. Otisk místo textu zabije diagnózu;
záznamy mimo git zabijí reprodukovatelnost napříč stroji.

**Co k tomu musí přibýt, ať je to hotové a ne rozdělané:**

* **licenční soubor** u `mereni/` s uvedením CC BY‑SA a odkazem na
  licenci;
* **atribuce po dokumentech** — u každého dokumentu **název článku
  a URL**, ne jen `conBond2@418d7f7`;
* **věta v `README.md`**, že repozitář obsahuje odvozeninu z CC BY‑SA
  a co z toho plyne pro toho, kdo si ho forkne.

**A protože je to věc, která míří ven z projektu, ne dovnitř:
POSLEDNÍ SLOVO MÁ MAJITEL REPA.** Jestli řekne „žádný cizí text
v gitu", padá to na variantu 3 a záznamy se drží mimo — pak ale chci
vidět, **čím se nahradí diagnóza**, ne jen že se text odstranil.

---

## Action Items for Agent 3

1. **Atribuce podle rozhodnutí výše** — a než bude hotová, **nepřidávej
   do `mereni/` další záznamy s celými větami**.
2. **Zkouška na červený pruh** (ověřeno zatím jen negativně).
3. **Pak W‑67.**
4. **A jedna věc přijde od Agenta 1, počítej s ní:** schválil jsem
   **částečný zápis** — věta se bude smět zapsat i s otevřenými
   otázkami. **Přinese to stav, pro který dnes nemáš jméno**
   (*„zapsáno, a přesto se ptá"*), a **nechci, aby ti spadl do „jiné"**.
   **Rozhodni, jestli je to šestý a půltý stav, nebo dvě osy** — a
   rozhodni to **dřív, než ten běh přijde**.

**Přejímka:** `core == core_na_konci` bez `+dirty`, counts
přepočitatelné, N‑10 0 porušení, determinismus shoda, mapa se třemi
revizemi — **a nově: žádný nový záznam bez atribuce.**

---

## ARCHIV — kolo #5

### Status: 🔴 FAIL — nástroj je opravený a hned si všiml sám sebe: **záznam je z běhu, který se nedá zopakovat**

**Kolo #5.** Commity `b0bc673`, `675bea6`, `bf4e8fb`, `1492c22`.

**Architectural Health Score: 9,6 / 10** — vrstva je lepší, odevzdaný
doklad ne.

---

## Co drží, ověřeno mnou

```
W‑78  protipříklad na vymyšlených řetězcích (revize_poplach.py)   0 porušení
      přibyl nesledovaný soubor → SHODA   ·  uklizeno vedle → SHODA
      sledovaný strom / commit / čistý→rozdělaný → ROZDÍL
W‑79  všechny tři skripty berou poslední záznam, spustil jsem je bez argumentu
      názvy korpus-RRRR-MM-DD-HHMM.json se řadí správně
N‑10  drží dál: ptá se 679 · prázdný seznam 0 · mlčí 157 · neprázdný 0
HTML  2,3 MB jeden soubor · lang="cs" + translate="no"
      šest stavů zvlášť, sedm druhů zvlášť, nikde jeden součet
```

**Že „poslední podle jména" vracelo STARŠÍ záznam, protože pomlčka je
v abecedě před tečkou, jsi našel sám** — a je to přesně ta vada, která
nespadne a jen tiše kreslí nad starým během. **Stejně tak `nsubj:pass`
v tabulce očekávaných závislostí: číslo, které skočilo šestkrát (12 →
78), byl artefakt párování, ne změna správnosti.** Obojí jsi ohlásil
dřív, než se někdo zeptal.

**Řazení vět v mapě podle POČTU OTEVŘENÝCH VĚCÍ, ne podle délky**, je
správné rozhodnutí: *nejhorší věta není nejdelší, ale ta, na kterou by
člověk musel odpovědět nejvíckrát.*

---

## Critical Blockers

### Záznam `korpus-2026-08-16-1050.json` je z běhu nad ROZDĚLANÝM jádrem, které se během běhu ZMĚNILO

```
core          : 27c6a62 … složí se i pod ztracenou hlavou  +dirty:bb2a6d72
core_na_konci : 27c6a62 … složí se i pod ztracenou hlavou  +dirty:21360955
```

**Tvoje nové pole zafungovalo přesně tak, jak má, a ohlásilo pravdu.
Jenže ta pravda zní: tenhle běh se nedá zopakovat.** Čísla
`666 / 124 / 34 / 7 / 5` **nepatří commitu `27c6a62`** — patří něčemu
mezi dvěma rozdělanými stavy, které v žádném commitu nejsou.

**Popsals to jako úspěch detektoru** (*„první skutečné zachycení té
změny a přesně k tomu to pole je"*) — **a to je pravda**. Ale je to
zároveň důvod ten záznam **znovu naměřit**, ne ho odevzdat. **Je to
tvoje vlastní pravidlo z W‑69**, jen obrácené na jádro: *měř nad
commitnutým stromem*.

**A dopad je větší než jeden soubor: HTML baseline se kreslí z něj**,
takže mapa, kterou jsi odevzdal jako krok 5, stojí na číslech, ke
kterým se nikdo nemůže vrátit.

**Co chci:** přeměřit nad **čistým, commitnutým** jádrem, vydat nový
záznam a **překreslit mapu z něj**. Nic jiného tohle kolo neotvírej.

**Přiznávám u toho vlastní chybu:** poprvé jsem si ta pole vypsal
zkrácená na 80 znaků, `+dirty:…` se do výpisu nevešlo a **málem jsem
napsal, že `core == core_na_konci` a je to v pořádku.** Je to popáté,
co mě v téhle sérii doběhla vlastní zkratka v měřidle — a tentokrát by
to prošlo do verdiktu.

---

## Semantic Warnings

**Čísla z toho záznamu už jsem jednou použil** — tabulka „stav podle
délky věty" ve verdiktu jádra #132 je z něj. **Závěr (od 11 slov výš se
nezapíše prakticky nic) je tak silný, že ho pár vět nezvrátí**, ale
**po přeměření ho ověřím znovu** a v REVIEW.md to opravím, jestli se
pohne.

**W‑67 zůstává** — prázdný `reason` u `ZAPSÁNO`, dnes **34 z 836** vět,
u nichž ze záznamu nejde ověřit nic než formuli. **Souhlas, že je další
v pořadí** — ale až po přeměření.

---

## Action Items for Agent 3

1. **Přeměřit nad čistým jádrem** a vydat nový záznam. Když jádro
   zrovna rozdělané je, **počkej** — běh nad rozdělaným stromem není
   měření, je to odhad s razítkem.
2. **Překreslit `baseline.html` z nového záznamu** a v hlavičce mapy
   uvést revizi jádra, korpusu i vrstvy — ať se z obrázku pozná, čeho
   je obrazem.
3. **Pak W‑67.**

**Přejímka:** `core == core_na_konci`, **obě strany bez `+dirty:`**;
counts přepočítatelné po větách; N‑10 dál 0 porušení; determinismus
shoda; mapa nese tři revize.

---

## ARCHIV — kolo #4

### Status: 🟢 PASS — N‑10 zavřená v obou směrech, a předpověď byla dřív než měření

**Kolo #4.** Commity `6aae0c9`, `0ed6c30`, `40bfc8c`, `3827731`,
`4ecb9da`.

**Architectural Health Score: 9,6 / 10** (bylo 9,3).

---

## Ověřil jsem to sám, ne jeho skriptem — a pak i jeho skriptem

```
vět v záznamu                                836
  jádro se ptá                               679   ptá se a seznam PRÁZDNÝ:   0
  jádro mlčí                                 157   mlčí a seznam NEPRÁZDNÝ:   0
open_questions == len(questions) u VŠECH             ano
součet otázek                               1917
druhy: role 956 · kvantifikace 375 · přívlastek 230 · koordinace 167
       · konstrukce 130 · koreference 52 · dvojznačnost 7 · jiné 0
```

**Ta vada je pryč.** Ve starém záznamu mělo **116 tázaných vět prázdný
seznam**; dnes **nula** — a **druhý směr je tam taky**, takže se to
nedalo splnit otočením vady na druhou stranu.

**Zdroj je jeden a je ten správný: otázka jádra.** Podmínka, že otazník
uvnitř uvozovek hranicí není, je přesně ten druh detailu, který se
pozná jedině během — a žes napsal, co by bez ní vyšlo (*„80 otázek se
rozpadlo v půlce věty"*), je doklad, ne poznámka.

## Předpověď byla PŘED měřením a odchylku vysvětlilo jádro, ne měření

**Reprodukoval jsem tvoji simulaci nad starým záznamem:**

```
--simulace   1863 → 1782 (−81)   ← předpověď, ještě před přeměřením
naměřeno     1917               ← o 135 víc
rozdíl:      role −20 · přívlastek −14 · konstrukce +2
             kvantifikace 0 · koreference 0 · dvojznačnost 0
             KOORDINACE 0 → 167     ← tah, který přinesl commit 1009036
```

**Sedí to do jedné položky.** A **„jiné" jako signál, ne odpadní koš**,
je nejlepší myšlenka téhle předávky: *tabulka druhů po každém kole
jádra zestárne a počet „jiné" je způsob, jak to poznat z běhu*.
**To si beru dál i do jádra.**

**A že jsi nepsal 1863 a 1917 vedle sebe jako „nárůst"**, protože se
mezitím změnila JEDNOTKA, je přesně ta poctivost, kterou tu vymáhám:
součty přes změnu definice nejsou srovnatelné.

**W‑70 opraveno správně** — ověřeno proti mému měření z kola #122:
3× `v+Loc/Geo`, 1× `u+Gen/Geo`, 1× `v+Loc`, a u *„Klíče od chaty"* vede
otázka na genitivní přívlastek. **Rodina je táž, věta ne.**

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

### W‑78 · planý poplach jsi neodstranil, přesunul jsi ho o pole vedle

**Záznam z běhu, který jsi právě odevzdal:**

```
core         : 1009036 … zúžení B‑27 (+6 nesledovaných souborů)
core_na_konci: 1009036 … zúžení B‑27 (+7 nesledovaných souborů)
```

**`core != core_na_konci`.** Pole, které existuje **jen proto**, aby
odpovědělo *„změnilo se jádro během běhu?"*, dnes odpovídá **ANO** —
a důvodem je, že během běhu přibyl **jeden nesledovaný soubor**
(nejspíš `__pycache__`). **Commit je týž, sledovaný strom je týž.**

**Je to táž vada, kterou jsi tohle kolo opravoval** (*„git status
hlásil dirty, i když se lišily jen nesledované soubory"*) — jen jsi ten
šum vyndal z jednoho místa a **nechal ho uvnitř řetězce, který se
POROVNÁVÁ**.

**Oprava plyne z tvé vlastní věty z jádra:** *„provenience je poznámka
pro člověka, rukojeť je hodnota, kterou kód porovnává."* **Počet
nesledovaných souborů je poznámka. Do porovnávané hodnoty nepatří** —
ať stojí vedle ní.

### W‑79 · `otazka_neni_nula.py` bez argumentu nespustí

```
VYCHOZI = … / "mereni" / "korpus-2026-08-15-c.json"     ← ten soubor v repu není
```

Skript je tvůj hlavní doklad k N‑10 a **kdo ho spustí podle docstringu,
dostane „záznam … není"**. Ukaž na poslední záznam, nebo ať si ho
najde sám.

---

## Action Items for Agent 3

1. **W‑78** — jednořádkové, ale je to identita běhu, tedy to jediné,
   čím se záznam liší od tabulky. **Protipříklad:** dva běhy nad touž
   revizí dají `core == core_na_konci` **i když mezi nimi přibude
   nesledovaný soubor**; a když se **sledovaný** strom opravdu změní,
   pozná se to dál.
2. **W‑79** — ať doklad jde spustit tak, jak je popsaný.
3. **Pak HTML baseline** (krok 5) — pořadí jsi držel správně, nemělo
   smysl kreslit ho nad čísly, která se po N‑10 změnila.
   **Podmínka:** baseline kreslí **stavy i druhy otázek** (těch sedm),
   ne jen součet — jinak se z obrázku nepozná právě to, co jsme dvě
   kola opravovali.
4. **Otevřené dál:** **W‑67** — prázdný `reason` u `ZAPSÁNO`. Dnes je
   `ZAPSÁNO` 31 z 836 a **u žádné z nich nejde ověřit nic než formule**.
   Po zavedení jmenné fráze v jádře jich přibude; **čím dřív, tím míň
   práce.**

---

## ARCHIV — kolo #3

### Status: 🔴 FAIL — otázka je nula dál, jen o patro jinde: **108 vět**

**Kolo #3.** Commit `29b061f`. **Zkracování je opravdu pryč a je to
doložené**, šestý stav je správné rozhodnutí, `diff_behu.py` je dobrý
nástroj a přechodová čísla sedí do jedné věty. **Ale vada, kterou jsi
zavřel u dvojznačnosti, žije dál u největší třídy otázek.**

**Architectural Health Score: 9,3 / 10** — vrstva je lepší než v #2;
blokuje jedno konkrétní číslo, ne architektura.

---

## Co jsem ověřil sám a co drží

```
counts ze záznamu přepočítány po větách   ✔ 669 · 124 · 31 · 7 · 5 = 836
determinismus                             ✔ beh1 == beh2; navíc můj vlastní
                                             vzorek 9 vět dvakrát → shoda
nezkracování, doložené během               ✔ nalezy/bez_zkraceni.py: 1839 znaků,
                                             shoda znak po znaku
šest vět, které se přestaly zapisovat      ✔ všech 6 reprodukováno na živém jádře
jedenáct nově zapsaných                    ✔ Einstein / Krkonoše ověřeny zvlášť
přechody 20 · 11 · 18 · 7 · 6              ✔ diff_behu.py vrací přesně to
7 ze 135 položek zlaté sady                ✔ včetně první „Kolik zubů má dospělý pes?"
diff odmítne porovnat chybějící pole       ✔ „OTÁZKY — nelze porovnat"
```

**Šestý stav je správně a zdůvodnění sedí.** *„Větě nerozumím"* je mez
schopnosti, *„rozumím jí dvěma způsoby"* je položená otázka — to jsou
dva různé znalostní stavy a slít je znamená ztratit obojí. **Pět stavů
bylo rozhodnutí, ne dogma; tohle je vědomé šesté a je odůvodněné
v kódu.**

---

## Critical Blockers

### N‑10 · 108 vět se PTÁ a v záznamu má **nula otázek a prázdný seznam**

**Reprodukováno na živém jádře, ne přečteno ze záznamu:**

```
» Rys loví srnce a zajíce.
    verdikt        PTÁ SE
    otázka jádra   „Nevím, jakou roli hraje »zajíce« (obj>conj+Acc) —
                    do čtení se nedostalo. Jak se ta role jmenuje?"
    open_questions 0
    questions      ()
```

**To je slovo do slova ta vada, kterou jsi tohle kolo zavíral** — jen
místo dvojznačnosti ji nese **„Nevím, jakou roli hraje…"**, což je
**největší třída otázek v korpusu**.

**Rozsah, změřeno:**

```
PTÁ SE                                     669
  z toho s PRÁZDNÝM seznamem otázek        108   (16 %)
     „Nevím, jakou roli hraje…"            103
     „Věta nemá podmět…"                     4
     „Co ten přívlastek v genitivu tvrdí"     1
```

**A tohle je ten důkaz, že to není druhá osa, ale nesrovnalost v jedné:**

```
otázka „Nevím, jakou roli hraje…"  celkem   237
   započítána do seznamu                    134
   nezapočítána (oq = 0)                    103
```

**Táž otázka jednou počítá a podruhé ne.** Nerozhoduje o tom věta ani
otázka — rozhoduje **náhoda, jestli stopa zrovna nesla hranatou značku**.
`open_items()` čte `[CHYBÍ:…]`, `[NEZAKOTVENO:…]` a spol. ze stopy;
otázku samu nečte. Proto:

```
» Původ a studium = = =
    otázka  „Nevím, jakou roli hraje »studium« (nsubj>conj+Nom)…"
    seznam  NEZAKOTVENO: role co …  ·  NEZAKOTVENO: role jak …
```

**V seznamu není to, na co se systém ptal.** Jsou tam jiné otevřené věci,
které se v té větě náhodou vyskytly. **Seznam se tedy nejmenuje, čím
je.**

**Proč to blokuje, ne jen vadí:** `diff_behu.py` porovnává běhy
**seznamem otázek** — a přesně u těch 108 vět je seznam prázdný, takže
změna v tom, **na co se systém ptá**, je v porovnání **neviditelná**.
Postavil jsi nástroj proti slévání a nechal v něm slepé místo o velikosti
šestiny všech tázaných vět. Totéž dělá `render()`: `(N×?)` u nich
nenapíše nic.

**Co po tobě chci:** aby číslo i seznam pocházely **z otázky**, ne ze
stopy. Otázka existuje → seznam není prázdný. Když otázka nese víc věcí
najednou („role X, role Y"), rozpad je tvoje rozhodnutí a chci ho vidět
zdůvodněný — **ale nula, když se systém ptá, nesmí zůstat ani jednou.**

**A ověř to protipříkladem, ne součtem:** projdi všech 669 `PTÁ SE`
a ukaž, že **žádná** nemá prázdný seznam; a naopak ukaž, že věta, kde
jádro **mlčí**, prázdný seznam **má** — jinak jsi jen otočil vadu na
druhou stranu.

---

## Semantic Warnings

### W‑69 · záznam je z **rozdělaného** stromu měřicí vrstvy

```
utils: 1bdee3e … +dirty:1da9971e
```

**Čísla vyrobil kód, který v žádném commitu není.** Otisk `dirty` jsi
tam dal sám a je to správně — ale **u vrstvy, jejímž jediným úkolem je
reprodukovatelnost, je „reprodukovat to nejde" divná vlastnost**.
Doporučuji: **měřit až nad commitnutým stromem**, nebo do záznamu
uložit i diff. Netlačím na přeměření kvůli tomuhle samotnému — stejně
budeš měřit znovu kvůli N‑10.

### W‑70 · „důvod je u všech šesti týž" — není

Ověřil jsem to:

```
v+Loc/Geo   Babička v Táboře · Josef v Písku · Rodina v Kolíně
u+Gen/Geo   Vltava … u Mělníka
v+Loc       Marie … v květnu
Gen         Klíče OD CHATY … vede otázka na přívlastek, ne na v+Loc
```

**Rodina je táž** (nenaučený tvar → role), **věta ale ne.** Jsou to čtyři
různé tvary a jedna věta padá na něčem jiném. Drobnost, píšu ji proto,
že tady se měří — a „u všech týž" je tvrzení, ne shrnutí.

---

## Co zůstává otevřené z minula

**W‑67** (zkracování) **zavřeno**, doložené. HTML baseline (krok 5)
**nezačato a je to správné pořadí** — nemá smysl kreslit baseline nad
číslem, které se po N‑10 změní.

---

## Action Items for Agent 3

1. **N‑10 první, nic jiného.** Číslo a seznam ať vzniknou z otázky.
   Protipříklad výše: **žádná ptající se věta bez seznamu, žádná mlčící
   se seznamem.**
2. **Přeměř nad commitnutým stromem** (W‑69) a řekni, **o kolik se změnil
   součet otevřených věcí** — čekám velký skok, protože 108 vět dnes
   přispívá nulou. **Jestli skok NEVYJDE, chci vědět proč**, ne
   vysvětlení po faktu.
3. **Až potom HTML baseline.**

**Zbytek předávky je dobrá práce a nechci, aby to zapadlo:** doklad
nezkrácení během, ne úvahou; šestý stav se zdůvodněním v kódu; nástroj,
který **odmítne** porovnat chybějící pole místo aby napsal nulu. **To
poslední je přesně ten návyk, který v N‑10 ještě chybí.**

---

## ARCHIV — kolo #2

### Status: 🟢 PASS — krok 4 stojí, a nejlepší věta v předávce je varování před vlastním číslem

**Kolo #2.** Historický korpus conBondu2 změřen: **836 vět**, 22
dokumentů, `korpus: github.com/alchy/conBond2@418d7f7`, **kontrola
determinismu prošla**. Commity `31e22bc` a `38ed480`.

**Architectural Health Score: 9,2 / 10.**

---

## Můj counterexample z kola #1, položku po položce — ověřeno mnou

```
dva běhy nad touž revizí → SHODNÉ počty      ✔ determinismus.shoda = true
revize korpusu, jádra i utils v záznamu      ✔ všechny tři + otisk dirty + core_na_konci
etalon CELÝ včetně unsure a clarify          ✔ 135 položek: 111 answer · 13 unsure
                                                · 2 clarify · 9 bez mode
neměřené věty se nezamlčely                  ✔ unmeasured 3045, vypsáno
tvar je vlastní osa, označit a nemazat       ✔ věta 652 · bez slovesa 103 · nadpis 61
                                                · položka 17 · popiska 3
```

**`core_na_konci` jsi přidal sám a je to správná úvaha** — měřím
souběžně s Builderem jádra a razítko jen ze začátku by tvrdilo identitu,
kterou půlka běhu neměla.

**Nejlepší věta celé předávky je ta, kterou varuješ před vlastním
číslem:** *„unsure 13 z 13 splněno není úspěch — báze je prázdná, takže
`U` vyjde na cokoli."* **Přesně tak.** Kdo by to citoval jako „mlčení
funguje", tvrdí víc, než záznam ukazuje — a žes to napsal dřív, než to
někdo odcituje, je přesně ta péče, kterou tu vymáhám po všech.

**Vrstva `tvar` mi sedí na kus** — přepočítal jsem si to ze záznamu:

```
NEPŘEČTENO 149 = věta 50 · nadpis 48 · bez slovesa 48 · položka 2 · popiska 1
```

**Máš pravdu i v tom, že to není zpřesnění, ale jiný nález**: na
skutečných větách je to **6,0 %**, ne 17,8 %.

**Kategorie „KANDIDÁT na špatné čtení" a to, že z dvanácti obstály ruční
kontrolou čtyři**, je správně pojmenované. *„Číslo, které si nikdo
neprošel, by tvrdilo víc, než ukazuje."*

---

## Critical Blockers

### N‑5 · záznam je z jádra o PATNÁCT KOL staršího — a hlavní číslo dnes neplatí

Nese `core: f681902` = kolo **#92**. Dnes je jádro na **#107**
(`388d3c4`), a mezi tím leží **W‑62**, které zakázalo zapsat fakt
s rolí pojmenovanou tvarem.

**Změřil jsem, co to dělá:**

```
ZAPSÁNO v záznamu (jádro #92):   26
na dnešním jádře (#107):         20    ·   6 vět se UŽ NEZAPÍŠE
   Klíče od chaty visí v předsíni.     viset(…, v+Loc:∃předsíň)
   Babička bydlí v Táboře.             bydlet(…, v+Loc:·Tábor)
   Marie slaví narozeniny v květnu.    slavit(…, v+Loc:∃květen)
   Josef bydlí v Písku.                bydlet(…, v+Loc:·Písek)
```

**Všech šest je přesně ta třída, kterou W‑62 zavřelo.** Tvůj korpus tu
vadu obsahoval taky — a **oprava jádra se tím potvrdila na datech mimo
Wikipedii**, což je právě to, k čemu historický korpus je.

**A W‑U1 UŽ NENÍ ZABLOKOVANÁ.** Napsals, že přeměřit nejde, protože
`conbond4/` má rozdělaný strom. **Ověřil jsem to teď: strom je čistý**
(`git status` prázdný, HEAD `388d3c4`). Překážka padla.

---

## Semantic Warnings

**W‑U3 · čtyři zkreslení jednoho nástroje** — a všechna našel někdo jiný:

```
1. reason uříznut na 160 znaků    165 vět → ze záznamu 10   (diagnose.py 105/111/130/131)
2. dvojí text „nadpis: věta“      4 z 238 posláno jako jedna věta
3. otázka počítaná jako NULA      „Čtu to jako … které z toho?“ → NEPŘEČTENO, 0 otázek
4. hlášení 17 místo 35            jádro hlásí druhou větu u 35 vět
```

**Bod 3 je nejhorší a týká se i tvého historického čísla:** slévá
*„nepřečteno"* s *„přečteno dvojznačně, ptám se které"*, a **tvůj etalon
je těch otázek plný** — první položka, kterou jsem otevřel, je přesně
ona. Těch 149 tedy nemusí být 149.

**N‑7 a nález o zlaté sadě jsou obojí správně pojmenované.** Že by
z 32 odkazů **osm textů tiše vypadlo** kvůli předponě a diakritice, je
**potřetí táž rodina**, kterou v tomhle projektu potkáváme: *identita
vedená něčím, co o věci nic neříká* — nejdřív pozice, pak čas, teď
doslovná shoda jména.

---

## Action Items for Agent 3

**HTML baseline (krok 5) POČKÁ.** Postavit pohled nad čísly, o kterých
vím, že dvě z nich neplatí, znamená ta čísla jen zvětšit.

**(1) OTÁZKA NENÍ NULA A `reason` SE NEZKRACUJE.** Tyhle dvě opravy mění
tvá vlastní čísla, takže musí být první. *„Přečteno dvojznačně, ptám se
které"* je **vlastní stav**; jestli z toho vyjde **šestý stav**, je to
správný výsledek — pět jich bylo rozhodnutí, ne dogma. **Rozhodni
vědomě a napiš proč.** A vedle textu `reason` nes **strukturovaný seznam
otázek**, ať se dá porovnávat strojově, ne podřetězcem.

**(2) PAK PŘEMĚŘ HISTORICKÝ KORPUS NAD ČISTOU REVIZÍ.** Překážka padla,
ověřil jsem to. **Čekám `ZAPSÁNO` kolem 20 a `NEPŘEČTENO` níž než 149** —
obojí je můj odhad z jednoho průchodu, ne měření; **tvoje číslo
rozhoduje a jestli se rozejde s mým, chci vědět proč.**

**(3) TEPRVE POTOM HTML.**

**Můj counterexample, psaný jako vlastnost:** **žádné dva různé
znalostní stavy nesmí v záznamu splynout do jednoho čísla** —
u každé věty, kde jádro vrátilo otázku, musí být ze záznamu poznat, že
se ptalo; **žádné pole se nezkracuje** a doložíš to na větě s dlouhou
otázkou porovnáním se stopou jádra; **dva běhy nad touž revizí dál
dávají shodné počty**; záznam nese revizi korpusu, jádra i utils
a `core_na_konci`; **v novém záznamu je vidět, kolik vět se oproti #92
přestalo zapisovat a proč** — těch šest už mám, chci je potvrzené nebo
vyvrácené; a **zůstane vlastnost z kola #1**: u aspoň jedné věty jde
poznat rozdíl mezi *„rozbor rozuměl, inference to neuměla použít"*
a *„rozbor vyrobil špatné čtení"*.

---

## ARCHIV — kolo #2

### Status: 🟢 PASS — krok 4 stojí, a jeho záznam je o patnáct kol pozadu

**Kolo #2.** Historický korpus conBondu2 změřen: **836 vět**,
`korpus: github.com/alchy/conBond2@418d7f7`, revize jádra i měřicí
vrstvy v záznamu, **kontrola determinismu prošla** (dva běhy, shodné
počty ve všech stavech).

**Architectural Health Score: 9,0 / 10.**

---

## Ověřeno mnou, ne převzato

**Můj counterexample z kola #1, položku po položce:**

```
dva běhy nad touž revizí → SHODNÉ počty         ✔  determinismus.shoda = true
záznam nese revizi korpusu, jádra i utils        ✔  všechny tři, včetně otisku dirty
etalon projde CELÝ včetně unsure a clarify       ✔  135 položek: 111 answer · 13 unsure
                                                     · 2 clarify · 9 bez mode
neměřené věty se nezamlčely                      ✔  unmeasured 3045, vypsáno
tvar vstupu je vlastní osa                       ✔  věta 652 · bez slovesa 103 · nadpis 61
                                                     · položka 17 · popiska 3
```

**Označit a nemazat** jsi dodržel — nadpisy a fragmenty **nezmizely ze
jmenovatele**, dostaly vlastní hodnotu. To byla podmínka a je splněná.

**Etalon odpovídá `U` na všech 135 otázek.** Je to legitimní nula
a správně změřená měřicí nula — ne výsledek, který by se dal vylepšit
výběrem.

---

## Critical Blockers

### N‑5 · záznam historického korpusu je z jádra o PATNÁCT KOL staršího

Záznam nese `core: f681902` — to je kolo **#92**. Dnes je jádro na
**#107 (`388d3c4`)**, a mezi tím leží mimo jiné **W‑62**, které zakázalo
zapsat fakt s rolí pojmenovanou tvarem.

**Změřil jsem, co to dělá s hlavním číslem toho záznamu:**

```
ZAPSÁNO v záznamu (jádro #92):      26
na dnešním jádře (#107):            20   ·  6 vět se UŽ NEZAPÍŠE
   Klíče od chaty visí v předsíni.        viset(…, v+Loc:∃předsíň)
   Babička bydlí v Táboře.                bydlet(…, v+Loc:·Tábor)
   Marie slaví narozeniny v květnu.       slavit(…, v+Loc:∃květen)
   Josef bydlí v Písku.                   bydlet(…, v+Loc:·Písek)
```

**Všech šest je přesně ta třída, kterou W‑62 zavřelo** — fakt s rolí,
jejímž jménem je tvar. **Tvůj korpus tu vadu obsahoval taky** a nikdo to
nevěděl, protože se neměřilo znovu.

**Je to dvojí zpráva.** Ta dobrá: oprava jádra se **potvrdila na datech
mimo Wikipedii**, což je přesně to, k čemu historický korpus je. Ta
druhá: **záznam tvrdí číslo, které dnes neplatí**, a je to jediné číslo,
kterým se ta sada zatím prezentuje.

---

## Semantic Warnings

### W‑U3 · ČTYŘI zkreslení jednoho nástroje, a všechna našel někdo jiný

`cb-wiki.py` / `diagnose.py` zkreslily čtení diffu **čtyřikrát za deset
kol**, pokaždé v jiném místě:

```
1. reason uříznut na 160 znaků      165 vět → ze záznamu 10   (diagnose.py 105/111/130/131)
2. dvojí text „nadpis: věta“        4 z 238 posláno jako jedna věta
3. otázka počítaná jako nula        „Čtu to jako … které z toho?“ → NEPŘEČTENO, open_questions=0
                                     skutečné NEPŘEČTENO je 14, ne 16
4. hlášení 17 místo 35              jádro hlásí druhou větu u 35 vět
```

**Bod 3 je nejhorší z nich**, protože **slévá dva různé znalostní stavy**
— *„nepřečteno"* a *„přečteno dvojznačně, ptám se které"*. To je přesně
to, co má tenhle nástroj ze všeho nejvíc chránit.

**Píšu to jako varování, ne jako výtku:** nic z toho neublížilo bázi.
Ale **řídí se tím celý projekt** — Builder jádra i já jsme podle těch
čísel vybírali směr, a čtyřikrát nás poslala vedle.

**W‑U2 znovu · čtrnáct záznamů měření a čtyři nálezové skripty leží
nezakomitované.** Je to táž ironie jako v kole #1.

---

## Action Items for Agent 3

**POŘADÍ JE DANÉ TÍM, ŽE SE TVÝMI ČÍSLY ŘÍDÍ DVA DALŠÍ AGENTI.**

**(1) NEJDŘÍV ČTYŘI ZKRESLENÍ.** Dokud je záznam ořezaný a stavy slité,
je každé další měření nečitelné — včetně toho, o které tě žádám v bodě 2.

- `reason` **nezkracovat**; a vedle textu nést **strukturovaný seznam
  otázek**, ať se dá porovnávat strojově, ne podřetězcem.
- *„přečteno dvojznačně, ptám se které"* je **vlastní stav**, ne
  `NEPŘEČTENO`. Jestli z toho vyjde šestý stav, **je to správný
  výsledek** — pět jich bylo rozhodnutí, ne dogma; ale **rozhodni to
  vědomě a napiš proč**.
- otázka, kterou jádro vrátilo, se **nesmí počítat jako nula**.
- dvojí text (`nadpis: věta`) **rozdělit v segmentaci** — jádro už to
  umí pojmenovat, rozdělit to má měřicí vrstva.

**(2) PAK PŘEMĚŘIT HISTORICKÝ KORPUS NAD ČISTOU DNEŠNÍ REVIZÍ.**
Ne kvůli lepšímu číslu — kvůli tomu, aby to číslo platilo. **Čekám
`ZAPSÁNO` kolem 20**, ale to je můj odhad z jednoho průchodu, ne měření;
tvoje číslo rozhoduje.

**(3) ZAKOMITOVAT.** Čtrnáct záznamů a čtyři skripty. Záznam bez revize
je přesně to, co u ostatních měříš.

**Můj counterexample, psaný jako vlastnost:** **žádné dva různé
znalostní stavy nesmí v záznamu splynout do jednoho čísla** — konkrétně
u obou vět typu *„Čtu to jako … které z toho?"* musí být ze záznamu
poznat, že se jádro ptalo; **žádné pole se nezkracuje** a u aspoň jedné
věty s dlouhou otázkou to doložíš porovnáním se stopou jádra; **dva běhy
nad touž revizí dál dávají shodné počty**; záznam nese revizi korpusu,
jádra i utils; **v novém záznamu je vidět, kolik vět se oproti #92
přestalo zapisovat a proč** — u těch šesti to už vím, chci to od tebe
potvrzené; a **zůstane v něm ta vlastnost z kola #1**: u aspoň jedné
věty jde poznat rozdíl mezi *„rozbor rozuměl, inference to neuměla
použít"* a *„rozbor vyrobil špatné čtení"*.

---

## ZAŘAZENO DO FRONTY — až po bodech (1)–(3)

### Měřicí běh s PŘEDPŘIPRAVENÝMI ODPOVĚĎMI: kolik otázek je PRVNÍCH?

**Tohle je otázka, kterou nikdo za dvacet kol nepoložil, a je levná.**
Systém se učí **TVAR**, ne slovo — jedna odpověď `→@` zavře celou třídu
vět. Jenže `triage()` dává **každé větě čerstvé sezení**, takže se
naučené nikdy nepřenese. **Ověřil jsem, že jedno sezení bez odpovědí
nezmění nic** (25 vět Čapkova článku: 23 / 2, otázek 41 v obou
uspořádáních). **S odpověďmi to nikdo nezkusil.**

**Změřil jsem, co je v sázce** (korpus 238 vět, jádro `388d3c4`):

```
vět, kde se systém ptá na význam role     152
různých TVARŮ                              55   ·  jen jednou:  23
prvních 15 tvarů pokrývá                77 %   výskytů
různých DVOJIC (přísudek, tvar)           166   ·  jen jednou: 143
   v+Loc* : 47 výskytů u 33 RŮZNÝCH přísudků
```

**Dvojice `(přísudek, tvar)` je trojnásobně řidší než tvar sám** — 143
ze 166 se v korpusu vyskytne jedinkrát. **Učit se po slovesech tedy
z textu NEJDE**; tvar je správná jednotka a systém ji už umí.

**Co změřit:** jeden průchod korpusem, kde se **15 nejčastějších tvarů
zodpoví jednou** (tahem `→@`, ne konfigurací), a odpovědi **platí pro
celý běh**. Výstup je jediné číslo, které dnes nikdo nemá:

> **kolik z těch 152 vět se ptá jen proto, že se ptalo POPRVÉ.**

**Proč to rozhoduje směr:** jestli po patnácti odpovědích zbude pět
otázek, je automatizace hotová a jmenuje se `→@`. Jestli zbude sto, je
odpověď **valenční slovník** — a to je **verzovaná změna jádra (I‑13)**,
tedy vědomé rozhodnutí, ne vylepšení.

**Proč AŽ PO opravách:** dokud je `reason` uříznutý, otázka počítaná jako
nula a u zapsaných vět prázdná stopa, tomu číslu nepůjde věřit — a je to
číslo, podle kterého se rozhodne o architektuře.

**Můj counterexample, psaný jako vlastnost:** **odpovědi jsou TAHY, ne
konfigurace** — v záznamu je vidět, **kdo a kdy** ten tvar pojmenoval,
a jde to odvolat; **žádná odpověď se nesmí týkat konkrétní věty**, jen
tvaru (jinak měříš vlastní výběr); **běh bez odpovědí se změří TAKÉ**
a obě čísla stojí vedle sebe, protože rozdíl je ten výsledek, ne to
druhé číslo samo; **pět stavů se dál neslévá**; dva běhy nad touž revizí
dávají shodné počty; a **u vět, které se po odpovědích nově zapíšou,
chci u KAŽDÉ doložení z textu** — `ZAPSÁNO` smí růst jen tam, kde by to
potvrdil člověk čtoucí tutéž větu.

---

## ARCHIV — kolo #1

### Status: 🟢 PASS — kroky 1–3 hotové, u brány zastaveno správně

**Kolo #1.** Zadané kroky 1–3 udělané, krok 4 **nezačat** — přesně jak
stav žádal. To samo o sobě je dobré znamení: agent, který se u brány
nezastaví, je horší než agent, který postupuje pomaleji.

**Architectural Health Score: 9,0 / 10**

---

## Ověřeno mnou reprodukcí

**Záznamy měření sedí do jednoho** (přečteno z JSONů, ne z hlášení):

```
běh 1  238 vět · NEPŘEČTENO 49 · PTÁ SE 187 · CHYBA 2
běh 2  238 vět · NEPŘEČTENO 30 · PTÁ SE 206 · CHYBA 2
změnilo stav 21:   NEPŘEČTENO → PTÁ SE  20      PTÁ SE → NEPŘEČTENO  1
sám blokuje: morfologie 29 → 10
```

**Reprodukce N‑1 běží** (`python nalezy/shoda_cisla.py`). U mě padlo
**5 z 9** párů, ne 9 z 9 — a je to tak správně: měřím **po** opravě
W‑32 v pracovním stromě jádra. Zbylé dvě třídy jsou jiné příčiny, přesně
jak hlásí:

```
B · koordinovaný podmět     ✗ Petr a Pavel četli knihu.     [shoda čísla]
C · kvantifikovaný podmět   ✗ Přišlo několik hostů.         [shoda čísla]
KONTROLA                    ✓ Dítě spalo. · Město rostlo. · Psi štěkali.
                            kontrolních a protějších vět selhalo: 0
```

Kontrolní skupina je to, proč tomu věřím: kdyby padaly i jednoznačné
tvary, byla by příčinou složitost věty, ne rys.

**Jádra se nedotkl** — `git status` v `conbond4/` ukazuje jen práci
Buildera jádra (`REVIEW.md`, `cascade.py`, `grounding.py`).

---

## Čtyři věci, které si zaslouží být pojmenované

**1. Opravil mě, a měl pravdu.** `mode` v etalonu conBondu2 má **čtyři**
hodnoty, ne dvě: 80 `answer`, 4 `unsure`, **2 `clarify`**, 9 bez `mode`.
`clarify` je **přímý předek dnešního `PTÁ SE`** — tedy doptání bylo
plnohodnotným režimem už o dvě generace dřív. Můj první průchod to
minul; jeho zápis je přesnější.

**2. Historický nález, který stojí za celý ten průzkum.** Zlatá sada
conBondu2 se jednou **tiše rozbila**, protože odkazovala na věty
**pozicí**: po rozšíření korpusu z 12 na 34 článků spadla ze 100 % na
0 % a **nic to neohlásilo**. Odtud `dok`+`vd`. To je táž třída jako
všechno, co v jádře hlídáme — měření bez identity je horší než žádné —
a je to argument pro rozhodnutí, která teprve přijdou.

**3. Našel vadu ve své vlastní vrstvě a opravil ji dřív, než ji našel
někdo jiný.** `diagnose.py` tvrdil u 20 vět *„0 čtení a systém neumí
říct proč"*, jenže **jádro důvod řeklo** — posílá ho v otázce, ne
v řádku `[PROČ:`. Bylo to **tvrzení o jádře, které neplatilo**, tedy
přesně vada, kterou tady hlídáme u ostatních. Po opravě se těch 20
rozpadlo na `role_nenalezena` 12 + `rozbor` 5 + `kolize_rolí` 3 —
**stavy se nezměnily, změnilo se jen to, co o nich měření tvrdí.**

**4. Rozeznal zlepšení od ztráty špatného čtení.** Jedna věta šla
opačně (`PTÁ SE → NEPŘEČTENO`) a **není to regrese**: dřív přežilo
čtení, které za podmět dosadilo předmět věty. Poznat to jde **jen
proto, že záznam vede i `reading`, ne jen stav** — to je návrhové
rozhodnutí, které se vyplatilo hned v prvním kole.

---

## Critical Blockers

**Žádné v téhle dráze.** N‑1 je bloker **jádra**, ne měřicí vrstvy, je
předaný Builderovi jádra jako W‑32 a z dvou třetin už opravený.

---

## Semantic Warnings

**W‑U1 · běh 2 není reprodukovatelný — a je to ošetřené líp, než jsem
chtěl napsat.** Je nad **rozdělaným pracovním stromem** jádra, ne nad
revizí; hlásí to sám a název souboru to přiznává. **Navíc si sám
všiml, že holý příznak `+dirty` nestačí:** v `mereni/` leží dva záznamy
z jednoho dopoledne, oba stampované `d6782cb +dirty`, a jeden má
`NEPŘEČTENO` 30, druhý 49 — mezi běhy se oprava v pracovním stromě
jádra **objevila a zase zmizela**. Rozdělaný strom proto dostává otisk
`git diff HEAD` (`+dirty:166b7e06`).

To je táž lekce jako `dok`+`vd` u conBondu2, jen o generaci později:
**identita běhu nesmí být nic, co se dá dvakrát obsadit.** Zbývá jen
přeměřit po commitu W‑32 nad čistou revizí.

**W‑U2 · vlastní práce není zakomitovaná.** Je v tom jemná ironie:
N‑4 byl přesně o tom, že záznam bez revize jádra vypadá jako nestabilní
měření — a měřicí vrstva sama zatím revizi nemá. **Zakomitovat.**

---

## Odpovědi na čtyři otázky, na kterých stojí krok 4

**1 · Korpus conBondu2 do `data/` skriptem — ANO, ne submodul.**
Submodul vtáhne cizí text do každého klonu, a to je přesně to, co
`ZDROJ.md` zakazuje. Vést v záznamu **revizi conBondu2** místo revizí
jednotlivých článků je správně: ten korpus je **zmražený**, což je pro
měřicí nulu lepší vlastnost než živá Wikipedie.

**2 · `status` a `cituje` v etalonu — NEDOPLŇUJ, měř zatím `mode`
a `expect`.** Máš pravdu, že je to **rozhodnutí o očekávání**, ne
odvoditelný údaj — a rozhodnutí o očekávání udělané měřicí vrstvou by
znamenalo, že si měření píše vlastní zlato. Baseline má říct, **kde
systém stojí**, ne ho známkovat proti očekávání vymyšlenému teď. Až to
někdo doplní, ať je to vědomý akt se zapsaným důvodem.

**3 · Vrstva `tvar` — ANO, se třemi podmínkami.**
„Tohle nebyla věta" je **jiný stav** než „neuměl jsem to přečíst",
a slévat je znamená, že měření lže. Podmínky: (a) **označit, nemazat**
— přesně jako `Vyp=proza/seznam` v conBondu2, což je tvůj vlastní nález;
(b) **původní řetězec zůstává** v záznamu i v reportu; (c) pravidlo je
**obecné** (řádek bez určitého slovesa, nadpis), ne seznam konkrétních
vět. A označené položky **nesmí zmizet ze jmenovatele** — dostanou svůj
řádek, ne ticho.

**4 · Pořadí — runner nad HISTORICKÝM korpusem první, HTML nad ním.**
Parita s conBondem2/3 je **součást zadání, ne volitelné vylepšení**;
HTML nad Wikipedií by vypadalo jako pokrok, zatímco ta parita by pořád
nebyla. Navíc bys pohled stavěl dvakrát.

---

## Action Items pro Agenta 3

**KROK 4 — minimální reprodukovatelný runner nad korpusem conBondu2.**

1. Skript, který korpus stáhne do `data/` (mimo git) a zapíše **revizi
   conBondu2** do záznamu.
2. Celá relevantní sada, **nekrácená** na to, co conBond4 zvládne.
   Věty, které padnou, mají vlastní řádek s důvodem — to je celý smysl.
3. Pět stavů zvlášť, druh uvnitř vrstvy, `reading` v záznamu.
4. **Zakomitovat** (W‑U2) a po commitu W‑32 v jádře **přeměřit nad
   čistou revizí** (W‑U1).

**Můj counterexample:** dva běhy nad **touž revizí conBondu2 a touž
revizí jádra** vrátí **shodné počty ve všech vrstvách**; záznam nese
revizi korpusu, jádra i měřicí vrstvy; etalon projde **celý** včetně
9 `unsure` a 2 `clarify`; a u aspoň jedné věty jde ze záznamu poznat
rozdíl mezi *„rozbor rozuměl, inference to neuměla použít"* a *„rozbor
vyrobil špatné čtení"* — bez toho rozdílu je runner jen počítadlo.
