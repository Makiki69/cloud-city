import streamlit as st

st.set_page_config(page_title="Cloud City", page_icon="☁️", layout="centered")

ISLANDS = {
    "University": ("☁️", "Classes, deadlines, May 2027"),
    "Research": ("🧬", "Lab work and bioinformatics"),
    "Kitchen": ("🍰", "Recipes and meal plans"),
    "Career": ("💼", "Applications and outreach"),
    "Memory": ("📖", "Notes and journal"),
    "Nonprofit": ("🌍", "Volunteering and causes"),
}

st.title("☁️ Cloud City")
st.caption("Pick an island to start")

cols = st.columns(3)
for i, (name, (icon, blurb)) in enumerate(ISLANDS.items()):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"## {icon}")
            st.subheader(f"{name} Island")
            st.write(blurb)
            if st.button("Enter", key=name, use_container_width=True):
                st.session_state["island"] = name

if "island" in st.session_state:
    st.divider()
    st.header(f"{ISLANDS[st.session_state['island']][0]} {st.session_state['island']} Island")
    st.info("This island is empty for now. Tell me what to build here.")
