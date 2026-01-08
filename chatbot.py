import re
import json
import requests
import webbrowser
import customtkinter as ctk
import paho.mqtt.client as mqtt_paho

from datetime import datetime
from tkinter import filedialog
from music_player.musicPlayer import Player
from lister.listAudio import AudioFileLister

import serial.tools.list_ports
import threading
import subprocess
import threading

def detect_esp32():
    ports = serial.tools.list_ports.comports()
    print(f"Se encontraron {len(ports)} puertos:")

    for port in ports:
        print(f"---")
        print(f"Dispositivo: {port.device}")
        print(f"Descripción: {port.description}")
        print(f"Hardware ID: {port.hwid}")
    for port in ports:
        # Buscamos identificadores comunes de chips serial (CP210x o CH340)
        if "CP210" in port.description or "CH340" in port.description or "USB Serial" in port.description:
            return port.device
    return None

regex_commands = {
    "esp32_flash": re.compile(r"(?i)^(?:graba(?: los archivos)?|flashea|sube archivos a) (?:la |mi )?esp32$"),
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
API_URL = "http://192.168.1.84:8000/api/v1/"

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

        self.label = ctk.CTkLabel(self, text="Asistente Huesos", font=("Roboto", 24, "bold"))
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
                device = response.json()["device"]
                print(token)
                self.login_callback(device, token, user) 
            else:
                self.error_label.configure(text="Credenciales incorrectas")
        except requests.exceptions.ConnectionError:
            self.error_label.configure(text="Error: No hay conexión con el servidor")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chatbot Asistente Virtual Huesos")
        self.geometry("500x700")

        # 1. Configuración de MQTT para el Chatbot
        self.mqtt_broker = "192.168.1.84"
        self.mqtt_port = 1883
        self.mqtt_client = mqtt_paho.Client()
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start() # Inicia el loop en un hilo secundario
            print(f"[MQTT] Conectado al broker en {self.mqtt_broker}")
        except Exception as e:
            print(f"[MQTT ERROR] No se pudo conectar al broker: {e}")

        # Contenedor principal
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def show_login(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.login_view = LoginFrame(self.container, login_callback=self.show_chat)
        self.login_view.pack(fill="both", expand=True)

    def show_chat(self, device, token, username):
        assert token is not None, "Necesitas validar tu cuenta"
        self.lister = AudioFileLister()
        try:
            with open('./utils/audio_files.txt') as file:
                songs = file.readlines()
        except Exception:
            songs = []
        
        self.player = Player([song.strip() for song in songs]) 
        self.username = username
        self.token = token
        self.device = device

        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.header = ctk.CTkLabel(self.container, text="🤖 Asistente Huesos", font=("Roboto", 20, "bold"))
        self.header.pack(pady=(20, 10))

        self.chat_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=0)

        self.input_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=20)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Escribe tu comando aquí...", height=45)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(self.input_frame, text="Enviar", width=80, height=45, command=self.send_message)
        self.send_button.pack(side="right")

        self.add_message(f"¡Hola {self.username}! Sistema listo. ¿Qué acción deseas ejecutar?", is_user=False)

    def add_message(self, message, is_user=True):
        new_message = ChatBubble(self.chat_frame, message=message, is_user=is_user)
        new_message.pack(fill="x")
        self.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self):
        user_text = self.entry.get()
        if not user_text: return
        self.add_message(user_text, is_user=True)
        self.entry.delete(0, 'end')
        self.after(600, lambda: self.ai_reply(user_text))

    # --- MÉTODO PARA NOTIFICAR AL TRABAJADOR MQTT ---
    def notify_worker(self, action_code, device_id, topic="pusuas"):
        """Envía el log de actividad al tópico pusuas."""
        payload = {
            "device_id": device_id,
            "action": action_code.upper(),
            "date": datetime.now().timestamp()
        } if topic == "pusuas" else f"{action_code.lower()}"
        print(action_code)
        try:
            self.mqtt_client.publish(topic, json.dumps(payload))
            print(f"[LOG SENT] {action_code} for Device {device_id}")
        except Exception as e:
            print(f"[LOG ERROR] No se pudo publicar en MQTT: {e}")

    def ai_reply(self, query):
        query_norm = self.player.normalize(query).lower()
        response = ""
        topic_map = {}
        action_log = "COMANDO NO PROCESADO, ERROR" # Acción por defecto si no hace match
        target_device = 0          # ID por defecto si no es un dispositivo físico
        try:
            req = requests.get(f"{API_URL}user/{self.token}/device/all/")
            if req.status_code == 200:
                devs = [f"ID {d['id']}: {d['nombre']}" for d in req.json()["devices"]]
                topic_map = {dev['is']:dev['topic'] for dev in req.json()["devices"]}
                print(topic_map)
            else: 
                devs = None
        except: 
            devs = None
            
        # 1. Lógica de Música
        if (regex_commands["musica_lista"].match(query_norm)):
            action_log = "LISTAR MUSICA"
            songs_list = [song.split("/")[-1].split(".")[0] for song in self.player.list_of_songs]
            response = f"Tus canciones:\n" + "\n".join(songs_list)

        elif (match := regex_commands["poner_musica"].match(query_norm)):
            action_log = "REPRODUCIR MUSICA"
            try:
                self.player.play(match.group(1))
                response = f"Reproduciendo {match.group(1)}"
            except Exception:
                response = f"Buscando {match.group(1)} en YouTube..."
                webbrowser.open(f"https://www.youtube.com/results?search_query={match.group(1)}")

        elif (regex_commands["musica_pausa"].match(query_norm)):
            action_log = "PAUSAR MUSICA"
            self.player.pause()
            response = "Música pausada."

        elif (regex_commands["musica_reanuda"].match(query_norm)):
            action_log = "REANUDAR MUSICA"
            self.player.resume()
            response = "Se reanudó la reproducción."

        elif (regex_commands["musica_deten"].match(query_norm)):
            action_log = "DETENER MUSICA"
            self.player.stop()
            response = "Música detenida."

        # 2. Lógica de Dispositivos (API + MQTT)
        elif (regex_commands["dispositivo_lista"].match(query_norm)):
            action_log = "LISTAR DISPOSITIVOS"
            if devs == None:
                try:
                    req = requests.get(f"{API_URL}user/{self.token}/device/all/")
                    if req.status_code == 200:
                        devs = [f"ID {d['id']}: {d['nombre']}" for d in req.json()["devices"]]
                        topic_map = {dev["id"]:dev["topic"] for dev in req.json()["devices"]}
                        print(topic_map)
                        response = "Dispositivos vinculados:\n" + "\n".join(devs)
                    else: 
                        devs = []
                        response = "No pude obtener la lista de dispositivos."
                except: 
                    action_log += " ERROR"
                    devs = None
                    response = "Error de conexión con la API."
            elif len(devs) > 0:
                response = "Dispositivos vinculados:\n" + "\n".join(devs)
            else:
                response = "No tienes algún dispositivo vinculado a tu cuenta, accede al portal web para agregarlos y poder configurarlos"

        elif (match := regex_commands["dispositivo_accion"].match(query_norm)):
            verb = match.group(1).upper() # ENCIENDE / APAGA / CONSULTA
            device_raw = match.group(2)
            
            action_log = f"{verb.upper}"

            target_device = None

            # Intentamos extraer el ID si el usuario lo dijo, si no usamos un ID de prueba (21)
            if devs == None:
                try:
                    req = requests.get(f"{API_URL}user/{self.token}/device/all/")
                    if req.status_code == 200:
                        devs = [f"ID {d['id']}: {d['nombre']}" for d in req.json()["devices"]]
                        topic_map = {dev["id"]:dev["topic"] for dev in req.json()["devices"]}
                        print(topic_map)
                        response = "Dispositivos vinculados:\n" + "\n".join(devs)
                    else: 
                        devs = []
                except: 
                    action_log += " ERROR"
                    devs = None
            
            if devs == None:
                response = "No se han detectado dispositivos"
            else:
                if len(devs) <= 0:
                    response = "No tienes algún dispositivo vinculado a tu cuenta, accede al portal web para agregarlos y poder configurarlos"
                    action_log += " ERROR"
                else:
                    if device_raw.replace(" ","").isdigit():
                        target_device_temp = int(device_raw.replace(" ",""))
                        for dev in devs:
                            if f" {str(target_device_temp)}" in dev:
                                target_device = target_device_temp
                    else:
                        for dev in devs:
                            if device_raw.replace(" ","") == dev.split(":")[-1].replace(" ",""):
                                target_device = int(dev.split(":")[0].split(" ")[-1])

                    if target_device:
                        self.notify_worker(verb,target_device,topic_map[target_device])
                        response = f"Ejecutando: {verb} en dispositivo {target_device} en topic: {topic_map[target_device]}"

                    else:
                        response = "No cuentas con un dispositivo con ese nombre o ID"

        # 3. Otros
        elif (match := regex_commands["busqueda"].match(query_norm)):
            action_log = "WEB SEARCH"
            webbrowser.open(f"https://www.google.com/search?q={match.group(1)}")
            response = f"Buscando {match.group(1)} en Google."

        elif (regex_commands["musica_update"].match(query_norm)):
            action_log = "ACTUALIZAR MUSICA"
            self.lister.create_audio_file()
            response = "Biblioteca actualizada."

        elif regex_commands["esp32_flash"].match(query_norm):
            # Ya no preguntamos por el puerto, mpremote lo hace solo
            self.add_message("📡 Preparando conexión. Por favor, selecciona los archivos.", is_user=False)
            
            file_paths = filedialog.askopenfilenames(title="Selecciona archivos para la ESP32")
            
            if file_paths:
                # Lanzamos el proceso en un hilo para que la UI de CustomTkinter no se congele
                threading.Thread(target=self.flash_process_mpremote, args=(file_paths,)).start()
            else:
                self.add_message("Operación cancelada.", is_user=False)

        else:
            action_log = "ERROR"
            response = "No entiendo ese comando."

        # --- ENVÍO OBLIGATORIO A MQTT ---
        self.notify_worker(action_log, self.device)
        self.add_message(response, is_user=False)


    def flash_process_mpremote(self, file_paths):
        try:
            self.add_message("🚀 Iniciando transferencia con mpremote...", is_user=False)
            device = detect_esp32()
            assert device is not None, "No se ha encontrado un dispositivo de ESP32"
            for path in file_paths:
                filename = path.split("/")[-1]
                # Comando: mpremote cp [origen] :[destino]
                # El ":" indica que es el sistema de archivos de la ESP32
                command = ["python", "-m", "mpremote", "cp", path, f":{filename}"]
                
                # Ejecutamos el comando
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.add_message(f"✅ {filename} subido.", is_user=False)
                else:
                    self.add_message(f"❌ Error en {filename}: {result.stderr}", is_user=False)
            
            # Opcional: Reiniciar la placa después de subir todo
            subprocess.run(["mpremote", "reset"])
            self.add_message("✨ ¡Listo! La ESP32 se ha reiniciado.", is_user=False)
            
        except Exception as e:
            self.add_message(f"⚠️ Error de sistema: {e}", is_user=False)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()