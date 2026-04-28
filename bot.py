# bot.py
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, ADMIN_ID

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"commands": {}, "responses": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Главное меню с кнопками
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    commands = data.get("commands", {})
    
    keyboard = []
    for i in range(1, 9):
        cmd_key = f"cmd{i}"
        if cmd_key in commands:
            keyboard.append([InlineKeyboardButton(commands[cmd_key], callback_data=cmd_key)])
    
    keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
    
    await update.message.reply_text(
        "🏢 *Добро пожаловать в MIDE WORK*\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    
    if query.data == "admin_panel":
        if user_id == ADMIN_ID:
            keyboard = [
                [InlineKeyboardButton("✏️ Изменить текст кнопки", callback_data="edit_btn")],
                [InlineKeyboardButton("📝 Изменить ответ кнопки", callback_data="edit_resp")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back")]
            ]
            await query.edit_message_text(
                "⚙️ *Админ-панель*\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("⛔ У вас нет доступа к админ-панели!")
        return
    
    elif query.data == "back":
        keyboard = []
        for i in range(1, 9):
            cmd_key = f"cmd{i}"
            if cmd_key in data["commands"]:
                keyboard.append([InlineKeyboardButton(data["commands"][cmd_key], callback_data=cmd_key)])
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
        await query.edit_message_text(
            "🏢 *MIDE WORK*\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif query.data == "edit_btn":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ Доступ запрещен")
            return
        keyboard = []
        for i in range(1, 9):
            cmd_key = f"cmd{i}"
            keyboard.append([InlineKeyboardButton(f"Кнопка {i}: {data['commands'].get(cmd_key, '???')}", callback_data=f"edit_btn_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
        await query.edit_message_text(
            "✏️ *Выберите кнопку для изменения текста:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif query.data == "edit_resp":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ Доступ запрещен")
            return
        keyboard = []
        for i in range(1, 9):
            cmd_key = f"cmd{i}"
            keyboard.append([InlineKeyboardButton(f"Ответ {i}: {data['responses'].get(cmd_key, '???')[:30]}...", callback_data=f"edit_resp_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
        await query.edit_message_text(
            "📝 *Выберите кнопку для изменения ответа:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif query.data.startswith("edit_btn_"):
        if user_id != ADMIN_ID:
            return
        btn_num = query.data.split("_")[2]
        context.user_data["edit_mode"] = f"btn_{btn_num}"
        await query.edit_message_text(
            f"✏️ Введите новый текст для КНОПКИ {btn_num}:\n(сейчас: {data['commands'].get(f'cmd{btn_num}', 'не задан')})",
            parse_mode="Markdown"
        )
        return
    
    elif query.data.startswith("edit_resp_"):
        if user_id != ADMIN_ID:
            return
        btn_num = query.data.split("_")[2]
        context.user_data["edit_mode"] = f"resp_{btn_num}"
        await query.edit_message_text(
            f"📝 Введите новый ОТВЕТ для кнопки {btn_num}:\n(сейчас: {data['responses'].get(f'cmd{btn_num}', 'не задан')})",
            parse_mode="Markdown"
        )
        return
    
    # Обычные команды
    response = data["responses"].get(query.data, "⚠️ Команда временно недоступна")
    btn_text = data["commands"].get(query.data, "")
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back")]]
    await query.edit_message_text(
        f"*{btn_text}*\n\n{response}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Обработка текста от админа (для редактирования)
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    if "edit_mode" in context.user_data:
        mode = context.user_data["edit_mode"]
        new_text = update.message.text
        data = load_data()
        
        if mode.startswith("btn_"):
            btn_num = mode.split("_")[1]
            data["commands"][f"cmd{btn_num}"] = new_text
            save_data(data)
            await update.message.reply_text(f"✅ Кнопка {btn_num} обновлена на: {new_text}")
        
        elif mode.startswith("resp_"):
            btn_num = mode.split("_")[1]
            data["responses"][f"cmd{btn_num}"] = new_text
            save_data(data)
            await update.message.reply_text(f"✅ Ответ для кнопки {btn_num} обновлен")
        
        del context.user_data["edit_mode"]
        
        # Показываем обновленное меню
        keyboard = []
        for i in range(1, 9):
            cmd_key = f"cmd{i}"
            if cmd_key in data["commands"]:
                keyboard.append([InlineKeyboardButton(data["commands"][cmd_key], callback_data=cmd_key)])
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
        await update.message.reply_text(
            "🏢 *Обновленное меню MIDE WORK*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# Старые команды /cmd1 ... /cmd8 для совместимости
async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_num: int):
    data = load_data()
    cmd_key = f"cmd{cmd_num}"
    response = data["responses"].get(cmd_key, "Команда не настроена")
    await update.message.reply_text(response)

async def cmd1(update, context): await cmd_handler(update, context, 1)
async def cmd2(update, context): await cmd_handler(update, context, 2)
async def cmd3(update, context): await cmd_handler(update, context, 3)
async def cmd4(update, context): await cmd_handler(update, context, 4)
async def cmd5(update, context): await cmd_handler(update, context, 5)
async def cmd6(update, context): await cmd_handler(update, context, 6)
async def cmd7(update, context): await cmd_handler(update, context, 7)
async def cmd8(update, context): await cmd_handler(update, context, 8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd1", cmd1))
    app.add_handler(CommandHandler("cmd2", cmd2))
    app.add_handler(CommandHandler("cmd3", cmd3))
    app.add_handler(CommandHandler("cmd4", cmd4))
    app.add_handler(CommandHandler("cmd5", cmd5))
    app.add_handler(CommandHandler("cmd6", cmd6))
    app.add_handler(CommandHandler("cmd7", cmd7))
    app.add_handler(CommandHandler("cmd8", cmd8))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("✅ Бот MIDE WORK запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
