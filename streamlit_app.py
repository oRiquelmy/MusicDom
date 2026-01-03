import streamlit as st

if "path" not in st.session_state:
    st.session_state["path"] = ""

if "musica_selecionada" not in st.session_state:
    st.session_state["musica_selecionada"] = None

if "autoplay" not in st.session_state:
    st.session_state["autoplay"] = False

if "go_to_player" not in st.session_state:
    st.session_state["go_to_player"] = False

st.sidebar.image("./assets/MusicDomLogo.png")

pg = st.navigation(
    [
        st.Page("list.py", title="Lista de músicas", icon=":material/list:"),
        st.Page("player.py", title="Reprodutor de músicas", icon=":material/play_circle:"),
        st.Page("downloader.py", title="Baixador de músicas", icon=":material/download:"),
    ],
)

pg.run()