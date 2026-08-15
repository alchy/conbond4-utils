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
| `NEPŘEČTENO` | 0 čtení; patro řeklo proč |
| `ODMÍTNUTO` | čtení bylo, zápis se odmítl (kruh, ireflexivita…) |
| `CHYBA` | parser nebo služba selhaly |

Řadí se podle `(n×?)` — **kolik věcí systém u té věty neví**. Není to
délka ani počet čárek, ale počet otázek, na které by člověk musel
odpovědět, než se věta zapíše. Nula znamená „zapsalo se to samo".

## První měření (4 témata, 236 vět)

```
CELKEM  PTÁ SE 187 · NEPŘEČTENO 49 · CHYBA 2 · ZAPSÁNO 0
```

**Ani jedna věta z encyklopedické prózy se nezapsala sama.** Nejblíž jsou
věty s jednou otevřenou otázkou (*„Jako nemístné viděl v tehdejší situaci
hledání viníků."*), typické souvětí jich má pět až sedm. `NEPŘEČTENO`
padá na tvrdých patrech — shoda, pádová mřížka — a to je správně: věta,
které systém nerozumí, se nemá zapsat napůl.

Je to číslo, které se má hýbat. Zatím říká, že vymyšlené věty a
encyklopedická próza jsou dva různé světy.

## Co tu vědomě není

Vlastní dělič vět ani vlastní čistič HTML. Obojí by se rozešlo s tím,
co dělá služba a co vrací API — a rozdíl by se poznal až na výsledcích.
