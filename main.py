import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

# --- KONFIGURASI (Mengambil dari Railway Environment Variables) ---
TOKEN = os.getenv('8370842756:AAEbjHtrnZNPnduqGNl-mTyuVmE8iuNB4fE')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7655136272'))
GROUP_CHAT_ID = int(os.getenv('GROUP_ID', '-1003649901491'))
YT_LINK = os.getenv('YT_LINK', 'https://www.youtube.com/channel/UCePnGN0-MkIt_dNjm1viwug')

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- KEYBOARD MENU ---
def get_main_menu():
    keyboard = [[KeyboardButton("📝 Registrasi"), KeyboardButton("❓ Bantuan")],
                [KeyboardButton("📊 Status Permintaan")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_upload_menu():
    keyboard = [[KeyboardButton("📸 Kirim Bukti Subscribe"), KeyboardButton("📸 Kirim Bukti Like")],
                [KeyboardButton("❌ Batal Registrasi")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, placeholder="Kirim 2 Foto Screenshot...")

def get_link_menu():
    keyboard = [[KeyboardButton("🔗 Request Link")], [KeyboardButton("🔙 Kembali ke Menu Utama")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- FUNGSI GENERATE LINK ---
async def generate_unique_link(context: ContextTypes.DEFAULT_TYPE, user_name):
    try:
        new_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_CHAT_ID, name=f"Link {user_name}", creates_join_request=True
        )
        return new_link.invite_link
    except Exception as e:
        logging.error(f"Error link: {e}")
        return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    context.user_data.clear()
    await update.message.reply_text(
        f"Halo <b>{user_name}</b>! 👋\nSilakan pilih menu <b>📝 Registrasi</b>.",
        reply_markup=get_main_menu(), parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    u_id = update.effective_user.id

    if text == "📝 Registrasi":
        context.user_data.update({'proof_count': 0, 'status': 'uploading_proofs'})
        await update.message.reply_text(
            f"🔒 <b>MODE REGISTRASI</b>\n\nSilakan <b>Subscribe & Like</b>:\n{YT_LINK}\n\n"
            "📸 Kirimkan 2 Screenshot bukti sekarang.",
            reply_markup=get_upload_menu(), parse_mode='HTML'
        )
    elif text in ["❌ Batal Registrasi", "🔙 Kembali ke Menu Utama"]:
        context.user_data.clear()
        await update.message.reply_text("Kembali ke Menu Utama:", reply_markup=get_main_menu())
    elif text == "🔗 Request Link":
        if context.user_data.get('proof_completed'):
            link = await generate_unique_link(context, update.effective_user.first_name)
            if link:
                await update.message.reply_text(f"✅ <b>Link Akses:</b>\n{link}\n\nKlik dan pilih 'Request to Join'.", parse_mode='HTML')
        else:
            await update.message.reply_text("⛔ Selesaikan bukti dulu!")
    elif text == "📊 Status Permintaan":
        status = "⏳ Menunggu Admin" if f"pending_{u_id}" in context.bot_data else "❌ Tidak ada permintaan aktif."
        await update.message.reply_text(f"Status: <b>{status}</b>", parse_mode='HTML')

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('status') != 'uploading_proofs':
        return
    
    count = context.user_data.get('proof_count', 0) + 1
    context.user_data['proof_count'] = count
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id,
            caption=f"📩 <b>BUKTI {count}</b>\n👤 User: {update.effective_user.full_name}\n🆔 ID: <code>{update.effective_user.id}</code>",
            parse_mode='HTML'
        )
    except: pass

    if count < 2:
        await update.message.reply_text(f"✅ Bukti {count} diterima. Kirim 1 lagi!")
    else:
        context.user_data.update({'proof_completed': True, 'status': 'completed'})
        await update.message.reply_text("✅ <b>LENGKAP!</b>\nSilakan ambil link Anda:", reply_markup=get_link_menu(), parse_mode='HTML')

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.chat_join_request.from_user
    c_id = update.chat_join_request.chat.id
    context.bot_data[f"pending_{u.id}"] = c_id
    btn = [[InlineKeyboardButton("Approve ✅", callback_data=f"app_{u.id}_{c_id}"),
            InlineKeyboardButton("Decline ❌", callback_data=f"dec_{u.id}_{c_id}")]]
    await context.bot.send_message(ADMIN_ID, f"🚨 <b>JOIN REQ:</b> {u.full_name}\nID: <code>{u.id}</code>", 
                                   parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action, u_id, c_id = data[0], int(data[1]), int(data[2])
    if action == "app":
        try:
            await context.bot.approve_chat_join_request(c_id, u_id)
            await context.bot.send_message(u_id, "🥳 Permintaan Anda disetujui!")
            await query.edit_message_text(f"✅ Berhasil Approve {u_id}")
            context.bot_data.pop(f"pending_{u_id}", None)
        except Exception as e: await query.edit_message_text(f"❌ Error: {e}")
    else:
        await context.bot.decline_chat_join_request(c_id, u_id)
        await query.edit_message_text(f"❌ Ditolak {u_id}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
