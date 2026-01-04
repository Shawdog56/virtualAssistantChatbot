import re
import json
import requests
import webbrowser
import customtkinter as ctk

from datetime import datetime
from music_player.musicPlayer import Player
from lister.listAudio import AudioFileLister

regex_commands = {
    "poner_musica": re.compile(r"(?i)^(?:reproduce(?: la cancion| en youtube)?|puedes poner(?: la cancion)?|pon(?: la cancion)?) (.+)$"),
    "busqueda": re.compile(r"(?i)^(?:busca(?: en internet| en google)?|investiga) (.+)$"),
    "dispositivo_accion": re.compile(r"(?i)^(enciende|apaga|consulta(?: estado de)?) (?:(?:mi )?dispositivo )?(.+)$"),
    "dispositivo_lista": re.compile(r"(?i)^(?:muestrame |cuales son )?(?:mis )?dispositivos$"),
    "musica_lista": re.compile(r"(?i)^((?:muestrame |cuales son )?(?:mis )?canciones|lista mi musica|musica)$"),
    "musica_update": re.compile(r"(?i)^actualiza(?:te| la biblioteca)?$"),
    "musica_pausa": re.compile(r"(?i)^(?:pausa|para momentaneamente)(?: la (musica|cancion))?$"),
    "musica_reanuda": re.compile(r"(?i)^(?:reanuda|continua(?: con)?(?: la (musica|cancion))?|sigue(?: con la (musica|cancion))?)$"),
    "musica_deten": re.compile(r"(?i)^(?:deten(?: la (musica|cancion))?|detente|para(?: la (musica|cancion))?|quita la (musica|cancion))$")
}

# Configuración del servidor (Tu API de Django)
API_URL = "http://127.0.0.1:8000/api/v1/"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, message, is_user=True, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        side = "right" if is_user else "left"
        anchor_point = "e" if is_user else "w"
        
        # 1. The Message Bubble
        self.bubble = ctk.CTkFrame(self, fg_color="#1f538d" if is_user else "#3d3d3d", corner_radius=15)
        self.bubble.pack(side=side, padx=(50, 10) if is_user else (10, 50), pady=5)
        
        self.label = ctk.CTkLabel(
            self.bubble, text=message, wraplength=300, 
            justify=side, anchor=anchor_point, # Pushes text inside the bubble
            padx=15, pady=10
        )
        self.label.pack()
        
        # 2. The Time Label
        self.time_label = ctk.CTkLabel(
            self, text=datetime.now().strftime("%H:%M"), 
            font=("Roboto", 10), text_color="gray"
        )
        # side=side puts it on the correct side of the frame
        # anchor=anchor_point ensures it aligns with the edge of the bubble
        self.time_label.pack(side=side, anchor=anchor_point, padx=15)


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.login_callback = login_callback

        self.label = ctk.CTkLabel(self, text="Soporte TI - LIXIL", font=("Roboto", 24, "bold"))
        self.label.pack(pady=40)

        self.username = ctk.CTkEntry(self, placeholder_text="Usuario", width=250)
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=250)
        self.password.pack(pady=10)

        self.login_button = ctk.CTkButton(self, text="Iniciar Sesión", command=self.attempt_login)
        self.login_button.pack(pady=20)

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()

    def attempt_login(self):
        user = self.username.get()
        pw = self.password.get()

        try:
            # Enviamos credenciales a tu API de Django
            response = requests.post(f"{API_URL}login/", json={"username": user, "password": pw})
            
            if response.status_code == 200:
                token = response.json()["token"]
                print(token)
                self.login_callback(token, user) 
            else:
                self.error_label.configure(text="Credenciales incorrectas")
        except requests.exceptions.ConnectionError:
            self.error_label.configure(text="Error: No hay conexión con el servidor")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LIXIL Assistant")
        self.geometry("500x700")

        # Contenedor principal
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Mostrar pantalla de login al inicio
        self.show_login()

    def show_login(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        
        self.login_view = LoginFrame(self.container, login_callback=self.show_chat)
        self.login_view.pack(fill="both", expand=True)

    def show_chat(self, token, username):
        assert token is not None, "Necesitas validar tu cuenta"
        self.lister = AudioFileLister()
        try:
            with open('./utils/audio_files.txt') as file:
                songs = file.readlines()
        except Exception:
            songs = None
        
        # Inicializamos el reproductor de música/audio que definimos antes
        self.player = Player([song.strip() for song in songs]) 
        self.username = username
        # Limpiamos el contenedor (Login -> Chat)
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.token = token

        # 1. Título superior (Altura fija)
        self.header = ctk.CTkLabel(self.container, text="🤖 Asistente personal", font=("Roboto", 20, "bold"))
        self.header.pack(pady=(20, 10)) # Padding superior mayor que el inferior

        # 2. Área de Chat (Prioridad de expansión)
        # expand=True hace que este widget "empuje" a los demás y tome el espacio sobrante
        self.chat_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=0)

        # 3. Contenedor inferior de entrada (Altura fija al fondo)
        self.input_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=20)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Escribe tu comando aquí...", height=45)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(self.input_frame, text="Enviar", width=80, height=45, command=self.send_message)
        self.send_button.pack(side="right")

        # Mensaje de bienvenida
        self.add_message(f"¡Hola {self.username}! Soy tu asistente de TI. ¿En qué puedo ayudarte hoy?", is_user=False)

    def add_message(self, message, is_user=True):
        new_message = ChatBubble(self.chat_frame, message=message, is_user=is_user)
        new_message.pack(fill="x")
        # Lógica de Autoscroll:
        # 1. Forzamos a la ventana a procesar los widgets recién creados (idletasks)
        self.update_idletasks()
        
        # 2. Movemos la vista al final (1.0 representa el 100% del scroll vertical)
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self):
        user_text = self.entry.get()
        if not user_text: return
        
        # 1. Mostrar mensaje del usuario
        self.add_message(user_text, is_user=True)
        self.entry.delete(0, 'end')

        # 2. Lógica de respuesta "IA"
        self.after(600, lambda: self.ai_reply(user_text))

    def ai_reply(self, query):
        query_norm = self.player.normalize(query).lower()

        if (lista_musica := regex_commands["musica_lista"].match(query_norm)):
            response = f"Listando tus canciones\n{"\n".join([song.split("/")[-1].split(".")[0] for song in self.player.list_of_songs])}"
        elif (poner_musica := regex_commands["poner_musica"].match(query_norm)):
            try:
                self.player.play(poner_musica.group(1))
                response = f"Reproduciento {poner_musica.group(1)} en tu ordenador"
            except Exception:
                self.add_message(f"No he podido reproducir {poner_musica.group(1)} en tu ordenador, buscando en youtube...", is_user=False)
                URL = f"https://www.youtube.com/results?search_query={poner_musica.group(1)}"
                webbrowser.open(URL)
                response = f"Abriendo youtube con la búsqueda de {poner_musica.group(1)}"
        elif (pausar_musica := regex_commands["musica_pausa"].match(query_norm)):
            self.player.pause()
            response = f"Pausando música..."
        elif (detener_musica := regex_commands["musica_deten"].match(query_norm)):
            self.player.stop()
            response = f"Deteniendo música..."
        elif (reanudar_musica := regex_commands["musica_reanuda"].match(query_norm)):
            self.player.resume()
            response = f"Reanudando música..."
        elif (actualizar_musica := regex_commands["musica_update"].match(query_norm)):
            self.lister.create_audio_file()
            self.add_message("Actualizando biblioteca, esto puede tomar un momento...",is_user=False)
            response = "Biblioteca de música actualizada"
        elif (mostrar_dispositivos := regex_commands["dispositivo_lista"].match(query_norm)):
            print(f"{API_URL}user/{self.token}/device/all/")
            try:
                request = requests.get(url=f"{API_URL}user/{self.token}/device/all/")
                if request.status_code == 200:
                    devices = [f"{device["id"]}: {device["nombre"]} :: {device["topic"]}" for device in request.json()["devices"]]
                    string = "\n---\n".join(devices)
                    response = f"Todos tus dispositivos:\n{string}"
                else:
                    raise Exception("No se recibieron los dispositivos correctamente")
            except requests.exceptions.ConnectionError:
                response = "No se pudo conectar con el servidor, intenta de nuevo"
            except Exception:
                response = "No se encontraron dispositivos vinculados a tu cuenta"
        elif (accion_dispositivo := regex_commands["dispositivo_accion"].match(query_norm)):
            response = f"Enviando acción a Dispositivo {accion_dispositivo.group(1)}"
        elif (busqueda := regex_commands["busqueda"].match(query_norm)):
            response = f"Abriendo el navegador para buscar {busqueda.group(1)}"
            webbrowser.open(f"https://www.google.com/search?q={busqueda.group(1)}")
        else:
            response = f"Lo siento, no he podido procesar tu solicitud"

        self.add_message(response, is_user=False)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()