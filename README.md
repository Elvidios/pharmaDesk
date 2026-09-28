PharmaCare SmartDesk - Cotizador B2B con IA
====================================================

Sistema automatizado de cotizaciones B2B para la industria farmacéutica. Utiliza procesamiento de lenguaje natural (Google Gemini) para interpretar solicitudes inestructuradas por WhatsApp, calcula los costos en tiempo real y permite la revisión y edición humana mediante un panel web antes de enviar la propuesta final al cliente.

REQUISITOS PREVIOS
----------------------------------------------------
Para ejecutar este proyecto localmente, necesitas las siguientes herramientas, librerías y cuentas de terceros:

1. Software y Librerías
- Python 3.10+: Lenguaje principal del backend.
- Ngrok: Herramienta de túneles HTTP para exponer el servidor local a internet y poder recibir los Webhooks de Meta.
- Librerías de Python: 
  * django (Framework Web y ORM)
  * pandas (Procesamiento de datos del tarifario)
  * requests (Comunicación HTTP con las APIs externas)
  * python-dotenv (Manejo seguro de credenciales)

2. Cuentas y Accesos API
- Cuenta de Google AI Studio: Para generar la GEMINI_API_KEY (utiliza el modelo gemini-1.5-flash-latest o gemini-flash-latest).
- Cuenta de Meta for Developers: Crear una App configurada con la API de WhatsApp Business en modo Sandbox (para obtener el Token de acceso temporal y el número de pruebas).


INSTALACIÓN Y CONFIGURACIÓN
----------------------------------------------------
Paso 1: Clonar el repositorio e instalar dependencias
Abre tu terminal y ejecuta los siguientes comandos:

# 1. Crear un entorno virtual
python -m venv env

# 2. Activar el entorno virtual
# En Linux/Mac:
source env/bin/activate
# En Windows:
# env\Scripts\activate

# 3. Instalar los requerimientos del proyecto
pip install django pandas requests python-dotenv

Paso 2: Configuración de Variables de Entorno
Crea un archivo llamado .env en la raíz de tu proyecto (al mismo nivel que el archivo manage.py) y agrega tus credenciales. Nunca subas este archivo a GitHub.

GEMINI_API_KEY=tu_api_key_de_google_aqui
WHATSAPP_TOKEN=tu_token_temporal_de_meta_aqui
WHATSAPP_VERIFY_TOKEN=un_token_inventado_por_ti_para_verificar_el_webhook

Paso 3: Configurar Base de Datos y Tarifario
- Asegúrate de que el archivo tarifario_bot.csv esté en la raíz del proyecto. Este archivo es el corazón del motor de cálculo que lee Pandas.
- Prepara la base de datos de Django ejecutando:

python manage.py makemigrations
python manage.py migrate


EJECUCIÓN DEL PROYECTO
----------------------------------------------------
Para que el flujo End-to-End funcione, debes ejecutar dos procesos en terminales separadas.

Terminal 1: Iniciar el Túnel Ngrok
Inicia Ngrok para exponer el puerto 8000 de Django a internet:

ngrok http 8000

Atención: Copia la URL segura (HTTPS) que genera Ngrok. Debes ir a tu panel de Meta for Developers > WhatsApp > Configuración y pegar esta URL en la sección de Webhooks, añadiendo la ruta de tu API (ej: https://abcd-123.ngrok-free.app/api/whatsapp/webhook/). Usa el WHATSAPP_VERIFY_TOKEN de tu archivo .env para verificar.

Terminal 2: Iniciar el Servidor Django
Con el entorno virtual activado, levanta el backend:

python manage.py runserver


GUÍA DE USO (Flujo Human-in-the-Loop)
----------------------------------------------------
1. Interacción del Cliente (WhatsApp): El usuario envía un mensaje de texto libre al número de pruebas de Meta (ej. "Hola, necesito registrar 3 labiales").
2. Triage por IA: El Webhook de Django recibe el mensaje y lo procesa con Gemini. Si la IA detecta que faltan datos, formula una pregunta de seguimiento automáticamente. Si los datos están completos, detiene la interacción y avisa al cliente que su solicitud está "en análisis".
3. Cálculo de Cotización: Pandas cruza las entidades detectadas por la IA con el archivo CSV, calculando el precio basado en la UF y guardando un borrador en la base de datos (Modelo Ticket).
4. Gestión del Especialista (Dashboard): El equipo humano ingresa al panel de control web desde el navegador (http://127.0.0.1:8000/).
5. Edición y Cierre: El especialista abre el ticket pendiente, revisa el borrador generado, lo edita en la caja de texto si requiere ajustes finos, y presiona "Aprobar y Enviar".
6. Despacho Automatizado: Django utiliza una petición AJAX para enviar la versión final validada al WhatsApp del cliente, cerrando el ciclo comercial con cero margen de error.
