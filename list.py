# import required modules
import os
import re
import mutagen
import streamlit as st
import multiprocessing
import pandas as pd
from playsound import playsound
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

# listagem de musicas
path = "C:\\Users\\rique\\Music"
obj = os.scandir(path)

st.set_page_config(layout="wide")

st.title('MusicDom')
st.write("Músicas disponíveis em '% s':" % path)

def sanitize_filename(nome):
    return re.sub(r'[\\/:*?"<>|]', '', nome).strip()

for entry in obj:
    if entry.is_file() and not entry.name.lower().endswith("desktop.ini"):

        arquivo = os.path.join(path, entry.name)
        ext = os.path.splitext(entry.name)[1].lower()

        meta_read = mutagen.File(arquivo, easy=True)
        meta_artist = meta_read.get("artist", ["Desconhecido"])[0] if meta_read else "Desconhecido"

        song_cols = st.columns(4)
        name_no_ext = re.sub(r'\.[^.]+$', '', entry.name)

        with song_cols[0]:
            if st.button(name_no_ext, key=f"name_{entry.name}"):
                st.session_state['musica_selecionada'] = entry.name
                st.session_state['autoplay'] = False
                st.switch_page("player.py")

        with song_cols[1]:
            st.text(meta_artist)

        with song_cols[2]:
            with st.expander("..."):
                titulo = st.text_input("Título", meta_read.get("title", [""])[0] if meta_read else "", key=f"title_{entry.name}")
                artista = st.text_input("Artista", meta_read.get("artist", [""])[0] if meta_read else "", key=f"artist_{entry.name}")
                album = st.text_input("Álbum", meta_read.get("album", [""])[0] if meta_read else "", key=f"album_{entry.name}")
                year = st.text_input("Ano", meta_read.get("date", [""])[0] if meta_read else "", key=f"date_{entry.name}")
                genre = st.text_input("Gênero", meta_read.get("genre", [""])[0] if meta_read else "", key=f"genre_{entry.name}")

                if st.button("Salvar metadados", key=f"save_{entry.name}"):

                    # ─── RENOMEAR ARQUIVO (opcional) ─────────────────────
                    if titulo:
                        titulo_limpo = sanitize_filename(titulo)
                        novo_nome = f"{titulo_limpo}{ext}"
                        destino = os.path.join(path, novo_nome)

                        if destino != arquivo and not os.path.exists(destino):
                            os.rename(arquivo, destino)
                            arquivo = destino  # atualiza referência

                    # ─── MP3 ────────────────────────────────────────────
                    if ext == ".mp3":
                        try:
                            meta = EasyID3(arquivo)
                        except ID3NoHeaderError:
                            meta = EasyID3()
                            meta.save(arquivo)
                            meta = EasyID3(arquivo)

                        # Assign lists (EasyID3 expects list-like values)
                        if titulo:
                            meta["title"] = [titulo]
                        else:
                            meta.pop("title", None)

                        if artista:
                            meta["artist"] = [artista]
                        else:
                            meta.pop("artist", None)

                        if album:
                            meta["album"] = [album]
                        else:
                            meta.pop("album", None)

                        if year:
                            meta["date"] = [year]
                        else:
                            meta.pop("date", None)

                        if genre:
                            meta["genre"] = [genre]
                        else:
                            meta.pop("genre", None)

                        meta.save()

                    # ─── OUTROS FORMATOS ────────────────────────────────
                    else:
                        try:
                            # FLAC
                            if ext == ".flac":
                                from mutagen.flac import FLAC
                                tags = FLAC(arquivo)
                                for k, v in {"title": titulo, "artist": artista, "album": album, "date": year, "genre": genre}.items():
                                    if v:
                                        tags[k] = [v]
                                    else:
                                        tags.pop(k, None)
                                tags.save()

                            # MP4 / M4A / AAC
                            elif ext in [".m4a", ".mp4", ".aac"]:
                                from mutagen.mp4 import MP4
                                tags = MP4(arquivo)
                                mp4_map = {"title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb", "date": "\xa9day", "genre": "\xa9gen"}
                                for k, v in {"title": titulo, "artist": artista, "album": album, "date": year, "genre": genre}.items():
                                    if v:
                                        tags[mp4_map[k]] = [v]
                                    else:
                                        tags.pop(mp4_map[k], None)
                                tags.save()

                            # OGG / OGA / OPUS
                            elif ext in [".ogg", ".oga", ".opus"]:
                                from mutagen.oggvorbis import OggVorbis
                                tags = OggVorbis(arquivo)
                                for k, v in {"title": titulo, "artist": artista, "album": album, "date": year, "genre": genre}.items():
                                    if v:
                                        tags[k] = [v]
                                    else:
                                        tags.pop(k, None)
                                tags.save()

                            # WAV (RIFF INFO)
                            elif ext == ".wav":
                                try:
                                    from mutagen.wave import WAVE
                                    wav = WAVE(arquivo)
                                except Exception:
                                    wav = None

                                if not wav:
                                    st.warning("Não foi possível abrir o arquivo WAV para metadados; apenas renomeado.")
                                else:
                                    riff_map = {"title": "INAM", "artist": "IART", "album": "IPRD", "date": "ICRD", "genre": "IGNR"}
                                    for k, v in {"title": titulo, "artist": artista, "album": album, "date": year, "genre": genre}.items():
                                        rk = riff_map[k]
                                        if v:
                                            # RIFF INFO fields are simple strings
                                            wav[rk] = v
                                        else:
                                            try:
                                                wav.pop(rk, None)
                                            except KeyError:
                                                pass
                                    try:
                                        wav.save()
                                    except Exception as e:
                                        st.warning(f"Não foi possível salvar metadados WAV: {e}; apenas renomeado.")

                            # Generic easy interface fallback
                            else:
                                tags = mutagen.File(arquivo, easy=True)
                                if not tags:
                                    st.warning("Formato não suportado para metadados; apenas renomeado.")
                                else:
                                    for k, v in {"title": titulo, "artist": artista, "album": album, "date": year, "genre": genre}.items():
                                        if v:
                                            tags[k] = [v]
                                        else:
                                            tags.pop(k, None)
                                    tags.save()
                        except Exception as e:
                            st.error(f"Erro ao salvar metadados: {e}")
                            st.stop()

                    st.success("Metadados atualizados com sucesso.")

        with song_cols[3]:
            if st.button(label="", icon=":material/play_circle:", key=f'play_{entry.name}'):
                st.session_state['musica_selecionada'] = entry.name
                st.session_state['autoplay'] = True
                st.switch_page("player.py")
