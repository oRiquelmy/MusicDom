import os
import re
import mutagen
import streamlit as st
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import streamlit.components.v1 as components

# Tenta importar tkinter (disponível em execução local)
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

st.set_page_config(layout="wide")
st.title('MusicDom')

# Inicializa o path se não existir
if "path" not in st.session_state:
    st.session_state["path"] = ""
    st.session_state["path_loaded"] = False

# Função para detectar se está rodando localmente
def is_local_execution():
    is_cloud = any([
        os.getenv('STREAMLIT_SHARING_MODE'),
        os.getenv('IS_STREAMLIT_CLOUD'),
        'streamlit.io' in os.getenv('HOSTNAME', ''),
    ])
    return not is_cloud and TKINTER_AVAILABLE

# Função para seletor nativo (tkinter)
def select_folder_native():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    
    folder = filedialog.askdirectory(
        title="Selecionar Diretório de Músicas",
        initialdir=os.path.expanduser("~")
    )
    
    root.destroy()
    return folder

# Componente web para seleção de pasta
def web_folder_picker():
    picker_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; padding: 0; font-family: sans-serif; }
            .picker-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                width: 100%;
                justify-content: center;
            }
            .picker-button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .picker-button:active { transform: translateY(0); }
            .picker-button:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
        </style>
    </head>
    <body>
        <button id="pickFolder" class="picker-button">
            <span>📁</span>
            <span id="buttonText">Procurar...</span>
        </button>

        <script>
            const button = document.getElementById('pickFolder');
            const buttonText = document.getElementById('buttonText');

            if (!('showDirectoryPicker' in window)) {
                button.disabled = true;
                buttonText.textContent = 'Não suportado';
            }

            button.addEventListener('click', async () => {
                try {
                    button.disabled = true;
                    buttonText.textContent = 'Aguarde...';
                    
                    const dirHandle = await window.showDirectoryPicker({ mode: 'read' });
                    
                    // Tenta obter o caminho completo (funciona em alguns casos)
                    let fullPath = dirHandle.name;
                    
                    // Conta músicas
                    const musicExtensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma'];
                    let musicCount = 0;
                    
                    for await (const entry of dirHandle.values()) {
                        if (entry.kind === 'file') {
                            const ext = entry.name.substring(entry.name.lastIndexOf('.')).toLowerCase();
                            if (musicExtensions.includes(ext)) {
                                musicCount++;
                            }
                        }
                    }
                    
                    buttonText.textContent = 'Procurar...';
                    button.disabled = false;
                    
                    // Salva no storage
                    try {
                        await window.storage.set('music_directory_path', fullPath);
                    } catch (e) {}
                    
                    // Envia para Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: {
                            path: fullPath,
                            musicCount: musicCount
                        }
                    }, '*');
                    
                } catch (err) {
                    buttonText.textContent = 'Procurar...';
                    button.disabled = false;
                    if (err.name !== 'AbortError') {
                        alert('Erro: ' + err.message);
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    return components.html(picker_html, height=50)

# Carrega o caminho salvo apenas uma vez por sessão
if not st.session_state.get("path_loaded", False):
    load_script = """
    <script>
    (async function() {
        try {
            const result = await window.storage.get("music_directory_path");
            if (result && result.value) {
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: result.value
                }, "*");
            }
        } catch (e) {}
    })();
    </script>
    """
    saved_path = components.html(load_script, height=0)
    
    if saved_path:
        st.session_state["path"] = saved_path
    
    st.session_state["path_loaded"] = True

col1, col2 = st.columns([4, 1])

with col1:
    # Input manual do caminho
    path_input = st.text_input(
        "Digite o caminho até seu diretório de músicas",
        placeholder="ex: C:\\Users\\seu_usuario\\Music",
        value=st.session_state["path"],
        key="path_input_field",
        label_visibility="collapsed"
    )

with col2:
    # Detecta ambiente e exibe botão apropriado
    is_local = is_local_execution()
    
    if is_local:
        # Botão nativo (tkinter)
        if st.button(icon=":material/folder:", label="Selecinar Diretório", use_container_width=True, help="Abrir seletor de pastas do sistema"):
            folder = select_folder_native()
            if folder:
                st.session_state["path"] = folder
                # Salva persistentemente
                save_script = f"""
                <script>
                (async function() {{
                    try {{
                        await window.storage.set("music_directory_path", "{folder.replace(chr(92), chr(92)*2)}");
                    }} catch (e) {{}}
                }})();
                </script>
                """
                components.html(save_script, height=0)
                st.rerun()
    else:
        # Botão web (File System API)
        result = web_folder_picker()
        if result:
            st.session_state["path"] = result.get("path", "")
            if result.get("musicCount"):
                st.session_state["temp_music_count"] = result["musicCount"]
            st.rerun()

# Atualiza o session_state e salva persistentemente quando o usuário digita
if path_input and path_input != st.session_state["path"]:
    st.session_state["path"] = path_input
    
    # Salva no armazenamento persistente
    save_script = f"""
    <script>
    (async function() {{
        try {{
            await window.storage.set("music_directory_path", "{path_input.replace(chr(92), chr(92)*2)}");
        }} catch (e) {{}}
    }})();
    </script>
    """
    components.html(save_script, height=0)

path = st.session_state["path"]

st.markdown("---")

# Validação do caminho
if not path or not os.path.exists(path):
    if path and not os.path.exists(path):
        st.error(f"Diretório não encontrado: `{path}`")
    else:
        st.info("Digite ou selecione o caminho para seu diretório de músicas")
    
    # Dica sobre modo de execução
    if is_local:
        st.caption("**Modo Local**: Use o botão de busca para abrir o seletor nativo do sistema")
    else:
        st.caption("**Modo Web**: Use o botão de busca para selecionar a pasta (requer Chrome/Edge 86+)")
    
    st.stop()

# ===== LISTA DE MÚSICAS =====
try:
    obj = os.scandir(path)
    st.subheader(f"Músicas disponíveis em '{os.path.basename(path)}'")

    def sanitize_filename(nome):
        return re.sub(r'[\\/:*?"<>|]', '', nome).strip()

    music_count = 0
    for entry in obj:
        if entry.is_file() and not entry.name.lower().endswith("desktop.ini"):
            arquivo = os.path.join(path, entry.name)
            ext = os.path.splitext(entry.name)[1].lower()
            
            # Conta apenas arquivos de música
            if ext not in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma']:
                continue
            
            music_count += 1

            meta_read = mutagen.File(arquivo, easy=True)
            meta_artist = meta_read.get("artist", ["Desconhecido"])[0] if meta_read else "Desconhecido"

            song_cols = st.columns([3, 2, 1, 0.5])
            name_no_ext = re.sub(r'\.[^.]+$', '', entry.name)

            # ───────── Nome / Navegação ─────────
            with song_cols[0]:
                if st.button(name_no_ext, key=f"name_{entry.name}", use_container_width=True):
                    st.session_state["musica_selecionada"] = entry.name
                    st.session_state["autoplay"] = False
                    st.switch_page("player.py")

            # ───────── Artista ─────────
            with song_cols[1]:
                st.text(meta_artist)

            # ───────── Metadados ─────────
            with song_cols[2]:
                with st.expander(icon=":material/edit:", label="...", expanded=False):
                    titulo = st.text_input("Título", meta_read.get("title", [""])[0] if meta_read else "", key=f"title_{entry.name}")
                    artista = st.text_input("Artista", meta_read.get("artist", [""])[0] if meta_read else "", key=f"artist_{entry.name}")
                    album = st.text_input("Álbum", meta_read.get("album", [""])[0] if meta_read else "", key=f"album_{entry.name}")
                    year = st.text_input("Ano", meta_read.get("date", [""])[0] if meta_read else "", key=f"date_{entry.name}")
                    genre = st.text_input("Gênero", meta_read.get("genre", [""])[0] if meta_read else "", key=f"genre_{entry.name}")

                    if st.button(icon=":material/save:", label="",  key=f"save_{entry.name}", use_container_width=True):
                        if titulo:
                            titulo_limpo = sanitize_filename(titulo)
                            novo_nome = f"{titulo_limpo}{ext}"
                            destino = os.path.join(path, novo_nome)
                            if destino != arquivo and not os.path.exists(destino):
                                try:
                                    os.rename(arquivo, destino)
                                    arquivo = destino
                                except OSError as e:
                                    st.error(f"Erro ao renomear: {e}")

                        if ext == ".mp3":
                            try:
                                meta = EasyID3(arquivo)
                            except ID3NoHeaderError:
                                meta = EasyID3()
                                meta.save(arquivo)
                                meta = EasyID3(arquivo)

                            for k, v in {
                                "title": titulo,
                                "artist": artista,
                                "album": album,
                                "date": year,
                                "genre": genre
                            }.items():
                                if v:
                                    meta[k] = [v]
                                else:
                                    meta.pop(k, None)

                            meta.save()
                            st.success("Dados salvos.", icon=":material/check_circle:")
                        else:
                            st.warning("Modifcações suportadads apenas em MP3 no momento.")

            # ───────── Play ─────────
            with song_cols[3]:
                if st.button(icon=":material/play_circle:", label="", key=f'play_{entry.name}', help="Reproduzir", use_container_width=True):
                    st.session_state["musica_selecionada"] = entry.name
                    st.session_state["autoplay"] = True
                    st.switch_page("player.py")
    
    if music_count == 0:
        st.warning("Nenhum arquivo de música encontrado neste diretório")
        st.info("Formatos suportados: MP3, WAV, OGG, M4A, FLAC, AAC, WMA")
    else:
        st.caption(f"Total: {music_count} música{'s' if music_count != 1 else ''}")

except PermissionError:
    st.error("Sem permissão de acesso ao diretório")
except Exception as e:
    st.error("Erro ao acessar o diretório")
    st.exception(e)