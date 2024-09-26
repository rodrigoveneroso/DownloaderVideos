import tkinter as tk
from tkinter import messagebox, ttk
import yt_dlp
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Resoluções válidas para vídeos do YouTube
VALID_RESOLUTIONS = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]

# Função para baixar vídeos do YouTube na qualidade selecionada
def download_youtube_video(url, quality, status_label):
    try:
        format_id = quality.split(' ')[-1].strip('()')

        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',  # Inclui o áudio junto ao vídeo
            'outtmpl': '%(title)s.%(ext)s',  # Nome do arquivo de saída
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # Faz o download do vídeo
        status_label.config(text="Download concluído!")  # Atualiza o status
    except yt_dlp.utils.DownloadError as e:
        status_label.config(text="Ocorreu um erro")
        messagebox.showerror("Erro", f"Erro no download: {str(e)}\nAlternando para o melhor formato disponível.")
        fallback_download(url, status_label)  # Tenta baixar no melhor formato disponível
    except Exception as e:
        status_label.config(text="Ocorreu um erro")
        messagebox.showerror("Erro", str(e))  # Exibe uma mensagem de erro genérica

# Função para fazer o download no melhor formato disponível se o formato escolhido falhar
def fallback_download(url, status_label):
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Melhor formato disponível
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # Faz o download do vídeo
        status_label.config(text="Download concluído no melhor formato disponível.")
    except Exception as e:
        status_label.config(text="Ocorreu um erro")
        messagebox.showerror("Erro", str(e))

# Inicia o download em uma nova thread
def start_download(url, quality_combobox, status_label):
    if not url:
        status_label.config(text="Por favor, insira uma URL válida.")
        return

    quality = quality_combobox.get()
    status_label.config(text="Baixando...")
    threading.Thread(target=download_youtube_video, args=(url, quality, status_label)).start()

# Função para buscar e exibir a miniatura do vídeo
def fetch_thumbnail(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail_url = info.get('thumbnail', None)
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                return img
    except Exception as e:
        print(f"Erro ao buscar miniatura: {e}")
        return None

# Valida se a URL foi inserida e alterna os botões de ação
def validate_url(event=None):
    url = url_entry.get().strip()  # Obtém a URL e remove espaços em branco

    if url:
        paste_button.pack_forget()
        check_url_button.pack(pady=(5, 10))  # Mostra o botão "Check URL" quando a URL é inserida
    else:
        check_url_button.pack_forget()
        paste_button.pack(pady=(5, 10))  # Mostra o botão "Paste URL" se a URL estiver vazia

# Função para verificar se a URL do YouTube é válida e listar as qualidades disponíveis
def check_url():
    url = url_entry.get()

    if not url:
        status_label.config(text="Por favor, insira uma URL do YouTube.")
        download_button.pack_forget()
        quality_combobox.pack_forget()
        thumbnail_label.pack_forget()  # Esconde a miniatura
        return

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            qualities = {}
            for f in formats:
                resolution = f.get('format_note', '')
                ext = f.get('ext', '')
                format_id = f.get('format_id', '')
                vcodec = f.get('vcodec', '')

                # Filtra formatos MP4 e WebM, e lida com streams somente de vídeo
                if resolution in VALID_RESOLUTIONS and ('avc1' in vcodec or 'vp9' in vcodec):
                    qualities[resolution] = f"{resolution} - {ext} ({format_id})"

            # Ordena as resoluções pela lista de resoluções válidas
            sorted_qualities = [qualities[res] for res in VALID_RESOLUTIONS if res in qualities]

            if sorted_qualities:
                quality_combobox['values'] = sorted_qualities
                quality_combobox.set("Escolha a Qualidade (padrão é a melhor)")
                quality_combobox.pack(pady=5)
                download_button.config(state=tk.NORMAL)  # Habilita o botão de download
                download_button.pack(pady=10)
                status_label.config(text="URL válida.")

                # Busca e exibe a miniatura
                thumbnail_img = fetch_thumbnail(url)
                if thumbnail_img:
                    thumbnail_img = thumbnail_img.resize((450, 250), Image.LANCZOS)  # Redimensiona para caber na janela
                    thumbnail_photo = ImageTk.PhotoImage(thumbnail_img)
                    thumbnail_label.config(image=thumbnail_photo)
                    thumbnail_label.image = thumbnail_photo
                    thumbnail_label.pack(pady=10)

                # Esconde o botão "Check URL" e mostra o botão "Reset URL"
                check_url_button.pack_forget()
                reset_button.pack(pady=5)

            else:
                raise ValueError("Nenhum formato válido disponível")
    except Exception as e:
        status_label.config(text="URL inválida")
        messagebox.showerror("Erro", str(e))
        download_button.pack_forget()
        quality_combobox.pack_forget()
        thumbnail_label.pack_forget()  # Esconde a miniatura

# Reseta o campo de URL e esconde os componentes
def reset_url():
    url_entry.delete(0, tk.END)
    quality_combobox.set('')
    quality_combobox['values'] = []
    quality_combobox.pack_forget()  # Esconde a combobox ao resetar
    download_button.pack_forget()
    check_url_button.pack_forget()
    reset_button.pack_forget()
    thumbnail_label.pack_forget()  # Esconde a miniatura
    paste_button.pack(pady=(5, 10))  # Mostra o botão "Paste URL" novamente
    status_label.config(text="")

# Função para colar a URL a partir do clipboard
def paste_url():
    url_entry.delete(0, tk.END)
    url_entry.insert(0, window.clipboard_get())
    validate_url()

# Cria a interface gráfica (GUI)
def create_gui():
    global url_entry, quality_combobox, download_button, reset_button, status_label, thumbnail_label, check_url_button, paste_button, window

    # Cria a janela principal
    window = tk.Tk()
    window.title("YouTube Downloader")

    # Cor de fundo da janela
    window_bg_color = window.cget("bg")

    # Label de instrução
    instruction_label = tk.Label(window, text="Escreva ou cole a URL do YouTube")
    instruction_label.pack(pady=(10, 5))  # Ajuste do padding

    # Label e entrada de URL
    url_label = tk.Label(window, text="")
    url_label.pack_forget()  # Esconde o texto "YouTube URL:"

    # Cria as bordas esquerda e direita com a mesma cor do fundo da janela
    left_border = tk.Frame(window, width=5, bg=window_bg_color)
    left_border.pack(side="left", fill="y")

    url_entry_frame = tk.Frame(window)
    url_entry_frame.pack(pady=(0, 5), padx=(15, 20))  # Ajuste do padding

    url_entry = tk.Entry(url_entry_frame, width=50)
    url_entry.pack(padx=(0, 0))  # Sem padding adicional dentro da entrada
    url_entry.bind("<KeyRelease>", validate_url)  # Mostra o botão "Check URL" na modificação

    right_border = tk.Frame(window, width=5, bg=window_bg_color)
    right_border.pack(side="right", fill="y")

    # Botão "Paste URL"
    paste_button = tk.Button(window, text="Colar URL", command=paste_url)
    paste_button.pack(pady=(5, 10))  # Ajuste do padding

    # Botão "Check URL" (inicialmente escondido)
    check_url_button = tk.Button(window, text="Verificar URL", command=check_url)
    check_url_button.pack_forget()

    # Label para miniatura (inicialmente escondido)
    thumbnail_label = tk.Label(window)
    thumbnail_label.pack_forget()

    # Combobox para qualidade (inicialmente escondido)
    quality_combobox = ttk.Combobox(window, state="readonly")
    quality_combobox.pack_forget()

    # Botão de download (inicialmente desabilitado)
    download_button = tk.Button(window, text="Baixar", state=tk.DISABLED,
                                command=lambda: start_download(url_entry.get(), quality_combobox, status_label))
    download_button.pack_forget()

    # Botão "Reset URL" (inicialmente escondido)
    reset_button = tk.Button(window, text="Resetar URL", command=reset_url)
    reset_button.pack_forget()

    # Label de status
    status_label = tk.Label(window, text="")
    status_label.pack(pady=10)

    # Executa a aplicação
    window.mainloop()

if __name__ == "__main__":
    create_gui()
