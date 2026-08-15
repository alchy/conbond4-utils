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
python cb-korpus.py --vet 40 --dvakrat --json mereni/korpus-2026-08-15.json
```

Korpus se klonuje do `data/` (mimo git, CC BY‑SA) a v záznamu je jeho
**revize** — je zmražený, takže na rozdíl od Wikipedie se měřicí nula
mezi běhy nepohne. 22 dokumentů, ke kterým existuje ruční zlatá sada,
836 vět:

```
PTÁ SE 656 · NEPŘEČTENO 149 · ZAPSÁNO 26 · CHYBA 5 · ODMÍTNUTO 0

ručně psané soubory   4 dok ·  74 vět · ZAPSÁNO 24 (32 %)   · NEPŘEČTENO   0
encyklopedické články 18 dok · 762 vět · ZAPSÁNO  2 (0,3 %) · NEPŘEČTENO 149
```

Dva běhy nad touž revizí korpusu i jádra vrátily **shodné počty ve všech
vrstvách**. Zlatá sada projde celá (135 položek včetně 9 `unsure`
a 2 `clarify`) a končí zatím na `U` — báze je prázdná, takže je to
měřicí nula, ne skóre.

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

## Co tu vědomě není

Vlastní dělič vět ani vlastní čistič HTML. Obojí by se rozešlo s tím,
co dělá služba a co vrací API — a rozdíl by se poznal až na výsledcích.
