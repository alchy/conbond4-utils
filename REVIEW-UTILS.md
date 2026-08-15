# conbond4-utils — audit měřicí vrstvy

## Status: 🟢 PASS — kroky 1–3 hotové, u brány zastaveno správně

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
