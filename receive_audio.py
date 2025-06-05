import serial
import wave
import os
import serial.tools.list_ports
from tqdm import tqdm

def detectar_puerto_esp32():
    puertos = serial.tools.list_ports.comports()
    for p in puertos:
        if 'USB' in p.description or 'Serial' in p.description or 'ESP' in p.description:
            return p.device
    raise Exception("No se encontró ningún puerto ESP32")

def obtener_nombre_archivo(base="grabacion", ext=".wav"):
    i = 0
    while True:
        nombre = f"{base}{'' if i == 0 else f'_{i}'}{ext}"
        if not os.path.exists(nombre):
            return nombre
        i += 1

CONFIG = {
    'sample_rate': 16000,
    'duracion_segundos': 3,
    'baudrate': 115200,
    'timeout': 10
}

try:
    puerto = detectar_puerto_esp32()
    print(f"🔌 Conectando a {puerto}...")
    
    with serial.Serial(puerto, CONFIG['baudrate'], timeout=CONFIG['timeout']) as ser:
        print("⏳ Esperando al ESP32...")
        
        while True:
            linea = ser.readline().decode(errors='ignore').strip()
            if linea:
                print("ESP32:", linea)
                if "Grabando" in linea:
                    break
        
        while "Grabacion completa" not in ser.readline().decode(errors='ignore'):
            pass
        
        print("📡 Recibiendo datos...")
        num_muestras = CONFIG['sample_rate'] * CONFIG['duracion_segundos']
        raw = bytearray()
        
        with tqdm(total=num_muestras * 2, unit='B', unit_scale=True) as pbar:
            while len(raw) < num_muestras * 2:
                chunk = ser.read(num_muestras * 2 - len(raw))
                if not chunk:
                    raise Exception("Tiempo de espera agotado")
                raw.extend(chunk)
                pbar.update(len(chunk))
        
        archivo_nombre = obtener_nombre_archivo()
        print(f"💾 Guardando como: {archivo_nombre}")
        
        with wave.open(archivo_nombre, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(CONFIG['sample_rate'])
            wf.writeframes(raw)
        
        print("✅ ¡Grabación guardada exitosamente!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
