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

ISLANDS = {
    "University": {
        "icon": "☁️",
        "blurb": "Classes, deadlines, and May 2027 graduation.",
        "columns": {"Course": "text", "Deadline": "text", "Status": "text"},
        "defaults": [{"Course": "", "Deadline": "", "Status": ""}],
    },
    "Research": {
        "icon": "🧬",
        "blurb": "Lab work and bioinformatics projects.",
        "columns": {"Project": "text", "Next step": "text", "Status": "text"},
        "defaults": [{"Project": "", "Next step": "", "Status": ""}],
    },
    "Kitchen": {
        "icon": "🍰",
        "blurb": "Recipes and meal plans.",
        "columns": {"Meal": "text", "Recipe / ingredients": "text", "Day planned": "text"},
        "defaults": [{"Meal": "", "Recipe / ingredients": "", "Day planned": ""}],
    },
    "Career": {
        "icon": "💼",
        "blurb": "Applications, outreach, and portfolio.",
        "columns": {"Company": "text", "Role": "text", "Date applied": "text", "Status": "text"},
        "defaults": [{"Company": "", "Role": "", "Date applied": "", "Status": ""}],
    },
    "Memory": {
        "icon": "📖",
        "blurb": "Notes, journal, and things worth keeping.",
        "columns": {"Date": "text", "Note": "text"},
        "defaults": [{"Date": "", "Note": ""}],
    },
    "Nonprofit": {
        "icon": "🌍",
        "blurb": "Volunteering and causes.",
        "columns": {"Organization": "text", "Role": "text", "Hours": "text"},
        "defaults": [{"Organization": "", "Role": "", "Hours": ""}],
    },
}


def tracker(name: str, spec: dict) -> None:
    """Editable table for an island, saved to a private local CSV."""
    path = DATA_DIR / f"{name.lower()}.csv"
    if path.exists():
        df = pd.read_csv(path, dtype=str).fillna("")
    else:
        df = pd.DataFrame(spec["defaults"])
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"editor_{name}")
    if st.button("Save", key=f"save_{name}"):
        edited.to_csv(path, index=False)
        st.success("Saved.")


def render_island(name: str) -> None:
    spec = ISLANDS[name]
    st.markdown("[← Back to Cloud City](/)")
    st.header(f"{spec['icon']} {name} Island")
    st.write(spec["blurb"])

    if name == "Research":
        st.subheader("Pinned projects")
        for title, lang, desc, url in PORTFOLIO:
            st.markdown(f"**[{title}]({url})** · {lang}  \n{desc}")
        st.subheader("Tracker")

    if name == "Career":
        st.subheader("Portfolio")
        st.markdown("GitHub: https://github.com/Makiki69")
        for title, lang, desc, url in PORTFOLIO:
            st.markdown(f"- [{title}]({url}): {desc}")
        st.subheader("Applications")

    tracker(name, spec)


selected = st.query_params.get("island")

if selected in ISLANDS:
    render_island(selected)
else:
    scene = (Path(__file__).parent / "scene.html").read_text(encoding="utf-8")
    components.html(scene, height=540)
