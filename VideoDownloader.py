import yt_dlp
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Função para buscar as opções de resoluções e formatos de vídeo
def get_video_options(url):
    if not url:
        raise ValueError("A URL não pode estar vazia!")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            resolutions = set()
            file_types = set()

            for f in formats:
                height = f.get('height')
                if height is not None:
                    resolutions.add(height)
                file_types.add(f.get('ext', 'mp4'))
            # Adiciona manualmente os formatos MKV e AVI
            file_types.update(['mkv', 'avi'])
            return sorted(resolutions), sorted(file_types)
    except Exception as e:
        raise ValueError(f"Erro ao tentar acessar o vídeo: {e}")

# Função para limpar caracteres inválidos do nome do arquivo (para segurança no sistema de arquivos)
def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Função para baixar o vídeo utilizando o yt-dlp (sem uso explícito do ffmpeg)
def download_video(url, resolution, file_type, log_func):
    os.makedirs('downloads', exist_ok=True)

    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'restrictfilenames': True,
        'merge_output_format': file_type,  # Converte/merge para o formato desejado
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            log_func("Iniciando o download...")
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'video')
            cleaned_title = clean_filename(video_title)
            final_file = os.path.join('downloads', f"{cleaned_title}.{file_type}")
            log_func(f"Vídeo baixado com sucesso em: {final_file}")
    except Exception as e:
        log_func(f"Ocorreu um erro ao baixar o vídeo: {e}")

# Classe para a interface gráfica
class VideoDownloaderGUI:
    def __init__(self, master):
        self.master = master
        master.title("Video Downloader")

        # Criação dos elementos de interface
        self.url_label = ttk.Label(master, text="URL do Vídeo:")
        self.url_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.url_entry = ttk.Entry(master, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        self.fetch_button = ttk.Button(master, text="Buscar Opções", command=self.fetch_options)
        self.fetch_button.grid(row=0, column=2, padx=5, pady=5)

        self.res_label = ttk.Label(master, text="Resolução:")
        self.res_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.res_combobox = ttk.Combobox(master, state="readonly", width=10)
        self.res_combobox.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.format_label = ttk.Label(master, text="Formato:")
        self.format_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.format_combobox = ttk.Combobox(master, state="readonly", width=10)
        self.format_combobox.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        self.download_button = ttk.Button(master, text="Baixar Vídeo", command=self.start_download)
        self.download_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Área de log
        self.log_area = scrolledtext.ScrolledText(master, width=70, height=15, state='disabled')
        self.log_area.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def fetch_options(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, informe uma URL!")
            return

        # Limpa os combobox
        self.res_combobox['values'] = []
        self.format_combobox['values'] = []
        self.log("Buscando opções de resolução e formatos...")

        def task():
            try:
                resolutions, file_types = get_video_options(url)
                if not resolutions or not file_types:
                    self.log("Não foi possível encontrar resoluções ou formatos para esse vídeo.")
                    return

                # Atualiza os combobox com as opções encontradas.
                self.res_combobox['values'] = [f"{res}p" for res in resolutions]
                self.format_combobox['values'] = file_types

                # Define valores padrão (usando a melhor resolução e mp4)
                self.res_combobox.current(len(resolutions) - 1)  # melhor resolução (maior valor)
                try:
                    default_index = file_types.index("mp4")
                except ValueError:
                    default_index = 0
                self.format_combobox.current(default_index)
                self.log("Opções carregadas com sucesso!")
            except Exception as e:
                self.log(f"Erro: {e}")

        # Executa a tarefa em uma thread para não travar a interface
        threading.Thread(target=task).start()

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, informe uma URL!")
            return

        res_value = self.res_combobox.get()
        format_value = self.format_combobox.get()

        if not res_value or not format_value:
            messagebox.showerror("Erro", "Por favor, busque as opções primeiro!")
            return

        # Remove o "p" da resolução para obter o número
        try:
            resolution = int(res_value.replace("p", ""))
        except ValueError:
            messagebox.showerror("Erro", "Resolução inválida!")
            return

        # Inicia o download em uma thread para não travar a interface
        threading.Thread(
            target=download_video,
            args=(url, resolution, format_value, self.log)
        ).start()

# Execução da interface gráfica
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderGUI(root)
    root.mainloop()
