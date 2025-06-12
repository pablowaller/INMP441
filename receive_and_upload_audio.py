import serial
import wave
import os
import serial.tools.list_ports
from tqdm import tqdm
import requests
import json
import base64
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import time

cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sense-bell-default-rtdb.firebaseio.com/'
})

CONFIG = {
    'sample_rate': 16000,
    'duracion_segundos': 3,
    'baudrate': 115200,
    'timeout': 10,
    'audio_folder': 'audio',
    'api_key': "YOUR_API_KEY"
}

if not os.path.exists(CONFIG['audio_folder']):
    os.makedirs(CONFIG['audio_folder'])

def detectar_puerto_esp32():
    puertos = serial.tools.list_ports.comports()
    for p in puertos:
        if 'USB' in p.description or 'Serial' in p.description or 'ESP' in p.description:
            return p.device
    raise Exception("No se encontró ningún puerto ESP32")

def obtener_nombre_archivo(base="grabacion", ext=".wav"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{base}_{timestamp}{ext}"
    return os.path.join(CONFIG['audio_folder'], nombre)

def transcribir_audio(audio_file):
    with open(audio_file, 'rb') as f:
        audio_content = f.read()
    
    response = requests.post(
        f"https://speech.googleapis.com/v1/speech:recognize?key={CONFIG['api_key']}",
        headers={'Content-Type': 'application/json'},
        json={
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": CONFIG['sample_rate'],
                "languageCode": "es-AR",
                "alternativeLanguageCodes": ["en-US", "fr-FR", "de-DE", "pt-BR"],
                "enableAutomaticPunctuation": True
            },
            "audio": {
                "content": base64.b64encode(audio_content).decode('utf-8')
            }
        }
    )
    
    if not response.json().get('results'):
        return None, None
    
    result = response.json()['results'][0]
    transcript = result['alternatives'][0]['transcript']
    detected_language = result.get('languageCode', 'unknown')
    
    return transcript, detected_language

def guardar_en_firebase(transcript, language, audio_filename):
    ref = db.reference('transcriptions')
    new_transcription = {
        "text": transcript,
        "language": language,
        "audio_file": audio_filename,
        "timestamp": datetime.now().isoformat()  
    }
    ref.push(new_transcription)
    print(f"Transcripción enviada: {transcript}")

def procesar_grabacion(raw_data):

    archivo_nombre = obtener_nombre_archivo()
    with wave.open(archivo_nombre, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(CONFIG['sample_rate'])
        wf.writeframes(raw_data)
    
    transcript, language = transcribir_audio(archivo_nombre)
    if transcript and language:
        guardar_en_firebase(transcript, language, archivo_nombre)
    else:
        print("No se detectó habla en el audio")

def main():
    try:
        puerto = detectar_puerto_esp32()
        print(f"🔌 Conectando a {puerto}...")
        
        with serial.Serial(puerto, CONFIG['baudrate'], timeout=CONFIG['timeout']) as ser:
            print("⏳ Esperando al ESP32...")
            
            while True:
                linea = ser.readline().decode(errors='ignore').strip()
                if linea and "Grabando" in linea:
                    print("ESP32:", linea)
                    break
            
            while True:

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
                
                procesar_grabacion(raw)
                
                while "Grabando" not in ser.readline().decode(errors='ignore'):
                    pass

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.reference('errors').push({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

if __name__ == "__main__":
    main()
