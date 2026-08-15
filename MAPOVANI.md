# Mapování starého měření na conBond4 — NÁVRH K REVIZI

Krok 3 zadání. **Nic z toho není postavené**; předkládám to dřív, než to
postavím, přesně jak stav žádá. Co je hotové, je v `NALEZY.md`.

Přenáší se **principy a datový model**, ne implementace: conBond2 měřil
aktivační pole a odpovídač, conBond4 má kaskádu s patry, verdikty
`A/N/U/CONFLICT`, důkaz s citací a dialogové tahy.

---

## 1 · Tři režimy odpovědi → pět stavů čtení + čtyři stavy dotazu

conBond2 měl u každé položky režim: **odpověz** (`answer`) · **mlč**
(`unsure`) · **doptej se** (`clarify`). conBond4 má dvě různé osy a je
zásadní je **nesloučit**:

| osa | co měří | hodnoty |
|---|---|---|
| **čtení** (`triage.Verdict`) | co systém udělal s **větou na vstupu** | `ZAPSÁNO` · `PTÁ SE` · `NEPŘEČTENO` · `ODMÍTNUTO` · `CHYBA` |
| **dotaz** (`QueryStatus`) | co systém řekne na **otázku** | `A` (K φ) · `N` (K φ̄) · `U` · `CONFLICT` |

Starý režim se mapuje takhle:

| conBond2 | conBond4 — očekávaný výsledek |
|---|---|
| `answer` | dotaz vrátí `A` nebo `N` **a důkaz cituje větu**, ze které to je |
| `unsure` | dotaz vrátí `U` — a `U` **není chyba**, je to splněný závazek |
| `clarify` | tah dialogu: systém vrátí **otázku**, ne verdikt (`PTÁ SE` na straně čtení) |

`CONFLICT` v conBondu2 protějšek nemá — je nový a měří se zvlášť. Není
to čtvrtá pravdivostní hodnota, ale stav dotazu (jádro, § 4), takže do
skóre nesmí spadnout jako „chyba".

**Nesloučit `U` s `PTÁ SE`.** `U` je odpověď na otázku („o tomhle nic
nevím"), `PTÁ SE` je stav čtení („větě rozumím jen zčásti"). Sloučené by
z nich vzniklo jedno bezobsažné číslo.

---

## 2 · Datový model položky — co se přenáší z `etalon.json`

Starý tvar (`q`, `expect`, `mode`, `kind`, `dok`) drží pohromadě
a přidávají se **tři pole**, která conBond2 neměl a conBond4 umí:

```jsonc
{
  "q":      "Kolik zubů má dospělý pes?",
  "expect": ["42"],            // PODŘETĚZCE, ne přesná shoda (§ 2.2 STARE-FRAMEWORKY)
  "mode":   "answer",          // answer | unsure | clarify
  "kind":   "zvířata",         // doména — ať je vidět, kde to drhne
  "dok":    "pes_domácí",      // odkud to je; kontrola, že fakt v korpusu JE

  // nové, conBond4:
  "status": "A",               // očekávaný QueryStatus: A | N | U | CONFLICT
  "cituje": "pes_domácí#412",  // z které VĚTY má důkaz vycházet
  "premisa": ["dospělý pes"]   // co si systém smí právem vyžádat dialogem
}
```

- `expect` **zůstává podřetězcem** — jinak se měří tokenizace.
- `cituje` je nový závazek: nestačí správná odpověď, musí být **z té
  správné věty**. Odpověď se správnou hodnotou a špatnou citací je horší
  než `U`, protože vypadá jako znalost.
- `premisa` drží `clarify` poctivé: doptání na **tuhle** chybějící
  premisu je splnění, doptání na cokoli jiného ne.

---

## 3 · Dvoustupňová metrika → dvoustupňová i tady

conBond2: *zásah pole* × *zúžení*. Princip — **našel správný druh místa**
× **vybral v něm správnou věc** — platí dál, jen se měří na jiných
věcech:

| stupeň | conBond2 | conBond4 |
|---|---|---|
| 1. | zásah pole — je správná faktová šablona mezi kandidáty? | **čtení** — je správná predikace mezi kandidáty, které kaskádě zbyly? |
| 2. | zúžení — je zrovna ta nejčastější? | **rozhodnutí** — zbyla po patrech **jedna**, nebo se systém právem ptá? |

Obojí zvlášť, nikdy jako součet. Věta, kde správné čtení mezi kandidáty
**bylo** a kaskáda se doptala, je úplně jiný stav než věta, kde správné
čtení vůbec nevzniklo — první je hranice rozhodování, druhá hranice
generátoru.

**Křížové měření** (`mereni.py`: mapování ze všech položek kromě zkoumané)
přenáším tam, kde se bude měřit **naučené** — lexikon a role. U kaskády
nemá smysl, ta se neučí z měřené sady.

---

## 4 · Vrstvy: kde věta uvázla

Zadání jmenuje vrstvy (segmentace, morfologie, závislostní rozbor,
koreference, identifikace entity, syntaktická interpretace, lexikální
mapování, převod do AST, inference, dialogové doplnění premisy).
Současný `diagnose.py` jich pojmenovává třináct a čte je **ze stopy
a otázky jádra**. Návrh dvou změn:

1. **Vrstva `tvar`** — nová a **před** vším ostatním: nadpis, položka
   seznamu, bibliografie. Označit, nesmazat (conBond2, § 2.5). Bez toho
   se plete *„neumím přečíst"* s *„tohle nebyla věta"* (`NALEZY.md` N‑3).
   Původní řetězec zůstává v záznamu vedle, jak žádá pravidlo 2.
2. **`kind` uvnitř vrstvy** — už zavedeno (`shoda_čísla`, `pádová_mřížka`,
   `bez_čtení`). Vrstva říká, **kde** se to opravuje, druh **co**.

Vrstvy `inference` a `dialogové doplnění premisy` zatím **nemají co
měřit**: na tomhle korpusu se nic nezapsalo, takže se k nim žádná věta
nedostane. Doplní se, až první věta projde — dřív by to bylo pokrytí,
které pokrytím není.

---

## 5 · Korpus

| zdroj | role | v gitu |
|---|---|---|
| `conBond2/data/raw/` — 65 článků, 208 064 slov | **historický korpus, základ** | ne (CC BY‑SA, `ZDROJ.md`) |
| `conBond2/data/gold/etalon.json` — 40 ručních | **etalon**, přenáší se celý včetně 9 `unsure` | ano (vlastní dílo) |
| `conBond2/data/gold/conbond.json` — 95 | kontinuita ještě staršího conBondu, včetně 2 `clarify` | ano |
| `conBond2/data/gold/otazky.json` — 682 | regresní sada, **ne primární** (§ 3 STARE-FRAMEWORKY) | ano |
| `conBond3/.../testbed-kdo-kde-kdy.txt` | krátké věty, hranice schopnosti | ano |
| Wikipedie přes `cb-wiki.py` | **rozšíření, ne náhrada** | ne |

Sada se **nekrátí na to, co conBond4 zvládne**. Věty, které padnou,
mají v reportu vlastní řádek s důvodem — to je celý smysl.

Otevřená otázka pro Reviewera: `conBond2/data/raw/` je cizí text pod
CC BY‑SA a do gitu nepatří, ale **měření nad ním musí být
reprodukovatelné**. Návrh: stahovat ho z conBondu2 skriptem do `data/`
(mimo git) a v záznamu vést revizi conBondu2, ne revize jednotlivých
článků — ten korpus je zmražený, což je pro měřicí nulu lepší než živá
Wikipedie.

---

## 6 · Co bude v HTML baseline (krok 5) — jen obrys

Ne teď; ať je vidět, kam mapování míří. Jedna věta = jeden rozklad:

```
původní řetězec → (normalizace, když byla — vedle, ne místo)
  → rozbor: tokeny, rysy, závislosti
  → kandidátní čtení z generátoru        (kolik jich bylo)
  → patra kaskády: které co zahodilo     (doslova ze stopy)
  → predikace, role, zakotvení
  → verdikt čtení + otázka / důvod odmítnutí / důvod nepřečtení
  → dotaz nad tím, co vzniklo: A / N / U / CONFLICT + důkaz s citací
```

Vazba na důkaz musí rozlišit tři různé věci: **rozbor rozuměl, inference
to neuměla použít** · **rozbor vyrobil špatné čtení** · **chybí znalost**.
První se pozná tak, že predikace vznikla a dotaz vrátil `U`; druhá tak,
že predikace vznikla a neodpovídá větě; třetí tak, že `U` má `gap`.

Agregace: pět stavů zvlášť, rozpis po tématech, po vrstvách, po druzích
uvnitř vrstvy, nejhorší věty podle počtu otevřených otázek. **Nikdy jeden
FAIL místo pěti stavů.**

---

## 7 · Na co potřebuju odpověď, než začnu stavět

1. **Korpus conBond2 do `data/` skriptem** — souhlas s § 5? Alternativa
   je git submodul, ale ten by cizí text vtáhl do klonu.
2. **`status` a `cituje` v etalonu** — mám je doplňovat ručně ke všem 40
   položkám, nebo nechat prázdné a měřit zatím jen `mode` a `expect`?
   Ruční doplnění je práce na dvě kola a je to **rozhodnutí o očekávání**,
   ne odvoditelný údaj.
3. **Vrstva `tvar`** (§ 4.1) — je to preprocessing, takže podle pravidla 2
   chci potvrdit, že označení nadpisu a položky seznamu je „obecná
   normalizace", ne úprava vstupu ve prospěch výsledku.
4. **Pořadí kroků 4 a 5** — postavit runner nad historickým korpusem
   dřív, nebo HTML nad tím, co už měřím (238 vět z Wikipedie)? Druhé dá
   Revieweru dřív něco k proklikání, první je pořadí ze zadání.
