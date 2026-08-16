# conbond4-utils

Nástroje kolem conBondu4, které **nepatří do jádra**: obstarání textu,
rozdělení na věty a měření, co si s nimi jádro dnes počne.

Jádro (`conbond4`) zůstává bez závislosti na síti a bez cizích dat.
Tenhle repozitář je ta druhá strana — sahá ven, a proto stojí zvlášť.

## K čemu to je

Znalostní sada conBondu4 rostla z vět, které jsme si vymysleli. To má
strop: vymyšlená věta je vždycky o něco jednodušší než ta, kterou by
někdo doopravdy řekl. `cb-wiki.py` vezme téma z Wikipedie, rozdělí ho
**touž službou**, která pak větu rozebírá, a u každé věty změří, kam až
se dostane.

**Nic se nevybírá za člověka.** Akceptační doména je rozhodnutí, ne
výstup filtru — skript jen říká, kde systém stojí.

## Použití

```bash
python cb-wiki.py "Karel Čapek" --vet 40
python cb-wiki.py                      # témata z temata.txt
python cb-wiki.py "Vesmír" --ulozit    # text do data/ (mimo git)
python cb-wiki.py --stav NEPŘEČTENO    # jen jeden stav
```

Potřebuje **běžící `cb-udpipe`** (viz `conbond4-deps`) a vedle sebe
naklonovaný `conbond4` — cesta se odvozuje ze sourozeneckého adresáře.

## Stavy

| stav | znamená |
|---|---|
| `ZAPSÁNO` | přečteno a uloženo do báze |
| `PTÁ SE` | přečteno neúplně, systém se ptá |
| `DVOJZNAČNÉ` | přečteno **víc způsoby**, systém se ptá který |
| `NEPŘEČTENO` | 0 čtení; patro nebo generátor řekl proč |
| `ODMÍTNUTO` | čtení bylo, zápis se odmítl (kruh, ireflexivita…) |
| `CHYBA` | parser nebo služba selhaly |

Řadí se podle `(n×?)` — **kolik věcí systém u té věty neví**. Není to
délka ani počet čárek, ale počet otázek, na které by člověk musel
odpovědět, než se věta zapíše. Nula znamená „zapsalo se to samo".

## Měření (4 témata, 238 vět)

Dva běhy nad **týmiž větami a týmiž revizemi článků**; mezi nimi se
změnilo jádro (oprava W‑32 — rysy se porovnávají průnikem, ne rovností):

```
běh 1   PTÁ SE 187 · NEPŘEČTENO 49 · CHYBA 2 · ZAPSÁNO 0
běh 2   PTÁ SE 206 · NEPŘEČTENO 30 · CHYBA 2 · ZAPSÁNO 0

vrstva            vyskytuje se  sám blokuje    (běh 2)
role               205 (86.1 %)   39 (16.4 %)
kvantifikace       163 (68.5 %)    1 ( 0.4 %)
koreference         16 ( 6.7 %)    0 ( 0.0 %)
role_nenalezena     12 ( 5.0 %)   12 ( 5.0 %)
konstrukce          11 ( 4.6 %)    0 ( 0.0 %)
morfologie          10 ( 4.2 %)   10 ( 4.2 %)   všech 10 · shoda_čísla
rozbor               5 ( 2.1 %)    5 ( 2.1 %)
kolize_rolí          3 ( 1.3 %)    3 ( 1.3 %)
segmentace           2 ( 0.8 %)    2 ( 0.8 %)
```

**Ani jedna věta z encyklopedické prózy se nezapsala sama.** Nejblíž jsou
věty s jednou otevřenou otázkou (*„Jako nemístné viděl v tehdejší situaci
hledání viníků."*), typické souvětí jich má pět až sedm.

`NEPŘEČTENO` v běhu 1 **nepadalo na tvrdých patrech oprávněně**: 29 z 49
shodil filtr shody čísla a ani jedna z těch vět nebyla negramatická —
doloženo minimálními páry v `nalezy/shoda_cisla.py`, popsáno v
`NALEZY.md` (N‑1). Oprava jádra 20 z nich uvolnila; zbylých 10 jsou
koordinovaný a kvantifikovaný podmět, tedy jiné příčiny.

Záznam každého běhu nese revizi článku, model orákula **i revizi jádra**
(`mereni/<datum>-<sha>.json`) — bez té třetí vypadá změna jádra jako
nestabilní měření.

## Historický korpus conBondu2 (krok 4)

```bash
python cb-korpus.py --vet 40 --dvakrat --json mereni/korpus-2026-08-16-1050.json
```

Korpus se klonuje do `data/` (mimo git, CC BY‑SA) a v záznamu je jeho
**revize** — je zmražený, takže na rozdíl od Wikipedie se měřicí nula
mezi běhy nepohne. 22 dokumentů, ke kterým existuje ruční zlatá sada,
836 vět, jádro `27c6a62`:

```
PTÁ SE 666 · NEPŘEČTENO 124 · ZAPSÁNO 34 · DVOJZNAČNÉ 7 · CHYBA 5 · ODMÍTNUTO 0
```

Dva běhy nad touž revizí korpusu i jádra vrátily **shodné počty ve všech
vrstvách**. Zlatá sada projde celá (135 položek včetně 9 `unsure`
a 2 `clarify`) a končí zatím na `U` — báze je prázdná, takže je to
měřicí nula, ne skóre.

Porovnání dvou běhů dělá `nalezy/diff_behu.py` — po větách, ne procentem:
běh, kde se deset vět nově zapsalo a deset jiných přestalo zapisovat,
vypadá v součtu jako beze změny.

Záznamy se jmenují `korpus-RRRR-MM-DD-HHMM.json` a ten tvar **není
kosmetika**: skripty berou bez argumentu poslední záznam podle jména,
a dokud se běhy jmenovaly `…-08-16.json` a `…-08-16-b.json`, vycházel
jako poslední ten **starší** (pomlčka je v abecedě před tečkou).

## HTML baseline (krok 5)

Diagnostická mapa, ne log v HTML: jeden soubor bez sítě, u každé věty
původní řádek ze zdroje, tvar vstupu, rozbor, stopa kaskády, čtení a
otevřené věci **seznamem**. Nahoře šest stavů zvlášť a sedm druhů otázek
zvlášť — jedno číslo místo nich by zahodilo přesně to, co se dvě kola
opravovalo. Filtruje se stavem, tvarem, vrstvou, druhem otázky a
dokumentem; věty se řadí podle počtu otevřených věcí, ne podle délky.

### Jak ji vyrobit od nuly

Mapa je **odvozená** — nese jen to, co je v záznamu měření. Celý řetěz:

```bash
# 1. co musí běžet vedle (jednou)
#    - služba cb-udpipe na 127.0.0.1:42200   (viz conbond4-deps)
#    - jádro conbond4 jako SOUROZENECKÝ adresář ../conbond4

# 2. měření: korpus conBondu2 → záznam
#    (korpus se sám naklonuje do data/, mimo git)
python cb-korpus.py --vet 40 --dvakrat --json mereni/korpus-2026-08-16-1050.json

# 3. záznam → mapa
python cb-html.py --do mereni/baseline.html      # bez argumentu vezme poslední záznam

# 4. otevřít
#    - dvojklikem na soubor, nebo
python -m http.server 8731 --directory mereni    # a jít na /baseline.html
```

Krok 2 trvá jednotky minut (836 vět × rozbor a kaskáda) a **je to ta
drahá část**; krok 3 je vteřina a dá se opakovat nad týmž záznamem, kolik
je potřeba. Proto jsou to dva skripty a ne jeden: kdo mění pohled,
nemá důvod znovu měřit — a hlavně by při tom měřil **jiné jádro**, což
je přesně ten druh tichého posunu, který se tady hlídá.

Záznamy v `mereni/` a `baseline.html` jsou v gitu proto, že bez nich by
po pull nešlo porovnat dva běhy a čísla v `NALEZY.md` by se musela brát
na slovo.

**Je v tom ale otevřená věc a nemá se přehlédnout:** záznam nese celé
věty korpusu, a ty jsou **cizí text pod CC BY‑SA**. Pravidlo 7 zadání
říká, že cizí text do gitu nepatří, pokud to není licenčně nutné —
a tady je to nutné *měřicky*, ne licenčně: bez věty v záznamu nejde
zpětně zjistit, na co se systém ptal. Možnosti jsou tři a rozhodnutí
není moje: nechat a doplnit atribuci podle CC BY‑SA (licence to dovoluje
se share‑alike), ukládat místo textu otisk věty (pak ale mapa přestane
být čitelná), nebo držet záznamy mimo git a přijít o porovnatelnost po
pull. Vedeno v `ZDROJ.md`.

## Kde co je

| soubor | co v něm je |
|---|---|
| `NALEZY.md` | co je doloženo, s čísly z běhu a s reprodukcí |
| `STARE-FRAMEWORKY.md` | conBond2/3 — co z nich má cenu přenést a co ne |
| `MAPOVANI.md` | návrh mapování starého měření na conBond4 (k revizi) |
| `nalezy/` | spustitelné reprodukce nálezů |
| `mereni/` | záznamy běhů |
| `cb-wiki.py` | měření nad živou Wikipedií (rozšíření) |
| `cb-korpus.py` | měření nad zmraženým korpusem conBondu2 (základ) |
| `cb-html.py` | záznam → diagnostická mapa v HTML |

## Co tu vědomě není

Vlastní dělič vět ani vlastní čistič HTML. Obojí by se rozešlo s tím,
co dělá služba a co vrací API — a rozdíl by se poznal až na výsledcích.
