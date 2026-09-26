import requests
import json
import time

url = 'http://127.0.0.1:8000/api/whatsapp/webhook/'

print("=========================================")
print("🟢 SIMULADOR PHARMACARE BOT (MODO DEMO)")
print("Escribe 'salir' para terminar la prueba")
print("=========================================\n")

while True:
    texto_usuario = input("📱 Cliente (escribe tu consulta): ")
    
    if texto_usuario.lower() == 'salir':
        print("Cerrando simulador...")
        break
        
    payload = {
      "object": "whatsapp_business_account",
      "entry": [{
          "changes": [{
              "value": {
                "messages": [{
                    "from": "56989998344",
                    "text": {"body": texto_usuario}
                }]
              }
          }]
      }]
    }

    try:
        # Simulamos el envío a Django
        requests.post(url, json=payload)
        
        # Pausa de 1 segundo para dar la sensación de que el bot "está escribiendo"
        time.sleep(1)
        print("✅ Petición procesada por Django (revisa la otra terminal para ver el mensaje de salida)\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: El servidor Django no está corriendo.\n")