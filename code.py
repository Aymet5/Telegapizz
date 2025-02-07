import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    CallbackContext, ConversationHandler, CallbackQueryHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен вашего бота (получите у BotFather в Telegram)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Состояния для ConversationHandler
MENU, CART, CHECKOUT, FEEDBACK = range(4)

# In-memory хранилище данных (замените на БД в реальном проекте)
menu = {
    'pizza_pepperoni': {'name': 'Пицца Пепперони', 'price': 550, 'description': 'Классика с пепперони и моцареллой'},
    'pizza_margarita': {'name': 'Пицца Маргарита', 'price': 450, 'description': 'Просто и вкусно: томаты, моцарелла, базилик'},
    'pizza_carbonara': {'name': 'Пицца Карбонара', 'price': 600, 'description': 'Бекон, сливки, пармезан, яйцо'},
    'cola': {'name': 'Coca-Cola', 'price': 100, 'description': 'Охлаждающий напиток'},
    'sprite': {'name': 'Sprite', 'price': 100, 'description': 'Освежающий лимонный напиток'},
    'fries': {'name': 'Картофель фри', 'price': 200, 'description': 'Хрустящий картофель фри'},
    'wings': {'name': 'Куриные крылышки', 'price': 350, 'description': 'Сочные куриные крылышки в соусе'}
}

user_carts = {}  # {user_id: {item_id: quantity}}

# --- Функции-обработчики ---
async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr"Привет, {user.mention_markdown_v2()}! Я бот пиццерии\. \n\n"
        "Я помогу тебе сделать заказ\. Используй /menu, чтобы увидеть наше меню\.",
    )

async def show_menu(update: Update, context: CallbackContext) -> int:
    """Показывает меню."""
    keyboard = []
    row = []
    for item_id, item in menu.items():
        row.append(KeyboardButton(text=item['name']))
        if len(row) == 2: #Две кнопки в строке
            keyboard.append(row)
            row = []
    if row: #Добавляем оставшиеся кнопки
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="Показать корзину")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Наше меню:", reply_markup=reply_markup)
    return MENU

async def add_to_cart(update: Update, context: CallbackContext) -> int:
    """Добавляет товар в корзину."""
    user_id = update.effective_user.id
    item_name = update.message.text
    item_id = None

    for key, value in menu.items():
        if value['name'] == item_name:
            item_id = key
            break

    if not item_id:
        await update.message.reply_text("Извините, такого товара нет в меню.")
        return MENU

    if user_id not in user_carts:
        user_carts[user_id] = {}

    if item_id in user_carts[user_id]:
        user_carts[user_id][item_id] += 1
    else:
        user_carts[user_id][item_id] = 1

    await update.message.reply_text(f"Добавлено в корзину: {menu[item_id]['name']}")
    return MENU

async def show_cart(update: Update, context: CallbackContext) -> int:
    """Показывает содержимое корзины."""
    user_id = update.effective_user.id

    if user_id not in user_carts or not user_carts[user_id]:
        await update.message.reply_text("Ваша корзина пуста.")
        return MENU

    cart_items = user_carts[user_id]
    total_price = 0
    cart_text = "Ваша корзина:\n"
    for item_id, quantity in cart_items.items():
        item = menu[item_id]
        item_price = item['price'] * quantity
        cart_text += f"- {item['name']} x {quantity} = {item_price} руб.\n"
        total_price += item_price

    cart_text += f"\nИтого: {total_price} руб."

    keyboard = [[KeyboardButton(text="Оформить заказ"), KeyboardButton(text="Продолжить покупки")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(cart_text, reply_markup=reply_markup)
    return CART

async def checkout(update: Update, context: CallbackContext) -> int:
    """Обработчик оформления заказа."""
    user_id = update.effective_user.id

    if user_id not in user_carts or not user_carts[user_id]:
        await update.message.reply_text("Ваша корзина пуста.")
        return MENU

    #Здесь можно добавить логику запроса адреса доставки и подтверждения заказа

    del user_carts[user_id]  # Очищаем корзину после оформления
    await update.message.reply_text("Спасибо за заказ!  Мы скоро свяжемся с вами для подтверждения.")
    return ConversationHandler.END  # Завершаем ConversationHandler

async def continue_shopping(update: Update, context: CallbackContext) -> int:
    """Возврат в меню из корзины."""
    await show_menu(update, context)
    return MENU

async def feedback(update: Update, context: CallbackContext) -> int:
    """Обработчик для обратной связи."""
    await update.message.reply_text("Пожалуйста, напишите ваш отзыв или предложение:")
    return FEEDBACK

async def process_feedback(update: Update, context: CallbackContext) -> int:
    """Сохраняет отзыв и завершает обработку."""
    user_feedback = update.message.text
    user = update.effective_user
    # Здесь можно добавить логику сохранения отзыва (например, в файл или БД)
    logging.info(f"Отзыв от пользователя {user.id} ({user.username}): {user_feedback}")
    await update.message.reply_text("Спасибо за ваш отзыв!")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Отменяет текущее действие."""
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

async def unknown(update: Update, context: CallbackContext):
    """Обработчик для неизвестных команд."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Извините, я не понимаю эту команду.")

# ---  Main  ---
def main() -> None:
    """Запуск бота."""
    application = ApplicationBuilder().token(TOKEN).build()

    # ConversationHandler для меню и корзины
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('menu', show_menu)],
        states={
            MENU: [MessageHandler(filters.Text(list(item['name'] for item in menu.values())), add_to_cart),
                   MessageHandler(filters.Text(["Показать корзину"]), show_cart)],
            CART: [MessageHandler(filters.Text(["Оформить заказ"]), checkout),
                   MessageHandler(filters.Text(["Продолжить покупки"]), continue_shopping)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_feedback)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('feedback', feedback))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown)) #Обработка неизвестных команд

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()