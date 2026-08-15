"""Článek z Wikipedie na HOLÝ TEXT.

Bere se přes `action=query&prop=extracts&explaintext=1`, tedy oficiální
API, které vrací text bez značek. Škrábat HTML by znamenalo psát si
vlastní čistič a ten je vždycky o jednu šablonu pozadu.

**Text se nestahuje do repozitáře.** Je pod CC BY-SA a je to cizí dílo;
patří do `data/`, které je v `.gitignore` (viz `ZDROJ.md`). Do gitu jde
jen SEZNAM TÉMAT, ne jejich obsah — kdo si projekt naklonuje, dojde
k témuž textu sám a s aktuální revizí.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://cs.wikipedia.org/w/api.php"
UA = "conbond4-utils/0.1 (vyzkumny nastroj; kontakt v README)"
TIMEOUT_S = 20.0


class WikiError(Exception):
    """Stažení selhalo, nebo článek neexistuje."""


@dataclass(frozen=True, slots=True)
class Article:
    """Stažený článek. `revision` je součást provenience — bez ní by se
    dva různé texty pod týmž jménem nedaly rozeznat, což je táž past
    jako keš rozborů bez identity modelu."""

    title: str
    revision: int
    text: str

    @property
    def provenance(self) -> str:
        return f"cs.wikipedia.org/{self.title}@{self.revision}"


def _get(params: dict[str, str]) -> dict:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch(title: str) -> Article:
    """Stáhne článek jako holý text i s číslem revize."""
    payload = _get(
        {
            "action": "query",
            "prop": "extracts|revisions",
            "rvprop": "ids",
            "explaintext": "1",
            "redirects": "1",
            "titles": title,
        }
    )
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        raise WikiError(f"článek {title!r} nevrátil žádnou stránku")
    page = next(iter(pages.values()))
    if "missing" in page:
        raise WikiError(f"článek {title!r} neexistuje")
    text = page.get("extract") or ""
    if not text.strip():
        raise WikiError(f"článek {title!r} nemá textový výtah")
    revisions = page.get("revisions") or [{}]
    return Article(
        title=page.get("title", title),
        revision=int(revisions[0].get("revid", 0)),
        text=text,
    )


def paragraphs(article: Article) -> tuple[str, ...]:
    """Odstavce bez nadpisů sekcí.

    Nadpis je v holém textu řádek `== Něco ==`. Není to věta a poslat ho
    do rozboru by znamenalo měřit, jak si parser poradí s nadpisem —
    což nikoho nezajímá.
    """
    out: list[str] = []
    for block in article.text.split("\n"):
        line = block.strip()
        if not line or line.startswith("=="):
            continue
        out.append(line)
    return tuple(out)
