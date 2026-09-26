import json
import os
import pandas as pd
import requests
import google.generativeai as genai
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv


load_dotenv()


# Configuración de la IA (Saca tu API Key gratuita en Google AI Studio)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def interpretar_mensaje_ia(texto_cliente):
    """
    Toma el texto desordenado del cliente y lo obliga a encajar 
    en una de nuestras palabras clave del CSV.
    """
    prompt = f"""
    Eres el clasificador de intenciones de PharmaCare. 
    Analiza este mensaje de un cliente: "{texto_cliente}"
    
    Clasifícalo en UNA de las siguientes categorías estrictas:
    - cosmetico (si hablan de cremas, maquillaje, cosmética, lociones)
    - higiene (si hablan de jabón, limpieza, cepillos, higiene bucal)
    - cda (si hablan de importar, aduana, internación, CDA)
    - validacion (si hablan de calidad, eximición, origen)
    - transferencia (si hablan de cambiar titularidad de registro)
    
    Regla estricta: Responde ÚNICAMENTE con la palabra clave elegida, en minúsculas y sin puntos. Si no logras clasificarlo, responde 'desconocido'.
    """
    try:
        # Usamos el modelo más rápido
        model = genai.GenerativeModel('gemini-1.5-flash')
        respuesta = model.generate_content(prompt)
        return respuesta.text.strip().lower()
    except Exception as e:
        print(f"Error en IA: {e}")
        return "desconocido"
    
# --- CONFIGURACIÓN META ---
# Pega aquí los datos de tu panel de Meta for Developers
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

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
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

@csrf_exempt
def whatsapp_webhook(request):
    # Verificación de Webhook (Meta te pide esto al configurar)
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
                texto_cliente = mensaje['text']['body'].lower()
                
                print(f"\nBuscando cotización para: '{texto_cliente}'...")
                
                ruta_csv = 'tarifario_bot.csv'
                if os.path.exists(ruta_csv):
                    # engine='python' y sep=None hace que Pandas detecte si es coma o punto y coma automáticamente
                    # encoding='utf-8-sig' elimina cualquier caracter invisible al inicio del archivo
                    df = pd.read_csv(ruta_csv, sep=None, engine='python', encoding='utf-8-sig')
                    
                    # Limpiamos los espacios
                    df.columns = df.columns.str.strip()

                    if 'Palabras_Clave' in df.columns:
                        coincidencias = df[df['Palabras_Clave'].str.lower().str.contains(texto_cliente, na=False)]
                    

                        if not coincidencias.empty:
                            respuesta_bot = "¡Hola! 👋 Aquí tienes los valores unitarios para tu consulta en PharmaCare:\n\n"
                            for _, row in coincidencias.iterrows():
                                tramite = row['Tramite']
                                precio = row['Precio_Total_UF']
                                rango = row['q_rango']
                                respuesta_bot += f"✅ *{tramite}*\n📦 Volumen: {rango} productos\n💰 Total: {precio} UF\n\n"
                            
                            enviar_mensaje(numero, respuesta_bot)
                            print("Respuesta generada y enviada con éxito.")
                            print("\nMENSAJE A ENVIAR:\n" + respuesta_bot)
                        else:
                            msj_error = "No encontré trámites exactos con esa palabra. ¿Podrías detallar un poco más si es cosmético, higiene o importación?"
                            enviar_mensaje(numero, msj_error)
                            print("Sin coincidencias en el CSV.")
                    else:
                        print("❌ ERROR GRAVE: La columna 'Palabras_Clave' no existe. El archivo está mal delimitado.")
                else:
                    print(f"Error crítico: No se encontró la base de datos {ruta_csv}")
                    
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Error procesando el webhook: {e}")
            return HttpResponse(status=500)