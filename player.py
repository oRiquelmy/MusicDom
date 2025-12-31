# import required modules
import os
import re
import mutagen
import streamlit as st
import base64
import requests
from bs4 import BeautifulSoup as bs
import image_search
import streamlit.components.v1 as components


@st.cache_data(ttl=3600)
def cached_fetch_image(query: str) -> str | None:
    # prefer images at least 40 KB for better visual quality
    return image_search.fetch_image_url(query, min_size=40 * 1024)

path = "C:\\Users\\rique\\Music"

st.set_page_config(layout="wide")

@st.cache_data(ttl=3600)
def fetch_image_url(query: str) -> str | None:
    """Return the first http image URL found for an image search or None.

    This function scrapes a simple image search result page and returns the
    first img `src` that looks like an http/https URL. It uses a short
    timeout and is cached for 1 hour to avoid repeated network calls.
    """
    if not query:
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        params = {"q": query, "tbm": "isch"}
        r = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=8)
        soup = bs(r.content, "html.parser")
        imgs = soup.select("img")
        for img in imgs:
            src = img.get("src") or img.get("data-src") or img.get("data-iurl")
            if src and src.startswith("http"):
                return src
    except Exception:
        return None
    return None

# Get selected music and autoplay flag from session state
selected = st.session_state.get('musica_selecionada')
autoplay = st.session_state.get('autoplay', False)

# Display name without file extension
display_name = re.sub(r'\.[^.]+$', '', selected) if selected else None

if not selected:
    st.info("Nenhuma música selecionada. Volte para a lista e escolha uma música.")
    if st.button("Voltar para lista"):
        st.switch_page("list.py")
else:
    musica_play = os.path.join(path, selected)
    if not os.path.exists(musica_play):
        st.error(f"Arquivo não encontrado: {musica_play}")
        if st.button("Voltar para lista"):
            st.switch_page("list.py")
    else:
        meta = mutagen.File(musica_play, easy=True)

        title = meta.get("title", [display_name or selected])[0] if meta else (display_name or selected)
        artist = meta.get("artist", ["Desconhecido"])[0] if meta else "Desconhecido"
        album = meta.get("album", [""])[0] if meta else ""
        year = meta.get("date", [""])[0] if meta else ""
        genre = meta.get("genre", [""])[0] if meta else ""


        # Prepare layout: left = cover placeholder, right = metadata + audio player
        player_cols = st.columns(2)
        image_placeholder = player_cols[0].empty()

        with player_cols[1]:
            st.subheader(title)

            st.write(f"**Artista:** {artist}")
            st.write(f"**Álbum:** {album}")
            st.write(f"**Ano:** {year}")
            st.write(f"**Gênero:** {genre}")

            # Start audio playback immediately (before fetching image)
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
                const p = document.getElementById('player');
                if (p) {{
                    p.play().catch(()=>{{}});
                }}
                </script>
                """
                components.html(audio_html, height=120, scrolling=False)
            except Exception:
                st.warning("Não foi possível embutir áudio para autoplay; exibindo controle de áudio padrão.")
                st.audio(musica_play)

        # Fetch and render image after audio has started (spinner shown while searching)
        search_query = " ".join(filter(None, [title, artist, album, year])) + " album cover"
        with st.spinner("Buscando capa..."):
            image_url = cached_fetch_image(search_query)

        if image_url:
            image_placeholder.image(image_url, width=350)
        else:
            image_placeholder.image("https://cdn-icons-png.flaticon.com/512/727/727245.png", width=150)
            image_placeholder.caption("Capa não encontrada — exibindo ícone padrão")
