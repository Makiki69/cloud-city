import json
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Cloud City", page_icon="☁️", layout="centered")

DATA_DIR = Path(__file__).parent / "data"  # private: gitignored, never pushed
DATA_DIR.mkdir(exist_ok=True)

# Portfolio content from github.com/Makiki69 (public repos)
PORTFOLIO = [
    ("Bioactive compound screening and modeling", "Python", "Drug discovery pipeline: RDKit fingerprint similarity ranking of natural compounds against known antifungals.", "https://github.com/Makiki69/Bioactive-compound-screening-and-modeling"),
    ("Bulk RNA-seq differential expression", "R", "End-to-end bulk RNA-seq analysis of stress and infection conditions using public GEO data and DESeq2.", "https://github.com/Makiki69/Bulk-RNA-seq-Differential-Expression-Analysis"),
    ("De novo genome assembly", "Shell", "De novo assembly of E. coli K-12 MiSeq reads with k-mer optimization in Velvet.", "https://github.com/Makiki69/Denovo-Genome-Assembly"),
]

# Which Notion page titles (case-insensitive keywords) belong on which island
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
        "icon": "☁️",
        "blurb": "Classes, deadlines, and May 2027 graduation.",
        "defaults": [{"Course": "", "Deadline": "", "Status": ""}],
    },
    "Research": {
        "icon": "🧬",
        "blurb": "Lab work and bioinformatics projects.",
        "defaults": [{"Project": "", "Next step": "", "Status": ""}],
    },
    "Kitchen": {
        "icon": "🍰",
        "blurb": "Recipes, teas, and meal plans.",
        "defaults": [{"Meal": "", "Recipe / ingredients": "", "Day planned": ""}],
    },
    "Career": {
        "icon": "💼",
        "blurb": "Applications, outreach, and portfolio.",
        "defaults": [{"Company": "", "Role": "", "Date applied": "", "Status": ""}],
    },
    "Memory": {
        "icon": "📖",
        "blurb": "Notes, journal, and things worth keeping.",
        "defaults": [{"Date": "", "Note": ""}],
    },
    "Nonprofit": {
        "icon": "🌍",
        "blurb": "Volunteering and causes.",
        "defaults": [{"Organization": "", "Role": "", "Hours": ""}],
    },
}


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
    """All pages shared with the Cloud City integration."""
    data = notion_request("search", {"page_size": 100, "filter": {"property": "object", "value": "page"}})
    return [{"id": p["id"], "title": page_title(p), "url": p["url"]} for p in data["results"]]


@st.cache_data(ttl=600, show_spinner=False)
def notion_text(page_id: str) -> str:
    """Plain text of a page's first 100 blocks."""
    data = notion_request(f"blocks/{page_id}/children?page_size=100")
    lines = []
    for block in data["results"]:
        kind = block["type"]
        rich = block.get(kind, {}).get("rich_text", [])
        text = "".join(t["plain_text"] for t in rich)
        if text:
            prefix = "- " if "list_item" in kind or kind == "to_do" else ""
            lines.append(prefix + text)
    return "\n\n".join(lines)


def notion_section(name: str) -> None:
    keywords = NOTION_KEYWORDS.get(name, [])
    if not keywords:
        return
    if "NOTION_TOKEN" not in st.secrets or st.secrets["NOTION_TOKEN"].startswith("PASTE"):
        st.info("Notion isn't connected yet. Add your token to `.streamlit/secrets.toml`.")
        return
    try:
        pages = [p for p in notion_pages() if any(k in p["title"].lower() for k in keywords)]
    except Exception as exc:  # show the problem instead of crashing the page
        st.error(f"Couldn't reach Notion: {exc}")
        return
    if not pages:
        st.caption("No matching Notion pages yet.")
        return
    st.subheader("From Notion")
    for page in pages:
        with st.expander(page["title"]):
            try:
                body = notion_text(page["id"])
                st.markdown(body[:4000] or "_(no text on this page)_")
            except Exception as exc:
                st.error(f"Couldn't load this page: {exc}")
            st.markdown(f"[Open in Notion]({page['url']})")


def tracker(name: str, spec: dict) -> None:
    """Editable table for an island, autosaved to a private local CSV."""
    path = DATA_DIR / f"{name.lower()}.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str).fillna("")
    else:
        df = pd.DataFrame(spec["defaults"])
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{name}")
    if not edited.equals(df):
        edited.to_csv(path, index=False)
        st.caption("Saved just now.")


def render_island(name: str) -> None:
    spec = ISLANDS[name]
    st.markdown("[← Back to Cloud City](/)")
    st.header(f"{spec['icon']} {name} Island")
    st.write(spec["blurb"])

    if name == "Research":
        st.subheader("Pinned projects")
        for title, lang, desc, url in PORTFOLIO:
            st.markdown(f"**[{title}]({url})** · {lang}  \n{desc}")

    if name == "Career":
        st.subheader("Portfolio")
        st.markdown("GitHub: https://github.com/Makiki69")
        for title, lang, desc, url in PORTFOLIO:
            st.markdown(f"- [{title}]({url}): {desc}")

    notion_section(name)
    st.subheader("Tracker")
    tracker(name, spec)


selected = st.query_params.get("island")

if selected in ISLANDS:
    render_island(selected)
else:
    scene = (Path(__file__).parent / "scene.html").read_text(encoding="utf-8")
    components.html(scene, height=540)
