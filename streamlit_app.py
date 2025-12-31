import streamlit as st

pg = st.navigation(
    [
        st.Page("list.py", title="Lista de músicas", icon=":material/list:"),
        st.Page("player.py", title="Reprodutor de músicas", icon=":material/play_circle:")])
pg.run()