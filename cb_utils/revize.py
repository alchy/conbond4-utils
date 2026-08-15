"""Čím je běh identifikován — aby šlo po změně jádra rozeznat
„systém se zlepšil" od „změnil se vstup".

Do prvního záznamu (`mereni/2026-08-15.json`) šla jen provenience
orákula. Vypadalo to dost, a nebylo: druhý běh nad **týmiž revizemi
článků a týmž modelem** vrátil u tří vět jinou otázku, a z toho záznamu
nešlo poznat, jestli se změnilo jádro, nebo jestli je měření nestabilní.
Změnilo se jádro (dva commity mezi běhy) — ale to se muselo dohledávat
v cizím repozitáři, ne přečíst ze záznamu.

Identita běhu má proto tři složky a **žádná z nich nestačí sama**:

    revize článku    co přišlo na vstup     (`Article.provenance`)
    model orákula    kdo to rozebral        (`UDPipeOracle.provenance`)
    revize jádra     kdo to četl            (tenhle modul)

`git describe` se nepoužívá — popisek visí na značkách, které v jádře
nejsou. Bere se `rev-parse HEAD` plus příznak, jestli byl strom čistý:
běh nad rozdělanou prací je legitimní, jen se na něj nesmí odkazovat
jako na revizi.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

TIMEOUT_S = 10.0


def _git(repo: Path, *args: str) -> str:
    try:
        done = subprocess.run(
            ("git", "-C", str(repo), *args),
            capture_output=True,
            # UTF-8 NATVRDO. `text=True` bere kódování z locale a na
            # Windows je to kódová stránka konzole — commit „věta bez
            # podmětu" se do záznamu zapsal jako „vÄ›ta bez podmÄ›tu".
            # Identita běhu, kterou nejde přečíst, není identita.
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as error:  # pragma: no cover
        return f"<git selhal: {error}>"
    if done.returncode != 0:
        return f"<git {' '.join(args)}: {done.stderr.strip()[:80]}>"
    return done.stdout.strip()


def revision(repo: Path) -> str:
    """`<sha> <datum> <předmět>`, s `+dirty:<otisk>`, když strom není čistý.

    **Holý příznak `+dirty` nestačí a je to změřené.** Dva záznamy
    z jednoho dopoledne nesly obojí `d6782cb +dirty` a přitom vrátily
    `NEPŘEČTENO 30` a `NEPŘEČTENO 49` — mezi běhy se v pracovním stromě
    jádra objevila a zase zmizela oprava shody. Pod jednou identitou tak
    ležely dva různé stavy kódu, což je táž past jako keš rozborů bez
    identity modelu nebo zlatá sada odkazující na věty pořadím.

    Otisk je `sha1` z `git diff HEAD` (prvních 8 znaků). Neřekne, CO se
    liší, ale spolehlivě rozezná dva různé rozdělané stromy — a to je
    přesně to, co se od identity běhu chce.

    Nikdy nevyhazuje výjimku: záznam měření se nemá neuložit proto, že
    jádro není v gitu. Neznámá revize je vlastní hodnota, ne chyba —
    jen se pod ní nesmí tvrdit reprodukovatelnost.
    """
    if not (repo / ".git").exists():
        return f"{repo.name}: mimo git — revize neznámá"
    head = _git(repo, "log", "-1", "--format=%h %ad %s", "--date=format:%Y-%m-%d %H:%M")
    status = _git(repo, "status", "--porcelain")
    if not status or status.startswith("<git"):
        return head
    diff = _git(repo, "diff", "HEAD")
    otisk = hashlib.sha1(diff.encode("utf-8", "replace")).hexdigest()[:8]
    return f"{head} +dirty:{otisk}"
