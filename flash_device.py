import os
import sys
import subprocess
import time

def get_device_port():
    """
    Attempts to find the USB port automatically using mpremote.
    """
    try:
        # Lists connected devices
        result = subprocess.run(['mpremote', 'devs'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if not lines or "list" in lines[0].lower():
            return None
        # Usually, the first part of the line is the port (e.g., /dev/ttyUSB0 or COM3)
        return lines[0].split()[0]
    except Exception:
        return None

def upload_folder(device_type):
    """
    Uploads the contents of the 'esp32' or 'raspberrypico' folder to the device.
    """
    # 1. Map the selection to the correct local folder
    folder_map = {
        "esp32": "esp32",
        "pico": "raspberrypico"
    }
    
    local_folder = folder_map.get(device_type.lower())
    if not local_folder or not os.path.exists(local_folder):
        print(f"❌ Error: La carpeta '{local_folder}' no existe en este directorio.")
        return

    # 2. Find the device
    print("🔍 Buscando dispositivo conectado...")
    port = get_device_port()
    if not port:
        print("❌ Error: No se detectó ningún dispositivo MicroPython. ¿Está conectado?")
        return
    
    print(f"✅ Dispositivo detectado en: {port}")

    # 3. Upload files using mpremote
    # We iterate through files in the selected folder
    files = [f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]
    
    if not files:
        print(f"⚠️ La carpeta '{local_folder}' está vacía. Nada que subir.")
        return

    for file_name in files:
        local_path = os.path.join(local_folder, file_name)
        print(f"📤 Subiendo: {file_name} ...")
        
        try:
            # mpremote connect <port> cp <local> :<remote>
            subprocess.run(['mpremote', 'connect', port, 'cp', local_path, f':{file_name}'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al subir {file_name}: {e}")
            return

    print(f"🚀 ¡Todo listo! Reiniciando el {device_type}...")
    subprocess.run(['mpremote', 'connect', port, 'reset'])
    print("✨ Proceso finalizado con éxito.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python flash_device.py [esp32|pico]")
    else:
        target = sys.argv[1].lower()
        if target in ["esp32", "pico"]:
            upload_folder(target)
        else:
            print("Por favor especifica 'esp32' o 'pico'.")