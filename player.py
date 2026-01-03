import os
import re
import mutagen
import streamlit as st
import base64
import image_search
import streamlit.components.v1 as components


@st.cache_data(ttl=3600)
def cached_fetch_image(query: str) -> str | None:
    return image_search.fetch_image_url(query, min_size=40 * 1024)

st.set_page_config(layout="wide")

# Garante que as variáveis estão inicializadas
if "path" not in st.session_state:
    st.session_state["path"] = ""

if "musica_selecionada" not in st.session_state:
    st.session_state["musica_selecionada"] = None

if "autoplay" not in st.session_state:
    st.session_state["autoplay"] = False

path = st.session_state.get("path", "")
selected = st.session_state.get('musica_selecionada')
autoplay = st.session_state.get('autoplay', False)

# Validação do caminho
if not path or not os.path.exists(path):
    st.error("Diretório de músicas não configurado.")
    st.write("Por favor, providencie um caminho válido para suas músicas na lista.")
    if st.button("Voltar para lista"):
        st.switch_page("list.py")
    st.stop()

display_name = re.sub(r'\.[^.]+$', '', selected) if selected else None

if not selected:
    st.info("Nenhuma música selecionada. Volte para a lista e escolha uma música.")
    if st.button("Voltar para lista"):
        st.switch_page("list.py")
    st.stop()

musica_play = os.path.join(path, selected)

if not os.path.exists(musica_play):
    st.error(f"Arquivo não encontrado: {musica_play}")
    if st.button("Voltar para lista"):
        st.switch_page("list.py")
    st.stop()

# Carrega metadados
meta = mutagen.File(musica_play, easy=True)

title = meta.get("title", [display_name or selected])[0] if meta else (display_name or selected)
artist = meta.get("artist", ["Desconhecido"])[0] if meta else "Desconhecido"
album = meta.get("album", [""])[0] if meta else ""
year = meta.get("date", [""])[0] if meta else ""
genre = meta.get("genre", [""])[0] if meta else ""

player_cols = st.columns(2)
image_placeholder = player_cols[0].empty()

with player_cols[1]:
    st.subheader(title)

    st.write(f"**Artista:** {artist}")
    st.write(f"**Álbum:** {album}")
    st.write(f"**Ano:** {year}")
    st.write(f"**Gênero:** {genre}")

    try:
        with open(musica_play, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        ext = os.path.splitext(musica_play)[1].lower()
        mime = "audio/mpeg"
        if ext == ".wav":
            mime = "audio/wav"
        elif ext in [".ogg", ".oga"]:
            mime = "audio/ogg"
        elif ext in [".mp4", ".m4a"]:
            mime = "audio/mp4"
        audio_html = f"""
        <audio id="player" controls {"autoplay" if autoplay else ""} style="width:100%">
            <source src="data:{mime};base64,{b64}">
            Seu navegador não suporta o elemento de áudio.
        </audio>
        <script>
        setTimeout(function() {{
            const p = document.getElementById('player');
            if (p) {{
                p.play().catch(function() {{}});
            }}
        }}, 100);
        </script>
        """
        components.html(audio_html, height=120, scrolling=False)
    except Exception as e:
        st.warning("Não foi possível embutir áudio para autoplay; exibindo controle de áudio padrão.")
        st.audio(musica_play)

# Busca capa do álbum
search_query = " ".join(filter(None, [title, artist, album, year])) + " album cover"
with st.spinner("Buscando capa..."):
    image_url = cached_fetch_image(search_query)

if image_url:
    image_placeholder.image(image_url, width=350)
else:
    image_placeholder.image("https://cdn-icons-png.flaticon.com/512/727/727245.png", width=150)
    image_placeholder.caption("Capa não encontrada – exibindo ícone padrão")

# Botão para voltar
if st.button("← Voltar para lista"):
    st.switch_page("list.py")