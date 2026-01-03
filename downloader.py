import streamlit as st
import shutil

try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None


def download_audio(yt_url: str, out_dir: str = '.') -> None:
    if not YoutubeDL:
        raise RuntimeError("Pacote 'yt-dlp' não está instalado. Instale com 'pip install yt-dlp'.")
    if not yt_url:
        raise ValueError("URL vazia")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{out_dir}/%(title)s.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    if not shutil.which("ffmpeg"):
        st.warning("FFmpeg não encontrado no PATH. A conversão para MP3 pode falhar; instale FFmpeg se precisar de MP3.")

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([yt_url])


st.set_page_config(layout="wide")
st.title("Baixador de músicas")

yt_url = st.text_input(
    "Copie a url da música que deseja baixar (apenas YouTube atualmente)",
    placeholder="ex: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
)

# Usa o path do session_state se disponível
default_dir = st.session_state.get("path", ".")
out_dir = st.text_input("Salvar em (diretório)", value=default_dir)

if st.button("Baixar"):
    if not yt_url:
        st.warning("Cole a URL antes de clicar em 'Baixar'.")
    else:
        try:
            st.write("Você pode trocar de página durante o download.")
            with st.spinner("Iniciando download..."):
                download_audio(yt_url, out_dir=out_dir)
            st.success("Download concluído com sucesso.")
        except Exception as e:
            st.error(f"Erro ao baixar: {e}")
            st.exception(e)