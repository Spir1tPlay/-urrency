import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from cfg import TOKEN

# Бесплатный API для курсов валют
RATES_URL = "https://api.exchangerate-api.com/v4/latest/USD"

bot = telebot.TeleBot(TOKEN)


def get_rates():
    response = requests.get(RATES_URL)
    return response.json()["rates"]


def convert(amount, from_currency, to_currency, rates):
    """Конвертируем любую валюту в любую через USD как базу"""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency not in rates:
        return None, f"Не знаю валюту: {from_currency}"
    if to_currency not in rates:
        return None, f"Не знаю валюту: {to_currency}"

    # Переводим: from_currency -> USD -> to_currency
    amount_in_usd = amount / rates[from_currency]
    result = amount_in_usd * rates[to_currency]

    return result, None


def parse_convert(text):
    """
    Разбираем текст вида "100 USD в KZT" или "100 USD KZT"
    Возвращаем (amount, from_currency, to_currency) или None если не распознали
    """
    # Убираем лишние пробелы и переводим в верхний регистр
    text = text.strip()

    # Заменяем слова-разделители на пробел
    for word in ["в", "to", "->", "="]:
        text = text.replace(word, " ")

    # Разбиваем по пробелам и убираем пустые части
    parts = [p for p in text.split() if p]

    # Ожидаем минимум 3 части: число, валюта_откуда, валюта_куда
    if len(parts) < 3:
        return None

    # Пробуем получить число из первой части
    try:
        amount = float(parts[0].replace(",", "."))
    except ValueError:
        return None

    from_currency = parts[1].upper()
    to_currency = parts[-1].upper()  # берём последнее слово

    return amount, from_currency, to_currency


def main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🇺🇸 USD → KZT", callback_data="conv_100_USD_KZT"),
        InlineKeyboardButton("🇪🇺 EUR → KZT", callback_data="conv_100_EUR_KZT"),
    )
    keyboard.row(
        InlineKeyboardButton("🇷🇺 RUB → KZT", callback_data="conv_100_RUB_KZT"),
        InlineKeyboardButton("🇺🇸 KZT → USD", callback_data="conv_1000_KZT_USD"),
    )
    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "👋 Привет! Я конвертер валют.\n\n"
        "Напиши например:\n"
        "  100 USD в KZT\n"
        "  50 EUR в RUB\n"
        "  5000 KZT to USD\n\n"
        "Или нажми кнопку быстрого перевода:"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith("conv_"))
def handle_button(call):
    # callback_data вида "conv_100_USD_KZT"
    parts = call.data.split("_")
    amount = float(parts[1])
    from_curr = parts[2]
    to_curr = parts[3]

    try:
        rates = get_rates()
        result, error = convert(amount, from_curr, to_curr, rates)
        if error:
            answer = f"❌ {error}"
        else:
            answer = f"💱 {amount:g} {from_curr} = {result:.2f} {to_curr}"
    except Exception:
        answer = "⚠️ Не удалось получить данные."

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=answer,
        reply_markup=main_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.strip()
    parsed = parse_convert(text)

    if parsed is None:
        bot.send_message(
            message.chat.id,
            "🤔 Не понял. Попробуй написать так:\n100 USD в KZT",
            reply_markup=main_keyboard()
        )
        return

    amount, from_curr, to_curr = parsed

    try:
        rates = get_rates()
        result, error = convert(amount, from_curr, to_curr, rates)

        if error:
            answer = f"❌ {error}"
        else:
            answer = f"💱 {amount:g} {from_curr} = {result:.2f} {to_curr}"

    except Exception:
        answer = "⚠️ Не удалось получить данные. Попробуй позже."

    bot.send_message(message.chat.id, answer, reply_markup=main_keyboard())


print("Бот запущен")
bot.polling()