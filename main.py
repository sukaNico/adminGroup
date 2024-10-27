import os
import threading

import telebot
import json
import random
import time
from threading import Thread
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


# Función que se ejecuta cada 10 minutos
def periodic_task():
    while True:
        time.sleep(600)
        print("sigo en pie")

def start_periodic_task():
    # Crear y comenzar un hilo para la tarea periódica
    thread = threading.Thread(target=periodic_task)
    thread.daemon = True  # Permite que el hilo se cierre al terminar el programa
    thread.start()

# Configura el bot con tu token
bot = telebot.TeleBot("7650156634:AAFUehxWRcRRx4mP3TsyfdaXD8y4fdw_vEM")  # Cambia esto a tu token

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


@bot.message_handler(commands=["help"])
def send_help(message):
    help_text = (
        "👋 *¡Hola! Aquí están los comandos que puedes usar:*\n\n"
        "🔹 *Estado AFK*\n"
        "`/afk` - Marca tu estado como 'AFK' (Ausente), avisando a los demás cuando te mencionen.\n\n"
        "🔹 *Menciones Grupales*\n"
        "`/llamada` - Menciona a todos los usuarios del grupo de forma discreta.\n\n"
        "🔹 *Mensajes Programados*\n\n"
        "`/programar_mensaje <mensaje>,<intervalo>` - Programa un mensaje para enviarse cada cierto tiempo.\n"
        "*Ejemplo:* `/programar_mensaje Hola a todos,60` \n(envía 'Hola a todos' cada 60 segundos).\n\n"
        "`/mensajes_programados`\n- Muestra una lista de todos tus mensajes programados y sus intervalos.\n\n"
        "`/cancelar_mensaje_programado <ID>`\n- Cancela un mensaje programado usando su ID.\n"
        "*Ejemplo:* `/cancelar_mensaje_programado 1`\n\n"

        "💡 *Si tienes alguna duda, aquí estoy para ayudarte! 😊*"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

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
scheduled_messages = {}


# Función para enviar mensajes periódicos
def send_periodic_message(chat_id, message_id, message, interval):
    while chat_id in scheduled_messages and message_id in scheduled_messages[
        chat_id]:  # Verifica que el mensaje siga programado
        bot.send_message(chat_id, message)
        time.sleep(interval)


# Comando para configurar un mensaje y su intervalo
@bot.message_handler(commands=['programar_mensaje'])
def set_scheduled_message(message):
    try:
        # Se espera el formato: /programar mensaje | tiempo_en_segundos
        user_input = message.text.split(" ", 1)[1]
        msg_text, interval = user_input.split(",")
        interval = int(interval.strip())
        msg_text = msg_text.strip()

        chat_id = message.chat.id
        if chat_id not in scheduled_messages:
            scheduled_messages[chat_id] = {}

        # Crear un ID único para el mensaje programado
        message_id = len(scheduled_messages[chat_id]) + 1
        scheduled_messages[chat_id][message_id] = {'message': msg_text, 'interval': interval}
        # Crear un nuevo hilo para enviar el mensaje periódicamente
        thread = Thread(target=send_periodic_message, args=(chat_id, message_id, msg_text, interval))
        thread.daemon = True  # Permite que el hilo se cierre al terminar el programa
        thread.start()
        bot.delete_message(message.chat.id, message.message_id)  # Opcional: Eliminar el mensaje de /afk

    except Exception as e:
        bot.reply_to(message, "Formato incorrecto. Usa: /programar mensaje | tiempo_en_segundos")


# Comando para ver los mensajes programados
@bot.message_handler(commands=['mensajes_programados'])
def view_scheduled_messages(message):
    chat_id = message.chat.id
    if chat_id in scheduled_messages and scheduled_messages[chat_id]:
        msg_list = "\n".join(
            [f"ID {msg_id}: '{details['message']}' cada {details['interval']} segundos"
             for msg_id, details in scheduled_messages[chat_id].items()]
        )
        bot.reply_to(message, f"Tus mensajes programados:\n{msg_list}")
    else:
        bot.reply_to(message, "No tienes mensajes programados.")


# Comando para cancelar un mensaje programado específico por ID
@bot.message_handler(commands=['cancelar_mensaje_programado'])
def cancel_scheduled_message(message):
    try:
        chat_id = message.chat.id
        message_id = int(message.text.split(" ")[1])  # Extrae el ID del mensaje a cancelar
        if chat_id in scheduled_messages and message_id in scheduled_messages[chat_id]:
            del scheduled_messages[chat_id][message_id]
            bot.delete_message(message.chat.id, message.message_id)  # Opcional: Eliminar el mensaje de /afk
        else:
            bot.reply_to(message, "No tienes un mensaje programado con ese ID.")

    except IndexError:
        bot.reply_to(message, "Debes proporcionar el ID del mensaje a cancelar. Ejemplo: /cancelar_programado 1")
    except ValueError:
        bot.reply_to(message, "Formato incorrecto. El ID debe ser un número.")


# Función para manejar el registro de mensajes y verificar estado AFK
@bot.message_handler(commands=["afk"])
def set_afk_status(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    name = message.from_user.first_name
    timestamp = datetime.now().isoformat()

    # Cargar y actualizar datos
    data = load_data()

    # Marcar al usuario como AFK
    if user_id in data:
        data[user_id]["AFK"] = True
    else:
        data[user_id] = {
            "nombre": name,
            "username": username,
            "numeroMensajes": 0,
            "ultimaActividad": timestamp,
            "AFK": True
        }

    # Guardar el estado AFK en el archivo
    save_data(data)

    # Confirmación para el usuario
    bot.delete_message(message.chat.id, message.message_id)  # Opcional: Eliminar el mensaje de /afk


# Función para manejar el registro de mensajes y verificar estado AFK
@bot.message_handler(func=lambda message: message.chat.type in ["group", "supergroup"])
def handle_message(message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name
    username = message.from_user.username
    timestamp = datetime.now().isoformat()

    # Cargar datos de usuario
    data = load_data()

    # Si el usuario estaba AFK, marcarlo como activo y enviar mensaje de vuelta
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

    # Actualizar datos del usuario en el registro de actividad
    if user_id not in data:
        data[user_id] = {
            "nombre": name,
            "username": username,
            "numeroMensajes": 0,
            "ultimaActividad": "",
            "AFK": False
        }

    data[user_id]["numeroMensajes"] += 1
    data[user_id]["ultimaActividad"] = timestamp
    data[user_id]["nombre"] = name
    data[user_id]["username"] = username

    # Guardar datos actualizados
    save_data(data)



# Ejecuta el bot
print("corriendo")
commands = [
    telebot.types.BotCommand("programar_mensaje", "Programar un mensaje periódico"),
    telebot.types.BotCommand("mensajes_programados", "Ver todos los mensajes programados"),
    telebot.types.BotCommand("cancelar_mensaje_programado", "Cancelar un mensaje programado por ID"),
    telebot.types.BotCommand("llamada", "Mencionar a todos los usuarios"),
]

# Establecer los comandos de autocompletado
bot.set_my_commands(commands)
print("corriendo")
start_periodic_task()
port = int(os.environ.get("PORT", 5000))
bot.polling(timeout=60, long_polling_timeout=30)
