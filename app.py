import json
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cloud City", page_icon="☁️", layout="wide")
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {display: none;}
    .block-container {padding: 0.5rem 1.5rem 2rem 1.5rem !important; max-width: 1200px;}
    .mascot {font-size: 96px; text-align: center; line-height: 1.1; animation: bounce 2.4s ease-in-out infinite;}
    @keyframes bounce {0%,100%{transform: translateY(0);} 50%{transform: translateY(-10px);}}
    .card-title {font-weight: 700; font-size: 1.05rem; margin-bottom: 0.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path(__file__).parent / "data"  # private: gitignored, never pushed
DATA_DIR.mkdir(exist_ok=True)

XP_PER_ENTRY = 10
XP_PER_NOTION_PAGE = 5
XP_PER_LEVEL = 50

# Portfolio content from github.com/Makiki69 (public repos)
PORTFOLIO = [
    ("Bioactive compound screening and modeling", "Python", "Drug discovery pipeline: RDKit fingerprint similarity ranking of natural compounds against known antifungals.", "https://github.com/Makiki69/Bioactive-compound-screening-and-modeling"),
    ("Bulk RNA-seq differential expression", "R", "End-to-end bulk RNA-seq analysis of stress and infection conditions using public GEO data and DESeq2.", "https://github.com/Makiki69/Bulk-RNA-seq-Differential-Expression-Analysis"),
    ("De novo genome assembly", "Shell", "De novo assembly of E. coli K-12 MiSeq reads with k-mer optimization in Velvet.", "https://github.com/Makiki69/Denovo-Genome-Assembly"),
]

# Notion page titles (case-insensitive keywords) that belong on each island
NOTION_KEYWORDS = {
    "University": ["senior year"],
    "Research": ["bioinformat", "lepto", "metabol", "dataset", "papers"],
    "Kitchen": ["food", "meat", "roast", "orange", "tea", "chamomile", "grey", "rooibos",
                "sleepytime", "lemon", "berry", "peach", "matcha", "oolong", "lavender",
                "breakfast", "teatime", "mint", "raspberry", "rosemary"],
    "Career": ["job", "linkedin"],
    "Memory": ["notes", "to-do"],
    "Nonprofit": ["nonprofit", "volunteer"],
}

ISLANDS = {
    "University": {
        "icon": "☁️", "mascot": "🦉", "mascot_name": "Hoot",
        "blurb": "Classes, deadlines, and May 2027 graduation.",
        "columns": ["Course", "Deadline", "Status"],
    },
    "Research": {
        "icon": "🧬", "mascot": "🐙", "mascot_name": "Inky",
        "blurb": "Lab work and bioinformatics projects.",
        "columns": ["Project", "Next step", "Status"],
    },
    "Kitchen": {
        "icon": "🍰", "mascot": "🐰", "mascot_name": "Whisk",
        "blurb": "Recipes, teas, and meal plans.",
        "columns": ["Meal", "Recipe / ingredients", "Day planned"],
    },
    "Career": {
        "icon": "💼", "mascot": "🦊", "mascot_name": "Scout",
        "blurb": "Applications, outreach, and portfolio.",
        "columns": ["Company", "Role", "Date applied", "Status"],
    },
    "Memory": {
        "icon": "📖", "mascot": "🐢", "mascot_name": "Pages",
        "blurb": "Notes, journal, and things worth keeping.",
        "columns": ["Date", "Note"],
    },
    "Nonprofit": {
        "icon": "🌍", "mascot": "🐼", "mascot_name": "Bamboo",
        "blurb": "Volunteering and causes.",
        "columns": ["Organization", "Role", "Hours"],
    },
}


# ---------- Notion ----------

def notion_request(path: str, body: dict | None = None) -> dict:
    token = st.secrets["NOTION_TOKEN"]
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def page_title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


@st.cache_data(ttl=600, show_spinner=False)
def notion_pages() -> list[dict]:
    data = notion_request("search", {"page_size": 100, "filter": {"property": "object", "value": "page"}})
    return [{"id": p["id"], "title": page_title(p), "url": p["url"]} for p in data["results"]]


@st.cache_data(ttl=600, show_spinner=False)
def notion_text(page_id: str) -> str:
    data = notion_request(f"blocks/{page_id}/children?page_size=100")
    lines = []
    for block in data["results"]:
        kind = block["type"]
        text = "".join(t["plain_text"] for t in block.get(kind, {}).get("rich_text", []))
        if text:
            lines.append(("- " if "list_item" in kind or kind == "to_do" else "") + text)
    return "\n\n".join(lines)


def notion_connected() -> bool:
    return "NOTION_TOKEN" in st.secrets and not st.secrets["NOTION_TOKEN"].startswith("PASTE")


def island_notion_pages(name: str) -> list[dict]:
    keywords = NOTION_KEYWORDS.get(name, [])
    if not keywords or not notion_connected():
        return []
    try:
        return [p for p in notion_pages() if any(k in p["title"].lower() for k in keywords)]
    except Exception as exc:
        st.error(f"Couldn't reach Notion: {exc}")
        return []


# ---------- Local trackers (private CSV) ----------

def load_entries(name: str, columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / f"{name.lower()}.csv"
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame(columns=columns)


def save_entries(name: str, df: pd.DataFrame) -> None:
    df.to_csv(DATA_DIR / f"{name.lower()}.csv", index=False)


def filled_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]


# ---------- Island page ----------

def dashboard_tab(name: str, spec: dict, df: pd.DataFrame, notion: list[dict]) -> None:
    entries = len(filled_rows(df))
    xp = entries * XP_PER_ENTRY + len(notion) * XP_PER_NOTION_PAGE
    level = xp // XP_PER_LEVEL + 1
    progress = (xp % XP_PER_LEVEL) / XP_PER_LEVEL

    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div class='mascot'>{spec['mascot']}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center'><b>{spec['mascot_name']}</b> · Level {level}</p>", unsafe_allow_html=True)
        st.progress(progress, text=f"{xp % XP_PER_LEVEL}/{XP_PER_LEVEL} XP to next level")
    with right:
        m1, m2, m3 = st.columns(3)
        m1.metric("Entries", entries)
        m2.metric("Notion pages", len(notion))
        m3.metric("Total XP", xp)
        status_col = next((c for c in spec["columns"] if c.lower() == "status"), None)
        if status_col and entries:
            counts = filled_rows(df)[status_col].replace("", "No status").value_counts()
            st.markdown("**By status**")
            st.bar_chart(counts)
        else:
            st.caption("Add a few entries and your stats and chart will show up here.")


def add_tab(name: str, spec: dict, df: pd.DataFrame) -> None:
    with st.form(f"add_form_{name}", clear_on_submit=True):
        values = {c: st.text_input(c, key=f"{name}_{c}") for c in spec["columns"]}
        if st.form_submit_button(f"Add to {name} Island", type="primary"):
            if any(v.strip() for v in values.values()):
                save_entries(name, pd.concat([df, pd.DataFrame([values])], ignore_index=True))
                st.success("Added! Check the Gallery or Dashboard.")
            else:
                st.warning("Fill in at least one field.")


def gallery_tab(name: str, spec: dict, df: pd.DataFrame, notion: list[dict]) -> None:
    if name in ("Research", "Career"):
        st.subheader("Portfolio")
        cols = st.columns(3)
        for i, (title, lang, desc, url) in enumerate(PORTFOLIO):
            with cols[i % 3].container(border=True):
                st.markdown(f"<div class='card-title'>{spec['mascot']} {title}</div>", unsafe_allow_html=True)
                st.caption(lang)
                st.write(desc)
                st.markdown(f"[View on GitHub]({url})")

    rows = filled_rows(df)
    st.subheader("Your entries")
    if rows.empty:
        st.caption("Nothing here yet. Use the Add tab.")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(rows.iterrows()):
            first, *rest = spec["columns"]
            with cols[i % 3].container(border=True):
                st.markdown(f"<div class='card-title'>{spec['mascot']} {row[first] or '(untitled)'}</div>", unsafe_allow_html=True)
                for c in rest:
                    if str(row[c]).strip():
                        st.write(f"**{c}:** {row[c]}")

    if notion:
        st.subheader("From Notion")
        for page in notion:
            with st.expander(f"📄 {page['title']}"):
                try:
                    st.markdown(notion_text(page["id"])[:4000] or "_(no text on this page)_")
                except Exception as exc:
                    st.error(f"Couldn't load this page: {exc}")
                st.markdown(f"[Open in Notion]({page['url']})")


def table_tab(name: str, spec: dict, df: pd.DataFrame) -> None:
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{name}")
    if not edited.equals(df):
        save_entries(name, edited)
        st.caption("Saved just now.")


def render_island(name: str) -> None:
    spec = ISLANDS[name]
    st.markdown("[← Back to Cloud City](/)")
    st.header(f"{spec['icon']} {name} Island")
    st.write(spec["blurb"])

    df = load_entries(name, spec["columns"])
    notion = island_notion_pages(name)

    dash, add, gallery, table = st.tabs(["🏠 Dashboard", "➕ Add content", "🖼️ Gallery", "📋 Table"])
    with dash:
        dashboard_tab(name, spec, df, notion)
    with add:
        add_tab(name, spec, df)
    with gallery:
        gallery_tab(name, spec, df, notion)
    with table:
        table_tab(name, spec, df)


# Island positions on the scene, as percentages of its width and height
ISLAND_POS = {
    "University": (50, 30),
    "Research": (22, 50),
    "Kitchen": (78, 48),
    "Career": (50, 66),
    "Memory": (84, 78),
    "Nonprofit": (36, 88),
}

SCENE_CSS = """
<style>
.cc-scene{position:relative;height:640px;overflow:hidden;border-radius:24px;
  background:linear-gradient(to bottom,#9ed8ff 0%,#e9f7ff 100%);font-family:"Segoe UI",system-ui,sans-serif;color:#1f3550;}
.cc-title{position:absolute;top:22px;left:0;right:0;text-align:center;pointer-events:none;}
.cc-title .cc-h{font-size:2.4rem;font-weight:700;margin:0;}
.cc-title .cc-sub{opacity:.7;margin-top:4px;}
.cc-cloud{position:absolute;height:60px;background:rgba(255,255,255,.6);border-radius:100px;animation:cc-drift linear infinite;}
@keyframes cc-drift{from{transform:translateX(-30%);}to{transform:translateX(130%);}}
a.cc-island{position:absolute;transform:translate(-50%,-50%);width:200px;text-align:center;text-decoration:none!important;color:#1f3550!important;animation:cc-bob 6s ease-in-out infinite;transition:transform .25s ease;}
a.cc-island:hover{transform:translate(-50%,-50%) scale(1.07);}
@keyframes cc-bob{0%,100%{margin-top:0;}50%{margin-top:-12px;}}
.cc-emoji{font-size:64px;line-height:1;filter:drop-shadow(0 12px 8px rgba(31,53,80,.25));}
.cc-ground{width:140px;height:24px;margin:-6px auto 0;background:linear-gradient(#b9e6a0,#7cc56b 40%,#8a7055 42%,#5e4a38);border-radius:0 0 60px 60px/0 0 30px 30px;}
.cc-label{display:inline-block;margin-top:8px;padding:3px 12px;border-radius:12px;background:rgba(255,255,255,.85);font-size:.9rem;font-weight:600;}
.cc-footer{position:absolute;bottom:10px;width:100%;text-align:center;font-size:.8rem;opacity:.6;pointer-events:none;}
</style>
"""


def scene_markup() -> str:
    clouds = [(160, 22, 60, -60), (240, 14, 46, -10), (300, 6, 60, -90)]
    parts = [SCENE_CSS, '<div class="cc-scene">']
    for width, top, dur, delay in clouds:
        parts.append(
            f'<div class="cc-cloud" style="width:{width}px;top:{top}%;'
            f'animation-duration:{dur * 1.2:.0f}s;animation-delay:{delay}s"></div>'
        )
    parts.append('<div class="cc-title"><div class="cc-h">☁️ Cloud City</div>'
                 '<div class="cc-sub">Pick an island to start</div></div>')
    for name, (x, y) in ISLAND_POS.items():
        spec = ISLANDS[name]
        parts.append(
            f'<a class="cc-island" href="?island={name}" style="left:{x}%;top:{y}%;">'
            f'<div class="cc-emoji">{spec["mascot"]}</div>'
            f'<div class="cc-ground"></div>'
            f'<div class="cc-label">{spec["icon"]} {name} Island</div></a>'
        )
    parts.append('<div class="cc-footer">Click an island to enter</div></div>')
    return "".join(parts)


selected = st.query_params.get("island")

if selected in ISLANDS:
    render_island(selected)
else:
    # Scene is plain page content (not an iframe) so its island links work.
    st.markdown(scene_markup(), unsafe_allow_html=True)
