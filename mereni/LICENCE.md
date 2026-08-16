# Licence a atribuce textů v záznamech

Záznamy v téhle složce (`korpus-*.json`) a mapa `baseline.html`
obsahují **celé věty** z korpusu conBondu2. Většina těch textů
pochází z **české Wikipedie** a je pod licencí
**CC BY-SA 4.0** — <https://creativecommons.org/licenses/by-sa/4.0/>.

Co z toho plyne pro toho, kdo si repozitář forkne: tenhle adresář
je **odvozené dílo** a šíří se dál pod touž licencí, s uvedením
zdroje. Zbytek repozitáře (kód, dokumentace, zlaté sady) je vlastní
dílo projektu a licence Wikipedie se ho netýká.

Korpus: `github.com/alchy/conBond2@418d7f7` (soubory `data/raw/*.txt`).

## Z české Wikipedie, CC BY-SA 4.0

Odkaz je **odvozený z názvu souboru** — conBond2 si u článků URL
nedrží. U několika článků je název ručně opravený (`R.U.R.`), jinde
může odkaz mířit na rozcestník; je to atribuce, ne katalog.

| dokument | článek | odkaz | v záznamech |
|---|---|---|---|
| `alois_jirásek` | Alois Jirásek | <https://cs.wikipedia.org/wiki/Alois_Jirásek> | 6 |
| `antarktida` | Antarktida | <https://cs.wikipedia.org/wiki/Antarktida> | 6 |
| `bohumil_hrabal` | Bohumil Hrabal | <https://cs.wikipedia.org/wiki/Bohumil_Hrabal> | 6 |
| `božena_němcová` | Božena Němcová | <https://cs.wikipedia.org/wiki/Božena_Němcová> | 6 |
| `egon_hostovský` | Egon Hostovský | <https://cs.wikipedia.org/wiki/Egon_Hostovský> | 6 |
| `fotosyntéza` | Fotosyntéza | <https://cs.wikipedia.org/wiki/Fotosyntéza> | 6 |
| `františek_halas` | František Halas | <https://cs.wikipedia.org/wiki/František_Halas> | 6 |
| `jaroslav_hašek` | Jaroslav Hašek | <https://cs.wikipedia.org/wiki/Jaroslav_Hašek> | 6 |
| `josef_čapek` | Josef Čapek | <https://cs.wikipedia.org/wiki/Josef_Čapek> | 6 |
| `josef_škvorecký` | Josef Škvorecký | <https://cs.wikipedia.org/wiki/Josef_Škvorecký> | 6 |
| `karel_čapek` | Karel Čapek | <https://cs.wikipedia.org/wiki/Karel_Čapek> | 6 |
| `kočka_domácí` | Kočka domácí | <https://cs.wikipedia.org/wiki/Kočka_domácí> | 6 |
| `kůň_domácí` | Kůň domácí | <https://cs.wikipedia.org/wiki/Kůň_domácí> | 6 |
| `pes_domácí` | Pes domácí | <https://cs.wikipedia.org/wiki/Pes_domácí> | 6 |
| `rur` | R.U.R. | <https://cs.wikipedia.org/wiki/R.U.R.> | 6 |
| `sopka` | Sopka | <https://cs.wikipedia.org/wiki/Sopka> | 6 |
| `včela_medonosná` | Včela medonosná | <https://cs.wikipedia.org/wiki/Včela_medonosná> | 6 |
| `šachy` | Šachy | <https://cs.wikipedia.org/wiki/Šachy> | 6 |

## Psané ručně v conBondu2 — bez vnějšího zdroje

Podle `data/raw/ZDROJ.md` conBondu2. **Odkaz na Wikipedii se jim
nepřilepuje** — to by byla atribuce naopak, tedy tvrzení o původu,
který neexistuje.

| dokument | v záznamech |
|---|---|
| `fyzika_gravitace` | 6 |
| `poznámky_domácnost` | 6 |
| `příroda_česká` | 6 |
| `rodina_novákovi` | 6 |

---

Soubor **se generuje** (`cb_utils/atribuce.py`) při každém zápisu
záznamu. Ručně psaná atribuce by zestárla hned s dalším dokumentem —
a atribuce, která nezahrnuje všechno, co v repu leží, je horší než
žádná, protože vypadá jako splněná povinnost.
