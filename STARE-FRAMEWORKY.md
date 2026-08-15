# conBond2 a conBond3 — co z toho má cenu přenést

Krok 1 a 2 zadání. Nejdřív **ověření Reviewerova průchodu**, pak to, co
vývojáři při stavbě conBondu2 a 3 opravdu pomáhalo — a co ne.

Čteno z `github.com/alchy/conBond2` (revize `418d7f7`, 2026‑08‑01)
a z místní pracovní kopie `conBond3` (`github.com/alchy/conBond3`).

---

## 1 · Ověření Reviewerova prvního průchodu

Přepočítáno, ne přejato. Vše sedí a dvě věci jsou navíc:

| tvrzení Reviewera | ověřeno |
|---|---|
| `data/raw/` 65 článků, 208 064 slov | **ano** — 65 souborů `.txt`, 208 064 slov |
| obsahuje `karel_čapek`, `božena_němcová`, `pes_domácí`, `kočka_domácí`, `kůň_domácí`, `koza_domácí`, `králík_domácí` | **ano**, a k tomu `ovce_domácí`, `prase_domácí`, `včela_medonosná`, `skot` |
| `otazky.json` 682 generovaných | **ano** — 682 položek, 34 dokumentů, `typ` jen `Typ=cas` (393) a `Typ=misto` (289) |
| `etalon.json` 40 ručních, `mode` = `answer` / `unsure` | **ano** — 31 `answer`, **9 `unsure`**, 7 domén (`zvířata`, `věci`, `životopisy`, `zápory`, `role`, `téma`, `bible`) |
| `conbond.json` 95 položek ze staršího conBondu | **ano** — a **`mode` má čtyři hodnoty**, ne dvě: 80 `answer`, 4 `unsure`, **2 `clarify`**, 9 bez `mode` |
| dvoustupňová metrika v `mereni.py` | **ano** — *zásah pole* × *zúžení*, křížově |

**Navíc oproti prvnímu průchodu:**

1. **`clarify` je třetí režim, ne varianta `unsure`.** V `conbond.json` je
   jen dvakrát, ale `etalon.py` ho drží jako scénář (*„shodné jméno se
   nehádá" → `Kdo je Novák?` → očekává `upřesni`*). Tři režimy odpovědi —
   *odpověz · mlč · doptej se* — jsou přímý předek pěti stavů conBondu4
   a mapování na ně je v `MAPOVANI.md`.
2. **Sada se jednou tiše rozbila a nikdo se to nedozvěděl.** Zlatá sada
   odkazovala na věty **pozicí v korpusu**; po rozšíření z 12 na 34
   článků ukazovala jinam a spadla ze 100 % na 0 %, *„aniž by to cokoli
   ohlásilo"* (`baseline.py`, `krok_zapis`). Odtud `dok` + `vd` v každé
   položce. Pro conBond4 to znamená: **věta se identifikuje původem, ne
   pořadím**.
3. **`mereni.py` měří křížově** — mapování se staví ze *všech* otázek
   kromě té zkoumané, aby se neměřilo zapamatování. To je vlastnost
   metriky, ne implementační detail.
4. **conBond3 přidává `zodpoveditelna: true/false`** — týž závazek jako
   `unsure`, jen v datech místo v režimu, a `TEST_STRATEGY.md` k němu
   dodává **tři nezávislá orákula** a **pojistky proti vakuu** (test,
   jehož podmínka nikdy nenastala, spadne).

---

## 2 · Co bylo diagnosticky cenné

Kritérium: pomohlo to někoho dovést k opravě? Věci níže jsou v kódu
doložené komentářem, který popisuje **konkrétní nález** — čísla, chybu,
následek.

### 2.1 · `mode: unsure` — mlčení je měřený výsledek

```
MLČENÍ SE POČÍTÁ. Stroj, který si vymyslí, je horší než stroj, který
mlčí — proto je `unsure` plnohodnotný režim a ne poznámka pod čarou.
```

Devět ze 40 položek etalonu má správnou odpověď „nevím". Kdyby se
skórovalo jedním číslem, systém, který na všechno něco plácne, by
vypadal líp než systém, který pozná svou mez.

**Přenosné beze zbytku.** V conBondu4 tomu odpovídá `PTÁ SE` a `U`.

### 2.2 · `expect` jako podřetězce

```
Odpověď je úsek textu v pádu, jaký si žádá věta („v Židenicích"),
a trvat na hranici úseku znamená měřit tokenizaci, ne odpověď.
```

Kdo trvá na přesné shodě, měří tokenizér. **Přenosné**, a v conBondu4
o to naléhavěji: důkaz nese citaci a citace má hranice.

### 2.3 · Dvoustupňová metrika: zásah pole × zúžení

```
zásah pole   je správná faktová šablona MEZI těmi, na které vzor
             dotazu ukazuje?
zúžení       vybere se v tom poli správná instance?
```

Dvě různé schopnosti, dvě čísla. Jedno skóre by trestalo to, co je
záměr. **Přenosný je princip, ne implementace** (aktivační pole conBond4
nemá): *našel systém správný druh místa* × *vybral v něm správnou věc*.

### 2.4 · `baseline.py` — pro‑drop řešený viditelně v datech

Nejcennější kus starého kódu. Řeší pro‑drop **bez přidávání slov do
textu**: sloveso dostane aktivace `Kor=prodrop` / `Kor=zajmeno` /
`Ent=<kdo>` a skript vypíše, **kolik případů zasáhl a kolik z nich
potvrdila shoda rodu a čísla**.

```
Nepřidáváme kvůli tomu do textu slova, která tam nejsou — pole má
zůstat obrazem textu. […] Je to heuristika, ne rozřešení koreference.
Kolik případů to zasáhne a kolik z nich shoda rodu potvrdí, skript
vypíše — ať se dá posoudit, čemu se dá věřit.
```

Čtyři měření, která z toho vypadla, a každé změnilo kód:

| nález | číslo | oprava |
|---|---|---|
| `nsubj` se bral odkudkoli z věty | pro‑drop nalezen jen v **83 z 3478** vět | podmět **kořene**, ne libovolný |
| filtr `Person=3` | zahodil **1188 z 1588** slovesných kořenů — čeština v minulém čase osobu na slovese nenese | příčestí implikuje 3. osobu |
| entita jen tam, kde podmět chybí | **913 z 3478 vět (26 %)** má vlastní pojmenovaný podmět a entitu nedostalo žádnou | doplnit i u pojmenovaného |
| jmenný přísudek („X byl prozaik") | koreference se na něj vůbec nepodívala — a je to věta, která říká, **kdo ten člověk je** | kořen = sloveso **nebo** spona |

Tohle je vzor, jak má vypadat nález v tomhle repozitáři: **jev, počet,
podíl, důsledek**.

### 2.5 · Označit, ne smazat

```
NEMAŽE SE TO. Pole má být obraz textu a v článku ta bibliografie je;
zahodit půlku korpusu by navíc změnilo všechna dosud naměřená čísla.
Místo toho se to OZNAČÍ a kdo měří výpovědi, si odfiltruje.
```

57 % „vět" nemělo slovesný kořen — byly to soupisy děl a cizojazyčná
bibliografie. Dvě věci naráz: vysvětlilo to i **vzory, které v poli
neseděly** (šablona plná `als`, `arts`, `bei` je vzor cizojazyčné
bibliografie, ne češtiny). **Přímo použitelné** — viz `NALEZY.md` N‑3.

### 2.6 · Identita se nesmí odvozovat z pořadí ani z křestního jména

```
První pokus bral z věty první PROPN v podmětu a dostal „bohumil",
„božena", „karel" — tedy holá křestní jména. To je přesně díra […]:
fakt navěšený na „Karel" patřil všem sedmadvaceti Karlům v korpusu.
```

Plus rozbitá zlatá sada z § 1.2. Dvakrát táž třída chyby: **identita
z něčeho nestabilního**. V conBondu4 se to vrací jako revize jádra
v záznamu měření (`NALEZY.md` N‑4).

### 2.7 · Brána do pole

`etalon.py` kontroluje zvlášť, kolik otázek **vůbec neprojde** do
vyhodnocení (`je_na_obsah`). Bez toho by otázka odfiltrovaná dřív
vypadala jako „neuměl odpovědět". Pro conBond4: **odlišit „nedostal se
tam" od „nedokázal to"**.

### 2.8 · `translate="no"` v HTML

```html
<!-- Bez `lang` si Chrome jazyk domyslí a stránku přeloží; a překlad se
     nedrží textu, sahá i na DATA — z „Trida=pomocny" udělal „Class=help".
     Na obrazovce pak stojí jména atributů, která v poli nejsou. -->
```

Drobnost, která zabíjí důvěru v report: prohlížeč přeloží jmenovky
rozboru a člověk se dívá na data, která neexistují. **Do HTML baseline
patří hned.**

---

## 3 · Co bylo v kódu, ale diagnosticky se to neosvědčilo

- **`otazky.json` (682 položek) samo o sobě.** Otázky mají odpověď
  *z konstrukce* — vznikly z návěsek, které v korpusu leží. Měří, jestli
  systém najde, co tam bylo položeno, ne jestli umí odpovídat; `etalon.py`
  si to o sobě říká sám. Přenášet jako **primární** sadu nemá cenu, jako
  regresní ano.
- **Cache ConceptNetu** (`synonyms.json`, 177 kB; `conceptnet_cache.json`,
  172 kB). Externí lexikální zdroj, který conBond4 z principu nemá —
  jádro stojí na vlastním lexikonu a na dialogu.
- **Prohlížeč pole** (`pole.html`, 127 kB + `js/`). Je to **inspektor
  živého stavu** — záložky Facts / Query / Vzory / Vazby / Matice,
  přepínání poloměrů. Ukazuje datovou strukturu, ne cestu jedné věty od
  textu k rozhodnutí. conBond4 potřebuje to druhé; **přenáší se řemeslo**
  (`translate="no"`, plátno místo responzivní stránky, sbalený výklad),
  ne struktura.
- **`experiment_*.py`, `uc.py`, `kotvy.py`** — jednorázové sondy do
  tehdejší architektury. Historie, ne materiál.
