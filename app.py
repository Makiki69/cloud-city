from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Cloud City", page_icon="☁️", layout="centered")

ISLANDS = {
    "University": ("☁️", "Classes, deadlines, May 2027"),
    "Research": ("🧬", "Lab work and bioinformatics"),
    "Kitchen": ("🍰", "Recipes and meal plans"),
    "Career": ("💼", "Applications and outreach"),
    "Memory": ("📖", "Notes and journal"),
    "Nonprofit": ("🌍", "Volunteering and causes"),
}

selected = st.query_params.get("island")

if selected in ISLANDS:
    icon, blurb = ISLANDS[selected]
    st.markdown("[← Back to Cloud City](/)")
    st.header(f"{icon} {selected} Island")
    st.write(blurb)
    st.info("This island is empty for now. Tell me what to build here.")
else:
    scene = (Path(__file__).parent / "scene.html").read_text(encoding="utf-8")
    components.html(scene, height=540)
