import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

TOKEN = '8488722647:AAG63wQERK5ZSRoZONxUvq9uU9GXU--KNxI'
ADMIN_ID = 8001717196

bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📩 Разместить объявление")
    bot.send_message(message.chat.id, "Привет! Я бот для подачи объявлений.\nНажми кнопку ниже, чтобы разместить своё.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📩 Разместить объявление")
def request_ad_text(message):
    user_data[message.chat.id] = {'photos': []}
    bot.send_message(message.chat.id, "✏️ Напишите текст объявления (что сдаётся/продаётся, цена, район):")

@bot.message_handler(func=lambda m: m.chat.id in user_data and 'text' not in user_data[m.chat.id])
def save_text(message):
    user_data[message.chat.id]['text'] = message.text
    bot.send_message(message.chat.id, "📞 Теперь пришлите ваш контакт (номер телефона или @username):")

@bot.message_handler(func=lambda m: m.chat.id in user_data and 'contact' not in user_data[m.chat.id])
def save_contact(message):
    user_data[message.chat.id]['contact'] = message.text
    bot.send_message(message.chat.id, "📷 Пожалуйста, отправьте до 3 фото квартиры. После отправки напишите 'Готово'.")

@bot.message_handler(content_types=['photo'])
def collect_photos(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id)
    if not data or len(data['photos']) >= 3:
        bot.send_message(chat_id, "❗Вы уже отправили 3 фото. Напишите 'Готово'.")
        return
    data['photos'].append(message.photo[-1].file_id)
    bot.send_message(chat_id, f"✅ Фото {len(data['photos'])} получено. Отправьте ещё или напишите 'Готово'.")

@bot.message_handler(func=lambda m: m.text.lower() == 'готово')
def confirm_preview(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id)
    if not data or not data['photos']:
        bot.send_message(chat_id, "❗Сначала отправьте хотя бы 1 фото.")
        return

    text = f"📄 Объявление:\n{data['text']}\n\n📞 Контакт: {data['contact']}"
    media = []

    for idx, photo_id in enumerate(data['photos']):
        if idx == 0:
            media.append(InputMediaPhoto(photo_id, caption=text))
        else:
            media.append(InputMediaPhoto(photo_id))

    bot.send_media_group(chat_id, media)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    bot.send_message(chat_id, "Опубликовать объявление?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['confirm', 'cancel'])
def handle_decision(call):
    chat_id = call.message.chat.id
    data = user_data.get(chat_id)

    if call.data == 'cancel':
        bot.send_message(chat_id, "❌ Объявление отменено.")
        user_data.pop(chat_id, None)
        return

    if not data:
        bot.send_message(chat_id, "⚠️ Что-то пошло не так. Начните заново: /start")
        return

    caption = f"🆕 Новая заявка!\n\n📄 Объявление:\n{data['text']}\n\n📞 Контакт: {data['contact']}\n👤 От @{call.from_user.username or 'без username'}"
    media = []

    for i, file_id in enumerate(data['photos']):
        if i == 0:
            media.append(InputMediaPhoto(file_id, caption=caption))
        else:
            media.append(InputMediaPhoto(file_id))

    bot.send_media_group(ADMIN_ID, media)
    bot.send_message(chat_id, "✅ Спасибо! Объявление отправлено на модерацию.")
    user_data.pop(chat_id, None)

bot.polling()
