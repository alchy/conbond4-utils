"""Který záznam měření vzít, když se žádný nezadá.

Skripty v `nalezy/` si cestu psaly natvrdo a ta zestárne s příštím
během: `otazka_neni_nula.py` sliboval v docstringu spuštění bez
argumentu a ukazoval na soubor, který v repozitáři nikdy nebyl (W‑79).
**Doklad, který nejde spustit podle návodu, je jen tvrzení** — a tady se
tvrzením nevěří ani jádru, natož vlastní vrstvě.

Bere se **nejnovější** záznam, ne jmenovaný: měření je řada běhů a
skript, který ukazuje na jeden, přestane po dalším běhu odpovídat na
otázku „jak to vypadá teď".
"""

from __future__ import annotations

from pathlib import Path

MERENI = Path(__file__).resolve().parent.parent / "mereni"


def posledni(vzor: str = "korpus-*.json", *, kde: Path | None = None) -> Path | None:
    """Nejnovější záznam podle jména, nebo `None`.

    Řadí se **jménem**, ne časem souboru: jméno nese datum a revizi,
    kdežto čas se změní každým kopírováním repozitáře. Je to táž zásada
    jako všude jinde tady — identita nesmí viset na něčem, co se dá
    přepsat mimochodem.
    """
    slozka = kde or MERENI
    if not slozka.exists():
        return None
    zaznamy = sorted(slozka.glob(vzor))
    return zaznamy[-1] if zaznamy else None


def vyber(argv: list[str], vzor: str = "korpus-*.json") -> Path:
    """Cesta z argumentů, jinak poslední záznam. Hlásí, když není nic."""
    volne = [a for a in argv if not a.startswith("--")]
    if volne:
        cesta = Path(volne[0])
        if not cesta.exists():
            raise SystemExit(f"záznam {cesta} není")
        return cesta
    cesta = posledni(vzor)
    if cesta is None:
        raise SystemExit(
            f"v {MERENI} není žádný záznam ({vzor}) — pusť napřed"
            f" `python cb-korpus.py --json mereni/korpus-<datum>.json`"
        )
    return cesta
