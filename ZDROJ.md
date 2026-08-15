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

## Parser

`cb-udpipe` s modelem `cs_all-ud-2.17-251125` (**CC BY-NC-SA 4.0**,
nekomerční). Model ani embeddingy nejsou v žádném z repozitářů; pořizuje
je `conbond4-deps`.

## Jádro

`conbond4` se **neinstaluje**, jen se hledá jako sourozenecký adresář.
Kopie jádra v tomhle repozitáři by byla druhá pravda o tom, jak se věty
čtou — a rozešla by se.
