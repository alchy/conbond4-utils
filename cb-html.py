#!/usr/bin/env python
"""Záznam měření → HTML **diagnostická mapa**.

    python cb-html.py                        # poslední záznam z mereni/
    python cb-html.py mereni/korpus-…json --do mereni/baseline.html

Krok 5 zadání. **Není to log převedený do HTML a není to demo.** Log
odpoví na „co se stalo", mapa musí odpovědět na **„proč zrovna tohle"** —
a to u každé jedné věty, aniž by se musel reprodukovat celý běh.

U každé věty je proto dohledatelné:

    původní řádek ze zdroje  a vedle něj věta, jak ji vydělila segmentace
    tvar vstupu              věta / nadpis / položka / popiska / bez slovesa
    rozbor                   tvar/UPOS/deprel→hlava
    stopa kaskády            které patro co zahodilo, doslova
    čtení                    co z toho vzniklo za predikaci
    otevřené věci            seznamem a s druhem, ne počtem
    zařazení vady            rozbor rozuměl × špatné čtení × nepřečteno

Agregace nahoře je **šest stavů zvlášť a sedm druhů otázek zvlášť**.
Jedno číslo místo nich by zahodilo přesně to, co se dvě kola opravovalo:
`PTÁ SE` není chyba, `DVOJZNAČNÉ` není mlčení a nadpis, který se nepřečetl,
není mezera schopnosti.

Stránka je **jeden soubor bez sítě** — data jsou v ní. Report, který si
při otevření něco stahuje, přestane fungovat v tu chvíli, kdy je potřeba
nejvíc: až se bude dohledávat, jak to vypadalo před půl rokem.
"""

from __future__ import annotations

import argparse
import html
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cb_utils.zaznamy import vyber  # noqa: E402

#: Pořadí stavů. Není abecední ani podle četnosti — jde od „systém to
#: umí" k „systém selhal", protože v tomhle pořadí se čte hranice
#: schopnosti.
STAVY = (
    "ZAPSÁNO · úplně",
    "ZAPSÁNO · s otázkami",
    "PTÁ SE",
    "DVOJZNAČNÉ",
    "NEPŘEČTENO",
    "ODMÍTNUTO",
    "CHYBA",
)

#: Barva nese VÝZNAM, ne náladu: co systém zvládl, co se ptá, co nezvládl.
#: Šest stavů má tři barvy — sytost uvnitř skupiny odlišuje stav, ale
#: skupina zůstane čitelná i pro toho, kdo barvy nerozlišuje, protože
#: stav je vždycky napsaný slovem.
BARVY = {
    "ZAPSÁNO · úplně": "var(--ok)",
    # Částečný zápis má vlastní barvu i vlastní číslo: je to pořád
    # zápis, ale s otevřenou otázkou — a holé „ZAPSÁNO 46" by o dvanácti
    # z nich tvrdilo víc, než platí.
    "ZAPSÁNO · s otázkami": "var(--ok2)",
    "ZAPSÁNO": "var(--ok)",
    "PTÁ SE": "var(--ask)",
    "DVOJZNAČNÉ": "var(--ask2)",
    "NEPŘEČTENO": "var(--no)",
    "ODMÍTNUTO": "var(--no2)",
    "CHYBA": "var(--err)",
}


def vety_zaznamu(zaznam: dict) -> list[dict]:
    out: list[dict] = []
    for dokument in zaznam.get("documents", []):
        for veta in dokument["sentences"]:
            out.append({**veta, "dokument": dokument["name"]})
    return out


def zarad(veta: dict) -> str:
    """Zařazení vady — z pole `parse` a `reading`, tedy ze záznamu.

    Drží se stejné hranice jako `nalezy/cteni_vs_inference.py`: tady jde
    o hrubý rozřaďovač do mapy, jemné posouzení dělá ten skript a umí
    říct i „kandidát". Do HTML se proto nepíše „špatné čtení" jako fakt.
    """
    if veta["verdict"] == "ZAPSÁNO":
        return "zapsáno"
    if veta["verdict"] in ("NEPŘEČTENO", "CHYBA"):
        return "nepřečteno"
    if veta["verdict"] == "DVOJZNAČNÉ":
        return "víc čtení"
    return "jádro nedotáhlo"


def sloupce(pocty: Counter[str], poradi: tuple[str, ...] | None = None) -> str:
    """Vodorovný pruh: jeden díl na hodnotu, šířka podle počtu."""
    klice = list(poradi) if poradi else [k for k, _ in pocty.most_common()]
    klice = [k for k in klice if pocty.get(k)]
    celkem = sum(pocty.get(k, 0) for k in klice) or 1
    dily = []
    for klic in klice:
        kolik = pocty.get(klic, 0)
        podil = 100.0 * kolik / celkem
        barva = BARVY.get(klic, "var(--druh)")
        dily.append(
            f'<div class="dil" style="width:{podil:.3f}%;background:{barva}"'
            f' title="{html.escape(klic)}: {kolik} ({podil:.1f} %)"></div>'
        )
    legenda = " ".join(
        f'<span class="klic"><i style="background:{BARVY.get(k, "var(--druh)")}">'
        f'</i>{html.escape(k)} <b>{pocty.get(k, 0)}</b></span>'
        for k in klice
    )
    return f'<div class="pruh">{"".join(dily)}</div><div class="legenda">{legenda}</div>'


def tabulka_krizem(vety: list[dict], klic: str, nadpis: str) -> str:
    """Osa × stav. **Kříží se, nesčítají** — nadpis, který se nepřečetl,
    není totéž co věta, která se nepřečetla."""
    krizem: Counter[tuple[str, str]] = Counter()
    for veta in vety:
        krizem[(veta.get(klic) or "—", veta["stav"])] += 1
    radky = sorted({r for r, _ in krizem})
    stavy = [s for s in STAVY if any(x == s for _, x in krizem)]
    hlava = "".join(f"<th>{html.escape(s)}</th>" for s in stavy)
    telo = []
    for radek in radky:
        bunky = "".join(
            f'<td class="{"nula" if not krizem[(radek, s)] else ""}">'
            f"{krizem[(radek, s)] or ''}</td>"
            for s in stavy
        )
        celkem = sum(krizem[(radek, s)] for s in stavy)
        telo.append(
            f"<tr><th>{html.escape(radek)}</th>{bunky}<td><b>{celkem}</b></td></tr>"
        )
    return (
        f"<h2>{html.escape(nadpis)}</h2><table class='krizem'>"
        f"<tr><th></th>{hlava}<th>celkem</th></tr>{''.join(telo)}</table>"
    )


def tabulka_vrstev(vety: list[dict]) -> str:
    """`sám blokuje` = kolik vět uvázlo JEN na téhle jediné vrstvě.
    Je to nejcennější sloupec: věta s jednou otevřenou věcí ukazuje
    přesnou hranici schopnosti, věta se sedmi říká jen, že je složitá."""
    hit: Counter[str] = Counter()
    sole: Counter[str] = Counter()
    for veta in vety:
        for vrstva in veta.get("layers") or []:
            hit[vrstva] += 1
        if veta.get("sole"):
            sole[veta["sole"]] += 1
    celkem = len(vety) or 1
    radky = []
    for vrstva, kolik in hit.most_common():
        sam = sole.get(vrstva, 0)
        radky.append(
            f"<tr><th>{html.escape(vrstva)}</th>"
            f"<td>{kolik} <span class='sede'>({100.0 * kolik / celkem:.1f} %)</span></td>"
            f"<td>{sam} <span class='sede'>({100.0 * sam / celkem:.1f} %)</span></td></tr>"
        )
    return (
        "<h2>Vrstvy — kde věta uvázla</h2><table class='krizem'>"
        "<tr><th></th><th>vyskytuje se</th><th>sám blokuje</th></tr>"
        f"{''.join(radky)}</table>"
    )


def postav(zaznam: dict, zdroj: Path) -> str:
    vety = vety_zaznamu(zaznam)
    for veta in vety:
        veta["zarazeni"] = zarad(veta)
        # Stav s fasetou. Starší záznamy pole `stav` nemají a bere se
        # verdikt: dopočítávat fasetu zpětně z `open_questions` by
        # znamenalo tvrdit o starém běhu něco, co v něm nestálo.
        if not veta.get("stav"):
            veta["stav"] = veta["verdict"]
    stavy: Counter[str] = Counter(v["stav"] for v in vety)
    druhy: Counter[str] = Counter(
        q.split(":", 1)[0] for v in vety for q in (v.get("questions") or [])
    )

    # Data pro stránku: co je v tabulkách, je i v seznamu — ať jde
    # z čísla nahoře doklikat na věty, ze kterých vzniklo.
    payload = [
        {
            "t": v["text"],
            "r": v.get("radek") or "",
            "d": v["dokument"],
            "s": v["stav"],
            "tv": v.get("tvar") or "",
            "z": v["zarazeni"],
            "c": v.get("reading") or "",
            "q": v.get("questions") or [],
            "l": v.get("layers") or [],
            "so": v.get("sole") or "",
            "k": v.get("kind") or "",
            "p": v.get("parse") or [],
            "st": v.get("trace") or [],
            "du": v.get("reason") or "",
            # Co se u zapsané věty doopravdy zapsalo (W‑67): id tvrzení,
            # program včetně reifikací a celý výstup jádra.
            "wid": v.get("written_id") or "",
            "pg": v.get("program") or [],
            "zp": v.get("zapis") or [],
        }
        for v in vety
    ]

    hlavicka = "".join(
        f"<tr><th>{html.escape(jmeno)}</th><td><code>{html.escape(str(hodnota))}"
        f"</code></td></tr>"
        for jmeno, hodnota in (
            ("korpus", zaznam.get("korpus", "?")),
            ("jádro", zaznam.get("core", "?")),
            ("jádro na konci", zaznam.get("core_na_konci", "?")),
            ("orákulum", zaznam.get("oracle", "?")),
            ("měřicí vrstva", zaznam.get("utils", "?")),
            ("záznam", zdroj.name),
            ("strop vět na dokument", zaznam.get("strop_vet_na_dokument", "?")),
            ("neměřeno řádků nad stropem", zaznam.get("unmeasured", "?")),
        )
    )
    # VAROVÁNÍ PŘÍMO V MAPĚ, ne v poznámce pod ní. Mapa se ukazuje
    # a cituje; kdo si ji otevře za měsíc, musí z ní poznat, jestli se
    # čísla dají zopakovat — jinak se z „běhu nad rozdělaným stromem"
    # stane citovaný fakt.
    vady = []
    if "+dirty:" in str(zaznam.get("core", "")):
        vady.append("jádro bylo <b>rozdělané</b> — tahle čísla nepatří "
                    "žádnému commitu")
    if zaznam.get("core_na_konci") and zaznam["core_na_konci"] != zaznam.get("core"):
        vady.append("jádro se <b>během běhu změnilo</b> — záznam není nad "
                    "jedním stavem kódu")
    if "+dirty:" in str(zaznam.get("utils", "")):
        vady.append("měřicí vrstva byla <b>rozdělaná</b> — čísla vyrobil kód, "
                    "který v žádném commitu není")
    varovani = (
        '<div class="varovani"><b>Tenhle běh nejde zopakovat.</b><ul>'
        + "".join(f"<li>{v}</li>" for v in vady)
        + "</ul></div>"
    ) if vady else ""

    determinismus = zaznam.get("determinismus") or {}
    if determinismus:
        hlavicka += (
            "<tr><th>determinismus</th><td>"
            + ("dva běhy nad touž revizí <b>shodné</b>"
               if determinismus.get("shoda")
               else "<b>ROZDÍL mezi běhy</b>")
            + "</td></tr>"
        )

    etalon = zaznam.get("etalon", {}).get("polozky", [])
    etalon_html = ""
    if etalon:
        podle: Counter[tuple[str, str]] = Counter(
            (p.get("mode") or "bez režimu", p.get("vysledek") or "?") for p in etalon
        )
        radky = "".join(
            f"<tr><th>{html.escape(rezim)}</th><td>{html.escape(vysledek)}</td>"
            f"<td>{kolik}</td></tr>"
            for (rezim, vysledek), kolik in sorted(podle.items())
        )
        etalon_html = (
            f"<h2>Zlatá sada — {len(etalon)} položek</h2>"
            "<p class='sede'>Celá, včetně <code>unsure</code> a <code>clarify</code>. "
            "Dokud se do báze nic nezapisuje, vychází na všechno <code>U</code> — "
            "je to <b>měřicí nula, ne skóre</b>: „splněno 13 z 13 unsure“ tu "
            "neznamená, že systém pozná svou mez, ale že nezná nic.</p>"
            f"<table class='krizem'><tr><th>režim</th><th>výsledek</th>"
            f"<th>kolik</th></tr>{radky}</table>"
        )

    # CO CHYBÍ ČÁSTEČNÝM ZÁPISŮM. Číslo „44 částečných" neřekne, jestli
    # je to jedna rodina, nebo čtyřicet čtyři různých — a řídit se dá
    # jedině podle toho druhého.
    castecne = [
        v for v in vety
        if v["stav"] == "ZAPSÁNO · s otázkami" and v.get("questions")
    ]
    castecne_html = ""
    if castecne:
        podle_druhu: Counter[str] = Counter(
            q.split(":", 1)[0] for v in castecne for q in v["questions"]
        )
        na_vetu: Counter[str] = Counter(
            " + ".join(sorted({q.split(":", 1)[0] for q in v["questions"]}))
            for v in castecne
        )
        radky = "".join(
            f"<tr><th>{html.escape(k)}</th><td>{n}</td></tr>"
            for k, n in na_vetu.most_common()
        )
        castecne_html = (
            f"<h2>Co chybí částečným zápisům — {len(castecne)} vět</h2>"
            "<p class='sede'>Zápis se stal, otázka zůstala. Bez tohohle "
            "rozpadu se z čísla nepozná, jestli je to jedna rodina, nebo "
            "tolik různých, kolik je vět.</p>"
            + sloupce(podle_druhu)
            + "<table class='krizem'><tr><th>na větu</th><th>kolik</th></tr>"
            + radky
            + "</table>"
        )

    return _SABLONA.format(
        varovani=varovani,
        castecne=castecne_html,
        hlavicka=hlavicka,
        pocet=len(vety),
        stavy=sloupce(stavy, STAVY),
        druhy=sloupce(druhy),
        tvar=tabulka_krizem(vety, "tvar", "Tvar vstupu × stav"),
        zarazeni=tabulka_krizem(vety, "zarazeni", "Zařazení vady × stav"),
        vrstvy=tabulka_vrstev(vety),
        etalon=etalon_html,
        data=json.dumps(payload, ensure_ascii=False),
    )


_SABLONA = """<!doctype html>
<!-- lang a translate="no" jsou tu obojí schválně a je to poučení
     z conBondu2: bez `lang` si prohlížeč jazyk domyslí a stránku
     přeloží — a překlad se nedrží textu, sahá i na DATA. Z „nsubj“ se
     stane něco jiného a na obrazovce pak stojí rozbor, který v korpusu
     není. -->
<html lang="cs" translate="no" class="notranslate">
<meta charset="utf-8">
<meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>conBond4 — diagnostická mapa</title>
<style>
  :root {{
    --plane:#f8f8f6; --surface:#fff; --ink:#111; --ink2:#555; --sede:#8a8a85;
    --ring:rgba(0,0,0,.12); --grid:#e6e5df;
    --ok:#1b9e63; --ok2:#6a9e1b; --ask:#3b7dd8; --ask2:#7c5cd6; --no:#c8641c; --no2:#a03b3b;
    --err:#8b1a1a; --druh:#6b7a8f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --plane:#0e0e0e; --surface:#171716; --ink:#f2f2f0; --ink2:#c2c2bc;
      --sede:#8a8a85; --ring:rgba(255,255,255,.14); --grid:#2b2b28;
      --ok:#35b97c; --ok2:#93c34a; --ask:#5b95e6; --ask2:#9a7cf0; --no:#e0803a; --no2:#c25c5c;
      --err:#e05555; --druh:#8ea0b5;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:28px 22px 80px; background:var(--plane); color:var(--ink);
         font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
  .wrap {{ max-width:1180px; margin:0 auto; }}
  h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:-.01em; }}
  h2 {{ font-size:15px; margin:26px 0 8px; letter-spacing:.02em; }}
  p.lede {{ color:var(--ink2); margin:0 0 18px; max-width:76ch; }}
  code {{ font:12px/1.5 ui-monospace,"Cascadia Code",Consolas,monospace; }}
  .sede {{ color:var(--sede); }}
  table.krizem {{ border-collapse:collapse; margin:6px 0 2px; }}
  table.krizem th, table.krizem td {{ border:1px solid var(--grid); padding:4px 9px;
        text-align:right; font-variant-numeric:tabular-nums; }}
  table.krizem th:first-child, table.krizem tr:first-child th {{ text-align:left;
        color:var(--ink2); font-weight:600; }}
  td.nula {{ color:var(--grid); }}
  .pruh {{ display:flex; height:15px; border-radius:4px; overflow:hidden;
           box-shadow:0 0 0 1px var(--ring); }}
  .dil {{ height:100%; }}
  .legenda {{ display:flex; flex-wrap:wrap; gap:14px; margin:8px 0 2px;
              color:var(--ink2); font-size:13px; }}
  .klic i {{ display:inline-block; width:10px; height:10px; border-radius:2px;
             margin-right:5px; }}
  .filtry {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center;
             margin:18px 0 10px; padding:10px 12px; background:var(--surface);
             border:1px solid var(--ring); border-radius:8px; }}
  select, input {{ font:inherit; padding:4px 7px; border:1px solid var(--ring);
                   border-radius:6px; background:var(--surface); color:var(--ink); }}
  input[type=search] {{ min-width:230px; }}
  .veta {{ background:var(--surface); border:1px solid var(--ring);
           border-radius:8px; margin:7px 0; padding:9px 12px; }}
  .veta > summary {{ cursor:pointer; list-style:none; display:flex; gap:10px;
                     align-items:baseline; }}
  .veta > summary::-webkit-details-marker {{ display:none; }}
  .stav {{ font-size:11px; letter-spacing:.05em; padding:2px 7px; border-radius:99px;
           color:#fff; white-space:nowrap; }}
  .pocet {{ color:var(--sede); font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .text {{ flex:1; }}
  .detail {{ margin-top:10px; border-top:1px solid var(--grid); padding-top:9px; }}
  .detail h3 {{ font-size:11px; letter-spacing:.07em; text-transform:uppercase;
                color:var(--sede); margin:11px 0 3px; font-weight:600; }}
  .detail pre {{ margin:0; white-space:pre-wrap; word-break:break-word;
                 font:12px/1.55 ui-monospace,Consolas,monospace; color:var(--ink2); }}
  .detail ul {{ margin:0; padding-left:18px; }}
  .detail li {{ margin:2px 0; }}
  .znacka {{ display:inline-block; font-size:11px; padding:1px 6px; border-radius:4px;
             background:var(--grid); color:var(--ink2); margin-right:5px; }}
  .prazdno {{ color:var(--sede); padding:18px 2px; }}
  .varovani {{ margin:16px 0 4px; padding:11px 14px; border-radius:8px;
               border:1px solid var(--err); color:var(--ink);
               background:color-mix(in srgb, var(--err) 12%, transparent); }}
  .varovani ul {{ margin:6px 0 0; padding-left:20px; }}
</style>

<div class="wrap">
<h1>conBond4 — diagnostická mapa</h1>
<p class="lede">Co systém z textu <b>skutečně přečetl</b>, čemu nerozuměl a
<b>proč</b> — u každé věty zvlášť. Šest stavů se nikdy neslévá do jednoho
skóre: <code>PTÁ SE</code> není chyba, <code>DVOJZNAČNÉ</code> není mlčení
a nadpis, který se nepřečetl, není mezera schopnosti.</p>

{varovani}
<h2>Identita běhu</h2>
<table class="krizem">{hlavicka}</table>

<h2>Stavy — {pocet} vět</h2>
{stavy}

<h2>Druhy otevřených věcí</h2>
<p class="sede">Na co se systém ptá, ne kolikrát. Součet je vyšší než počet
vět — jedna věta má otevřených věcí víc.</p>
{druhy}

{castecne}
{tvar}
{zarazeni}
{vrstvy}
{etalon}

<h2>Věty</h2>
<div class="filtry">
  <label>stav <select id="f-stav"></select></label>
  <label>tvar <select id="f-tvar"></select></label>
  <label>vrstva <select id="f-vrstva"></select></label>
  <label>druh otázky <select id="f-druh"></select></label>
  <label>dokument <select id="f-dok"></select></label>
  <input type="search" id="f-text" placeholder="hledat ve větě…">
  <span class="sede" id="pocitadlo"></span>
</div>
<div id="seznam"></div>
</div>

<script type="application/json" id="data">{data}</script>
<script>
const VETY = JSON.parse(document.getElementById("data").textContent);
const BARVA = {{"ZAPSÁNO":"var(--ok)","ZAPSÁNO · úplně":"var(--ok)","ZAPSÁNO · s otázkami":"var(--ok2)","PTÁ SE":"var(--ask)","DVOJZNAČNÉ":"var(--ask2)",
  "NEPŘEČTENO":"var(--no)","ODMÍTNUTO":"var(--no2)","CHYBA":"var(--err)"}};
const esc = s => String(s).replace(/[&<>]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));

function naplnit(id, hodnoty, popis) {{
  const el = document.getElementById(id);
  el.innerHTML = '<option value="">' + popis + '</option>' +
    [...hodnoty].sort().map(h => '<option>' + esc(h) + '</option>').join('');
  el.onchange = vykreslit;
}}
naplnit("f-stav", new Set(VETY.map(v => v.s)), "vše");
naplnit("f-tvar", new Set(VETY.map(v => v.tv)), "vše");
naplnit("f-vrstva", new Set(VETY.flatMap(v => v.l)), "vše");
naplnit("f-druh", new Set(VETY.flatMap(v => v.q.map(q => q.split(":")[0]))), "vše");
naplnit("f-dok", new Set(VETY.map(v => v.d)), "vše");
document.getElementById("f-text").oninput = vykreslit;

function detail(v) {{
  const kus = (nadpis, telo) => telo ? '<h3>' + nadpis + '</h3>' + telo : '';
  const pre = t => '<pre>' + esc(t) + '</pre>';
  const seznam = a => '<ul>' + a.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>';
  return '<div class="detail">'
    + (v.r && v.r !== v.t ? kus("původní řádek ze zdroje", pre(v.r)) : '')
    + kus("čtení", v.c ? pre(v.c) : '')
    + (v.wid ? kus("zapsáno jako " + esc(v.wid), pre(v.zp.join("\\n"))) : '')
    + (v.pg.length ? kus("co přibylo v bázi — " + v.pg.length, seznam(v.pg)) : '')
    + (v.q.length ? kus("otevřené věci — " + v.q.length, seznam(v.q)) : '')
    + (!v.q.length && v.du ? kus("důvod", pre(v.du)) : '')
    + (v.st.length ? kus("stopa kaskády", pre(v.st.join("\\n"))) : '')
    + (v.p.length ? kus("rozbor", pre(v.p.join("  "))) : '')
    + '</div>';
}}

function vykreslit() {{
  const stav = document.getElementById("f-stav").value;
  const tvar = document.getElementById("f-tvar").value;
  const vrstva = document.getElementById("f-vrstva").value;
  const druh = document.getElementById("f-druh").value;
  const dok = document.getElementById("f-dok").value;
  const hledat = document.getElementById("f-text").value.toLowerCase();
  const vybrane = VETY.filter(v =>
    (!stav || v.s === stav) && (!tvar || v.tv === tvar) &&
    (!vrstva || v.l.includes(vrstva)) &&
    (!druh || v.q.some(q => q.split(":")[0] === druh)) &&
    (!dok || v.d === dok) &&
    (!hledat || v.t.toLowerCase().includes(hledat)));
  // NEJVÍC OTEVŘENÝCH VĚCÍ NAHORU: „nejhorší věty“ nejsou nejdelší,
  // ale ty, na kterých by člověk musel odpovědět nejvíckrát.
  vybrane.sort((a, b) => b.q.length - a.q.length || a.t.length - b.t.length);
  document.getElementById("pocitadlo").textContent =
    vybrane.length + " z " + VETY.length;
  document.getElementById("seznam").innerHTML = vybrane.length
    ? vybrane.map(v => '<details class="veta">'
        + '<summary><span class="stav" style="background:' + BARVA[v.s] + '">'
        + esc(v.s) + '</span>'
        + '<span class="pocet">' + (v.q.length ? v.q.length + "×?" : "—") + '</span>'
        + '<span class="text">' + esc(v.t) + '</span>'
        + '<span class="znacka">' + esc(v.tv) + '</span></summary>'
        + detail(v) + '</details>').join('')
    : '<div class="prazdno">Nic, co by odpovídalo filtrům.</div>';
}}
vykreslit();
</script>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zaznam", nargs="*", help="cesta k záznamu měření")
    parser.add_argument("--do", default="", help="kam uložit HTML")
    args = parser.parse_args()

    zdroj = vyber(args.zaznam)
    zaznam = json.loads(zdroj.read_text(encoding="utf-8"))
    stranka = postav(zaznam, zdroj)
    cil = Path(args.do) if args.do else zdroj.with_suffix(".html")
    cil.write_text(stranka, encoding="utf-8")
    print(f"záznam: {zdroj.name}")
    print(f"mapa:   {cil}  ({len(stranka) / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
