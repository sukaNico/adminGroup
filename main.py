import threading

import telebot
import json
import random
import time
from datetime import datetime


# Cargar o inicializar datos
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# Configura el bot con tu token
bot = telebot.TeleBot("7650156634:AAFUehxWRcRRx4mP3TsyfdaXD8y4fdw_vEM")  # Cambia esto a tu token
CHAT_ID = "-4542935245"

# Lista de frases para el regreso y respuesta AFK
frases_volver = [
    "¡He vuelto, amigos!",
    "¡Aquí estoy de nuevo!",
    "¡Me extrañaron!",
    "¡Regresé! ¿Qué me perdí?",
    "¡Estoy de vuelta, listo para la acción!"
]

frases_afk = [
    "Está ocupado corriendo el mundo.",
    "No puede responder ahora, está en su aventura.",
    "Está AFK, pero pronto regresará.",
    "No puede hablar, está en una misión secreta.",
    "Está ocupado salvando el día."
]


# Función para mencionar a todos solo con emojis
@bot.message_handler(commands=["llamada"])
def llamar_con_espacios_invisibles(message):
    data = load_data()
    mensaje_invisible = ""

    for user_id, info in data.items():
        # Crear un enlace invisible usando el espacio sin ancho
        mensaje_invisible += f"[\u200B](tg://user?id={user_id})"

    # Envía el mensaje invisible con todas las menciones
    if mensaje_invisible:
        bot.send_message(message.chat.id, "🗣️" + mensaje_invisible, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "No hay usuarios para mencionar.")

# Diccionario para almacenar los mensajes y sus intervalos
@bot.message_handler(func=lambda message: message.chat.type in ["group", "supergroup"])
def handle_message(message):
    print(message.chat.id)
    user_id = str(message.from_user.id)
    name = message.from_user.first_name  # Captura el username o nombre
    username = message.from_user.username
    timestamp = datetime.now().isoformat()

    # Cargar y actualizar datos
    data = load_data()

    if message.text.lower() == "brb":
        # Marcar como AFK y eliminar el mensaje
        if user_id in data:
            data[user_id]["AFK"] = True
        else:
            data[user_id] = {
                "nombre": name,
                "username": username,  # Guarda el username también
                "numeroMensajes": 0,
                "ultimaActividad": timestamp,
                "AFK": True
            }

        # Eliminar el mensaje
        bot.delete_message(message.chat.id, message.message_id)
        save_data(data)
    else:
        # Si el usuario estaba AFK, marcarlo como activo y notificar con una frase aleatoria
        if user_id in data and data[user_id]["AFK"]:
            data[user_id]["AFK"] = False
            frase = random.choice(frases_volver)
            bot.send_message(message.chat.id, f"{username} {frase}")

        # Verificar si el mensaje es una respuesta a alguien que está AFK
        if message.reply_to_message:
            replied_user_id = str(message.reply_to_message.from_user.id)
            if replied_user_id in data and data[replied_user_id]["AFK"]:
                frase_afk = random.choice(frases_afk)
                bot.send_message(message.chat.id, f"{frase_afk}")

        # Actualizar mensajes normales
        if user_id not in data:
            data[user_id] = {
                "nombre": name,
                "username": username,  # Guarda el username también
                "numeroMensajes": 0,
                "ultimaActividad": "",
                "AFK": False
            }

        data[user_id]["numeroMensajes"] += 1
        data[user_id]["ultimaActividad"] = timestamp
        data[user_id]["nombre"] = name
        data[user_id]["username"] = username

        # Guardar datos
        save_data(data)


# Ejecuta el bot
print("corriendo")
bot.polling(timeout=60, long_polling_timeout=30)
