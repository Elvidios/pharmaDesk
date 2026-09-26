import os
import json
import pandas as pd
import requests
from dotenv import load_dotenv
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


def obtener_valor_uf():
    try:
        # mindicador.cl no requiere API Key y es muy rápida
        url = "https://mindicador.cl/api/uf"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            # Extraemos el valor del día (el primer elemento de la serie)
            valor_uf = float(data['serie'][0]['valor'])
            print(f"Valor UF de hoy obtenido: ${valor_uf}")
            return valor_uf
        else:
            print("Fallo en API de mindicador, usando UF de respaldo.")
            return 38500.0 # Valor de respaldo
            
    except Exception as e:
        print(f"Error conectando a mindicador: {e}")
        return 38500.0 # Valor de emergencia para salvar la demo

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

import json

def interpretar_mensaje_ia(texto_cliente):
    api_key = os.getenv('GEMINI_API_KEY').strip()
    
    prompt = f"""
    Eres el asistente de Triage (filtro inicial) de PharmaCare.
    Tu objetivo es obtener la información mínima para armar una cotización farmacéutica.
    
    Analiza este mensaje: "{texto_cliente}"
    
    Información obligatoria que necesitamos deducir:
    1. Categoría: Solo puede ser: higiene, cosmetico, cda, validacion, o transferencia.
    2. Trámite: Qué quiere hacer (ej. registro, importar, patentar, vender).
    
    EVALUACIÓN:
    - Si el mensaje es muy ambiguo (ej. "hola", "quiero cotizar", "necesito ayuda") o no logras deducir la Categoría, el estado es "incompleto".
    - Si está incompleto, redacta una "pregunta_seguimiento" corta, amable y directa, dando ejemplos de lo que haces. (Ej: "¡Hola! Para ayudarte a cotizar, ¿podrías detallarme si buscas registrar un producto cosmético, de higiene, o hacer una importación? ¿Y de cuántos productos estamos hablando?").
    - Si logras deducir la Categoría y el Trámite, el estado es "completo" y asume cantidad 1 si no la mencionan.
    
    Devuelve ESTRICTAMENTE este JSON y nada más:
    {{
        "estado": "completo o incompleto",
        "categoria": "higiene",
        "tramite": "registro",
        "cantidad": 1,
        "pregunta_seguimiento": "Tu pregunta amigable aquí (déjalo vacío si está completo)"
    }}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            data = response.json()
            respuesta_texto = data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if respuesta_texto.startswith('```'):
                respuesta_texto = respuesta_texto.replace('```json', '').replace('```', '').strip()
                
            return json.loads(respuesta_texto)
        else:
            return {"estado": "incompleto", "pregunta_seguimiento": "Hubo un error de conexión. ¿Podrías repetirme tu solicitud de forma más detallada?", "categoria": "desconocido"}
            
    except Exception as e:
        print(f"Error procesando la IA: {e}")
        return {"estado": "incompleto", "pregunta_seguimiento": "No pude procesar eso. ¿Podrías indicarme si es un producto cosmético o de higiene?", "categoria": "desconocido"}

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
                
                # 1. Pasamos por el Triage de IA
                datos_ia = interpretar_mensaje_ia(texto_crudo)
                print(f"2. Análisis de IA: {datos_ia}")
                
                # 2. EVALUACIÓN DE TRIAGE
                if datos_ia.get('estado') == 'incompleto':
                    # La IA detectó que faltan datos. Extrae la pregunta amable y la envía.
                    pregunta = datos_ia.get('pregunta_seguimiento', 'No estoy seguro de qué necesitas. ¿Podrías detallar más?')
                    enviar_mensaje(numero, pregunta)
                    print("3. Triage Activo: Solicitando más datos al cliente.")
                    
                    # CORTAMOS LA EJECUCIÓN AQUÍ. No avanzamos a Pandas.
                    return HttpResponse(status=200) 
                
# 3. SI ESTÁ COMPLETO, CONTINUAMOS AL CÁLCULO
            palabra_clave = datos_ia.get('categoria', 'desconocido')
            tramite_solicitado = datos_ia.get('tramite', 'tu solicitud')
            
            # Aseguramos que la cantidad sea un número entero
            try:
                cantidad_solicitada = int(datos_ia.get('cantidad', 1))
            except:
                cantidad_solicitada = 1
            
            # Obtenemos la UF del día ANTES de entrar al CSV
            valor_uf_hoy = obtener_valor_uf()
            
            # Buscamos en Pandas
            ruta_csv = 'tarifario_bot.csv'
            if os.path.exists(ruta_csv) and palabra_clave != 'desconocido':
                df = pd.read_csv(ruta_csv, sep=',', encoding='utf-8')
                df.columns = df.columns.str.strip()
                
                coincidencias = df[df['Palabras_Clave'].str.lower().str.contains(palabra_clave, na=False)]
                
                if not coincidencias.empty:
                    respuesta_bot = f"¡Perfecto! Para {cantidad_solicitada}x *{tramite_solicitado}* de la categoría *{palabra_clave}*:\n\n"
                    
                    for _, row in coincidencias.iterrows():
                        tramite_csv = row['Tramite']
                        precio_uf_unitario = float(row['Precio_Total_UF'])
                        rango = row['q_rango']
                        
                        # MATEMÁTICA: UF unitaria * Cantidad solicitada * Valor de la UF hoy
                        total_uf = precio_uf_unitario * cantidad_solicitada
                        total_clp = int(total_uf * valor_uf_hoy)
                        
                        # Formateamos los pesos chilenos con puntos (ej. $1.500.000)
                        formato_clp = f"${total_clp:,.0f}".replace(',', '.')
                        
                        respuesta_bot += f"✅ *{tramite_csv}*\n📦 Escala: {rango}\n💎 Subtotal: {total_uf} UF\n💰 Total Estimado: {formato_clp} CLP\n\n"
                    
                    enviar_mensaje(numero, respuesta_bot)
                    print("3. ¡Cotización en CLP enviada con éxito!")
                else:
                    print("3. Sin coincidencias en el CSV para esa palabra.")
                    enviar_mensaje(numero, "Entendí tu solicitud, pero no encontré tarifas exactas para esa categoría.")
                    
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Error procesando el webhook: {e}")
            return HttpResponse(status=500)