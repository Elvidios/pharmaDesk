import os
import json
import pandas as pd
import requests
from dotenv import load_dotenv
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


def home(request):
    # Ahora Django buscará index.html dentro de la carpeta templates
    return render(request, 'index.html')

# 1. Cargamos credenciales seguras
load_dotenv()
META_TOKEN = os.getenv('META_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

# 2. Función para enviar WhatsApp a Meta
def enviar_mensaje(numero_destino, texto):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Envío a Meta status: {response.status_code}")
        if response.status_code != 200:
            print(f"Detalle del error de Meta: {response.text}")
    except Exception as e:
        print(f"Error enviando mensaje a Meta: {e}")

def interpretar_mensaje_ia(texto_cliente):
    api_key = os.getenv('GEMINI_API_KEY').strip()
    
    prompt = f"""
    Eres el clasificador de intenciones de PharmaCare. 
    Analiza este mensaje de un cliente: "{texto_cliente}"
    
    Tu ÚNICO trabajo es responder con UNA SOLA PALABRA de esta lista exacta:
    - higiene (si el mensaje menciona boca, dientes, jabón, limpieza, cepillos, higiene bucal, pasta dental, patentar producto bucal).
    - cosmetico (si menciona cremas, maquillaje, cosmética, lociones, piel, rostro).
    - cda (si menciona importar, aduana, internación, traer de otro país).
    - validacion (si menciona calidad, eximición, origen).
    - transferencia (si menciona cambiar titularidad, vender registro).
    
    REGLA ESTRICTA: RESPONDE SOLO CON LA PALABRA CLAVE DE LA LISTA. SIN EXPLICACIONES, SIN PUNTOS, SIN COMILLAS Y EN MINÚSCULAS. 
    Si el cliente pide información muy ambigua, responde: desconocido
    """
    
    # ¡AQUÍ ESTÁ LA MAGIA! Apuntamos directo al modelo 3.8 que nos pidió la API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            respuesta_ia = data['candidates'][0]['content']['parts'][0]['text']
            return respuesta_ia.strip().lower()
        else:
            print(f"Error de la API de Gemini: {response.text}")
            return "desconocido"
            
    except Exception as e:
        print(f"Error de conexión con IA: {e}")
        return "desconocido"

# 4. Webhook Principal
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        challenge = request.GET.get('hub.challenge')
        return HttpResponse(challenge)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
            
            if 'messages' in value:
                mensaje = value['messages'][0]
                numero = mensaje['from']
                texto_crudo = mensaje['text']['body']
                
                print(f"\n--- NUEVA CONSULTA ---")
                print(f"1. Mensaje original: '{texto_crudo}'")
                
                # Pasamos por la IA
                palabra_clave = interpretar_mensaje_ia(texto_crudo)
                print(f"2. La IA lo clasificó como: '{palabra_clave}'")
                
                # Buscamos en Pandas
                ruta_csv = 'tarifario_bot.csv'
                if os.path.exists(ruta_csv) and palabra_clave != 'desconocido':
                    df = pd.read_csv(ruta_csv, sep=',', encoding='utf-8')
                    df.columns = df.columns.str.strip()
                    
                    coincidencias = df[df['Palabras_Clave'].str.lower().str.contains(palabra_clave, na=False)]
                    
                    if not coincidencias.empty:
                        respuesta_bot = "¡Hola! 👋 Aquí tienes los valores unitarios para tu consulta en PharmaCare:\n\n"
                        for _, row in coincidencias.iterrows():
                            tramite = row['Tramite']
                            precio = row['Precio_Total_UF']
                            rango = row['q_rango']
                            respuesta_bot += f"✅ *{tramite}*\n📦 Volumen: {rango} productos\n💰 Total: {precio} UF\n\n"
                        
                        enviar_mensaje(numero, respuesta_bot)
                        print("3. ¡Cotización enviada con éxito!")
                    else:
                        print("3. Sin coincidencias en el CSV para esa palabra.")
                else:
                    msj_error = "No estoy seguro de qué trámite necesitas. ¿Podrías detallar si es un producto cosmético, de higiene o una importación?"
                    enviar_mensaje(numero, msj_error)
                    print("3. Mensaje de error/ayuda enviado al cliente.")
                    
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Error procesando el webhook: {e}")
            return HttpResponse(status=500)