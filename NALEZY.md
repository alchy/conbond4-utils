# Nálezy

Co měřicí vrstva doložila. Každý nález má **reprodukci, kterou jde
pustit**, a čísla z běhu — ne z odhadu. Opravy v jádře **nedělám**;
`conbond4/` zůstává beze změny.

Běhy, ze kterých čísla jsou. **Dva**, protože jádro se mezi nimi
změnilo — a to je přesně to, co má být ze záznamu vidět:

| | běh 1 | běh 2 |
|---|---|---|
| záznam | `mereni/2026-08-15.json` | `mereni/2026-08-15-d6782cb-dirty-W32.json` |
| jádro | před `b4c7e89` (revize v záznamu **není** — viz N‑4) | `d6782cb` **+dirty**: pracovní strom s neodkomitovanou opravou W‑32 |
| orákulum | `udpipe2 model=cs_all-ud-2.17-251125 tokenizer=6247b8b7a5c8` | totéž |
| zdroje | `Domácí zvíře@24589916`, `Karel Čapek@26105343`, `Božena Němcová@25984882`, `Vesmír@26130989` | tytéž revize |
| vět | 238 (58 + 60 + 60 + 60) | tytéž věty |
| stavy | `PTÁ SE 187 · NEPŘEČTENO 49 · CHYBA 2` | `PTÁ SE 206 · NEPŘEČTENO 30 · CHYBA 2` |
| | `ZAPSÁNO 0 · ODMÍTNUTO 0` | `ZAPSÁNO 0 · ODMÍTNUTO 0` |

Běh 2 je nad **rozdělaným pracovním stromem** jádra, ne nad revizí.
Reprodukovat ho podle `d6782cb` nejde a záznam to přiznává příznakem
`+dirty` — proto je to v názvu souboru.

---

## N‑1 · Patro shody čísla zahazuje gramatické české věty — BLOCKER

**Reprodukce:** `python nalezy/shoda_cisla.py --korpus`

**Rozsah:** 29 vět z 238 (12,2 % korpusu), **59,2 % všeho `NEPŘEČTENO`**.
Ani jedna z těch 29 vět není negramatická. Jsou to tři třídy a **každá
chce jinou opravu**:

| třída | kolik | co to je | příklad z korpusu |
|---|---|---|---|
| **A** dvojhodnotový rys | 20 | příčestí na `-la` je tvarově `Fem Sing` i `Neut Plur`, rozbor to vrátí jako `Number=Plur,Sing`; patro porovnává rys jako **řetězec**, takže `"Sing" != "Plur,Sing"` | *Matka Božena Čapková sbírala slovesný folklor.* |
| **B** koordinovaný podmět | 7 | přísudek je v plurálu podle celé koordinace, `nsubj` je první člen v singuláru, zbytek visí jako `conj` | *Mnichovská dohoda a … kapitulace znamenaly …* |
| **C** kvantifikovaný podmět | 2 | čeština má u počitatelných výrazů přísudek v neutru singuláru a jméno v genitivu plurálu; shoda čísla tu z principu neplatí | *Nicméně existovalo mnoho právních ochran …* |

Třídy se překrývají (*„vzniklo několik kosmologií a kosmogonií"* je B i C);
zařazení bere koordinaci dřív, aby jedna věta nebyla ve dvou třídách.

**Minimální páry** — táž stavba, jediný rozdíl je to jedno. Padlo 9 z 9,
kontrolní skupina prošla 3 ze 3:

```
✓ Petr četl knihu.            Number=Sing        kandidátů 2 → zbylo 1
✗ Žena psala dopis.           Number=Plur,Sing   kandidátů 2 → zbylo 0
      [PROČ: shoda čísla — přísudek Plur,Sing, podmět musí být týž]

✓ Petr četl knihu.            Number=Sing        kandidátů 2 → zbylo 1
✗ Petr a Pavel četli knihu.   Number=Plur        kandidátů 2 → zbylo 0

✓ Přišel host.                Number=Sing        kandidátů 1 → zbylo 1
✗ Přišlo několik hostů.       Number=Sing        kandidátů 1 → zbylo 0

kontrola: Dítě spalo. ✓   Město rostlo. ✓   Psi štěkali. ✓
```

Kdyby byla příčinou složitost věty, padaly by obě strany páru. Padá
vždycky jen ta jedna a kontrolní skupina drží.

**Proč je to blocker, a ne capability gap.** `PTÁ SE` je legitimní tah:
systém přečetl a doptává se. Tady se ale **nečte nic** a věta zmizí do
téže škatule jako věta opravdu nesrozumitelná. Ztráta dobrého vstupu,
o které se dole neví, je horší než hlučná chyba: dokud tam ta třída
sedí, nejde na tomhle korpusu měřit **nic dalšího**, protože 12 %
vstupu se ani nedostane k dalším patrům.

Třída A je navíc **regrese vůči conBond2**. Tamní `baseline.py` bral
morfologický rys jako **množinu hodnot** a shodu ověřoval průnikem:

```python
rod = set(a.split("=", 1)[1].split(","))     # core/…/baseline.py: rod_cislo
if rod is not None and not (rod & osoba["rod"]):
    souhrn["neshoda"] += 1
```

Ta znalost — *„český rys smí nést víc hodnot naráz"* — v projektu už
jednou byla a v conBondu4 se ztratila.

**Co s tím (rozhodnutí je na Builderovi jádra, ne na mně):** A je vada
porovnání, ne chybějící schopnost — rys má dvě hodnoty a stačí je číst
jako množinu. B a C jsou chybějící schopnosti a je na rozhodnutí, jestli
mají patro projít, nebo se mají stát vlastní otázkou dialogu.

### Stav: třída A je v jádře opravená (pracovní strom, W‑32)

Během měření se objevila v pracovním stromě jádra oprava — rysy se
porovnávají **průnikem** (`feature_values`, `agrees`) a ke shodě čísla
přibyl rod. Změřeno na týchž 238 větách, týchž revizích článků a témž
modelu:

| | běh 1 | běh 2 | rozdíl |
|---|---|---|---|
| `PTÁ SE` | 187 | 206 | **+19** |
| `NEPŘEČTENO` | 49 | 30 | **−19** |
| `morfologie` (sám blokuje) | 29 | 10 | **−19** |

Po větách: **20 vět `NEPŘEČTENO → PTÁ SE`** a všech dvacet je třída A.
Zbylých 10 na shodě čísla je **7 × B + 2 × C + 1 věta níž** — třídy B a C
tedy oprava nekryje, což odpovídá tomu, že jsou to jiné příčiny.

**Jedna věta šla opačně** (`PTÁ SE → NEPŘEČTENO`) a stojí za to, protože
holé číslo by ji ukázalo jako regresi, a ona regrese není:

```
Několik nezávislých experimentálních měření tuto teoretickou inflaci
i teorii velkého třesku podpořilo.

  běh 1  PTÁ SE   podpořit(co: měření, kdo: teoretická inflace)   ← čtení je ŠPATNĚ
  běh 2  NEPŘEČTENO   [PROČ: shoda čísla — přísudek Sing, podmět se s ním shodnout nemůže]
```

Dřív přežilo čtení, které dosadilo za podmět **předmět věty** („inflace",
`Fem Sing`, shodou okolností v čísle sedící). Kontrola rodu ho zahodila.
Systém tedy nepřišel o čtení, přišel o **špatné** čtení — a spadl do
třídy C, kam ta věta patří (`Několik … měření … podpořilo`).

Bez `reading` v záznamu by tenhle rozdíl nešlo poznat od skutečné
regrese. To je důvod, proč se u každé věty vede i to, **jak** ji systém
přečetl, ne jen v jakém stavu skončila.

---

## N‑2 · Měření tvrdilo o jádře mlčení, které jádro nemlčelo — OPRAVENO

Nález **na mé vlastní vrstvě**, ne na jádře. V prvním záznamu skončilo
20 vět (8,4 % korpusu) s hláškou:

```
rozbor   20 (8.4 %)   „0 čtení a systém neumí říct proč"
```

To tvrzení **neplatilo**. Jádro důvod řeklo — `cascade.why_nothing`
skládá vysvětlení a posílá ho v **otázce**, kdežto `diagnose.py` ho
hledal výhradně v řádcích `[PROČ:`. Když ho tam nenašel, dosadil vlastní
větu o tom, že jádro mlčí:

```
» Toxické rostliny: Určité druhy pokojových rostlin mohou být …
  jádro řeklo: „Tuhle větu přečíst neumím: přísudek „rostliny“ nemá ani
               jeden člen, který bych uměl pojmenovat (rozbor dal amod, appos)."
  měření napsalo: „0 čtení a systém neumí říct proč"
```

Přesně ta vada, kterou tenhle repozitář hlídá u ostatních: **měření
tvrdilo víc (a jiného), než doložilo**. Po opravě se těch 20 vět rozpadlo
na tři různé příčiny, každou s jinou opravou:

| vrstva | dřív | teď | co to je |
|---|---|---|---|
| `role_nenalezena` | — | 12 | přísudek nemá ani jeden pojmenovatelný člen (rozbor dal `amod`, `appos`, `conj`) |
| `rozbor` | 20 | 5 | důvod jádra beze změny, nezařaditelný |
| `kolize_rolí` | — | 3 | dva jádrové členy dostaly touž roli |

Stavy se nezměnily (`PTÁ SE 187 · NEPŘEČTENO 49 · CHYBA 2`), změnilo se
jen to, co o nich měření tvrdí. Přibyl taky `kind` — druh **uvnitř**
vrstvy, slovy jádra: bez něj splynulo 20 vět shozených dvojhodnotovým
rysem s 9, kde jde o koordinaci a kvantifikaci.

---

## N‑3 · Do korpusu vstupují nadpisy a položky seznamu jako věty

Z 12 vět ve vrstvě `role_nenalezena` je většina **útvar, který není
výpověď**: *„Stres způsobený chováním zvířat"*, *„Úrazy způsobené
pády."*, *„Toxické rostliny: Určité druhy …"*. `wiki.py` zahazuje řádky
`== Nadpis ==`, ale odrážky a nadpisy s dvojtečkou projdou.

**Neznamená to je smazat.** conBond2 na to narazil dřív a vyřešil to
správně: 57 % „vět" tehdejšího korpusu nemělo slovesný kořen (bibliografie
a soupisy děl) a `baseline.py` je **označil** (`Vyp=proza` / `Vyp=seznam`)
místo aby je vyhodil — *„pole má být obraz textu a v článku ta
bibliografie je; zahodit půlku korpusu by navíc změnilo všechna dosud
naměřená čísla."*

Dokud se to neoznačí, plete se **„conBond4 tuhle větu neumí přečíst"**
s **„tohle vůbec nebyla věta"** — a to jsou dva různé nálezy. Návrh
řešení je v `MAPOVANI.md` (§ 4, vrstva `tvar`); je to preprocessing,
takže patří až za schválené mapování, ne před něj.

---

## N‑4 · Záznam měření nenesl revizi jádra — OPRAVENO

Druhý běh nad **týmiž revizemi článků a týmž modelem** vrátil u tří vět
jinou otázku než první. Ze záznamu nešlo poznat, jestli se změnilo jádro,
nebo jestli je měření nestabilní — a to je přesně ten rozdíl, kvůli
kterému se reprodukovatelnost vede. Změnilo se jádro (mezi běhy přibyly
`b4c7e89 kontext textu` a `d6782cb pro-drop`), ale muselo se to dohledávat
v cizím repozitáři.

Záznam teď nese identitu **trojmo** (`cb_utils/revize.py`): revize článku,
model orákula, revize jádra i měřicí vrstvy. Dva po sobě jdoucí běhy nad
týmž stromem vrátily shodné počty ve všech vrstvách.

**Příznak `+dirty` sám nestačil — a to je taky změřené.** V `mereni/`
leží dva záznamy z jednoho dopoledne, oba stampované `d6782cb +dirty`:

```
mereni/2026-08-15-w32.json        NEPŘEČTENO 30 · PTÁ SE 206
mereni/baseline-d6782cb.json      NEPŘEČTENO 49 · PTÁ SE 187
```

Mezi běhy se v pracovním stromě jádra objevila a zase zmizela oprava
shody. Pod **jednou identitou** tak ležely dva různé stavy kódu — táž
past jako keš rozborů bez identity modelu nebo zlatá sada odkazující na
věty pořadím (`STARE-FRAMEWORKY.md` § 2.6). Rozdělaný strom proto dostává
**otisk** `git diff HEAD`: `d6782cb … +dirty:166b7e06`. Neřekne, co se
liší, ale dva různé rozdělané stromy rozezná.

(Ty dva záznamy jsem nevytvořil já — `mereni/2026-08-15-w32.json`
a `mereni/baseline-d6782cb.json` přibyly v 8:54 a 8:56 z cizího běhu.
Nechávám je být, jsou to platná měření; jen je z nich vidět přesně ten
problém, který otisk řeší.)
