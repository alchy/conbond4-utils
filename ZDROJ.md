# Zdroje a licence

Co do projektu přichází odjinud, odkud a pod jakou licencí. Vede se to
tady proto, že **cizí text se nesmí dostat do repozitáře** — a kontrola
toho má být automatická, ne slib.

## Wikipedie

| co | odkud | licence | v gitu? |
|---|---|---|---|
| texty článků | `cs.wikipedia.org` přes `action=query&prop=extracts` | **CC BY-SA 4.0** | **ne** |
| seznam témat | `temata.txt` | vlastní | ano |

Stažené texty jdou do `data/`, které je v `.gitignore`. Do gitu patří
**jen seznam témat**: kdo si projekt naklonuje, dojde k témuž textu sám
a s aktuální revizí.

`Article.provenance` nese `cs.wikipedia.org/<název>@<revize>`. Číslo
revize tam není pro ozdobu — bez něj by se dva různé texty pod týmž
jménem nedaly rozeznat, což je táž past jako keš rozborů bez identity
modelu (viz `conbond4-deps`).

## Korpus conBondu2

| co | odkud | licence | v gitu? |
|---|---|---|---|
| texty článků | `github.com/alchy/conBond2`, `data/raw/` | **CC BY-SA** (Wikipedie) + 5 vlastních | **ne** — klonuje se do `data/` |
| zlaté sady | `data/gold/*.json` tamtéž | vlastní dílo projektu | ne (čtou se z klonu) |
| **věty v záznamech měření** | `mereni/*.json`, `baseline.html` | **CC BY-SA** | **ANO — a je to otevřená otázka** |

Poslední řádek je vědomá výjimka, ne přehlédnutí. Záznam měření nese
**celé věty** korpusu, protože bez nich nejde zpětně zjistit, na co se
systém ptal a proč — a měření, které se nedá po pull ověřit, je jen
tvrzení. Je to ale cizí text v repozitáři, což pravidlo 7 zadání zakazuje.

Tři cesty ven a **rozhodnutí patří Revieweru**, ne měřicí vrstvě:

1. nechat a doplnit atribuci — CC BY-SA to dovoluje (uvést zdroj, dílo
   šířit pod touž licencí);
2. ukládat místo věty její otisk — reprodukovatelnost zůstane, ale mapa
   přestane být čitelná a s ní i celý smysl kroku 5;
3. držet záznamy mimo git — pak po pull nejde porovnat dva běhy.

Do rozhodnutí platí varianta 1 bez formální atribuce, což je stav, který
se má **buď dodělat, nebo zvrátit**; proto to stojí tady a ne v poznámce.

## Parser

`cb-udpipe` s modelem `cs_all-ud-2.17-251125` (**CC BY-NC-SA 4.0**,
nekomerční). Model ani embeddingy nejsou v žádném z repozitářů; pořizuje
je `conbond4-deps`.

## Jádro

`conbond4` se **neinstaluje**, jen se hledá jako sourozenecký adresář.
Kopie jádra v tomhle repozitáři by byla druhá pravda o tom, jak se věty
čtou — a rozešla by se.
