from flask import Flask, request, jsonify
import requests
import os
import time
import openai
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()

# Claves de autenticación
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Token de OpenAI
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")  # Token de acceso de WhatsApp
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")  # ID del número de WhatsApp

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

# Configuración inicial del bot
bot_activo = True  # Lo dejamos activo por defecto
delay_respuesta = 5  # Delay entre mensaje de texto e imagen

# Configuración del AI Agent
ai_config = {
    "prompt": "Eres una asistente mujer buena onda, joven y contestas con palabras modernas de jóvenes. Eres experta en atención a clientes para joyería y estambre. Solo vendes 2 estambres llamados Angel y Brisa" ,
    "role": "Asistente de Ventas",
    "temperature": 0.7,
    "max_tokens": 100
}

# Iniciar Flask
app = Flask(__name__)

# Función para enviar mensajes de WhatsApp
def enviar_mensaje(numero, texto, imagen_url=None):
    # 📌 Corregir el número si es de México y tiene el "1" extra
    if numero.startswith("521"):
        numero = "52" + numero[3:]

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_KEY}",
        "Content-Type": "application/json"
    }

    data_texto = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    print(f"📤 Enviando mensaje a {numero}: {texto}")  # 🔍 Debugging

    response_texto = requests.post(url, headers=headers, json=data_texto)
    print(f"📩 Respuesta API WhatsApp (Texto): {response_texto.json()}")  # 🔍 Ver si hubo error


# Función para obtener la respuesta del AI de OpenAI
def responder_mensaje(mensaje):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": ai_config["prompt"]},
            {"role": "user", "content": mensaje}
        ],
        temperature=ai_config["temperature"],
        max_tokens=ai_config["max_tokens"]
    )
    return response["choices"][0]["message"]["content"]

# Endpoint para activar el bot
@app.route("/activar", methods=["POST"])
def activar_bot():
    global bot_activo
    bot_activo = True
    return jsonify({"status": "Bot activado"}), 200

# Endpoint para apagar el bot
@app.route("/apagar", methods=["POST"])
def apagar_bot():
    global bot_activo
    bot_activo = False
    return jsonify({"status": "Bot apagado"}), 200

# 📌 **Nuevo Endpoint: Webhook de WhatsApp**
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verificación del Webhook en Meta
        verify_token = "whatsapp_bot_123"
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            print("WEBHOOK VERIFICADO CORRECTAMENTE")
            return challenge, 200
        else:
            return "Error en la verificación", 403

    # 📌 Procesar mensajes entrantes
    data = request.json
    print("Mensaje recibido (JSON completo):", data)  # 🔍 Depuración

    # Extraer información del mensaje
    if "entry" in data:
        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" in change["value"]:
                    mensaje_data = change["value"]["messages"][0]
                    numero = mensaje_data["from"]  # Número del remitente

                    if "text" in mensaje_data:
                        texto = mensaje_data["text"]["body"]
                        print(f"Mensaje recibido de {numero}: {texto}")  # 🔍 Debugging

                        # Obtener respuesta del AI
                        respuesta_ai = responder_mensaje(texto)

                        # Enviar respuesta por WhatsApp
                        enviar_mensaje(numero, respuesta_ai)
                    else:
                        print("⚠️ No se encontró texto en el mensaje recibido.")

    return jsonify({"status": "Mensaje procesado"}), 200

# Inicia el servidor en el puerto 5000
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
