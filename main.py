import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

# --- KONFIGURASI ---
TOKEN = '8370842756:AAEbjHtrnZNPnduqGNl-mTyuVmE8iuNB4fE'
ADMIN_ID = 7655136272
GROUP_CHAT_ID = -1003649901491
YT_LINK = "https://www.youtube.com/channel/UCePnGN0-MkIt_dNjm1viwug"

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- KEYBOARD MENU ---

def get_main_menu():
    keyboard = [
        [KeyboardButton("📝 Registrasi"), KeyboardButton("❓ Bantuan")],
        [KeyboardButton("📊 Status Permintaan")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_upload_menu():
    # Menu ini muncul saat proses upload screenshot
    keyboard = [
        [KeyboardButton("📸 Kirim Bukti Subscribe"), KeyboardButton("📸 Kirim Bukti Like")],
        [KeyboardButton("❌ Batal Registrasi")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, placeholder="Kirim 2 Foto Screenshot...")

def get_link_menu():
    keyboard = [
        [KeyboardButton("🔗 Request Link")],
        [KeyboardButton("🔙 Kembali ke Menu Utama")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- FUNGSI GENERATE LINK ---
async def generate_unique_link(context: ContextTypes.DEFAULT_TYPE, user_name):
    try:
        new_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_CHAT_ID,
            name=f"Link {user_name}",
            creates_join_request=True
        )
        return new_link.invite_link
    except Exception as e:
        logging.error(f"Error link: {e}")
        return None

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    context.user_data.clear() # Reset data
    
    await update.message.reply_text(
        f"Halo <b>{user_name}</b>! 👋\nSilakan pilih menu <b>📝 Registrasi</b> untuk memulai.",
        reply_markup=get_main_menu(),
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if text == "📝 Registrasi":
        context.user_data['proof_count'] = 0
        context.user_data['status'] = 'uploading_proofs'
        
        msg = (
            "🔒 <b>MODE REGISTRASI AKTIF</b>\n\n"
            f"Silakan <b>Subscribe & Like</b> di sini:\n{YT_LINK}\n\n"
            "📸 <b>TUGAS:</b> Kirimkan 2 Screenshot bukti sekarang.\n"
            "<i>Menu di bawah telah berubah menjadi menu upload.</i>"
        )
        # DI SINI KEYBOARD BERGANTI:
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_upload_menu())

    elif text == "❌ Batal Registrasi" or text == "🔙 Kembali ke Menu Utama":
        context.user_data.clear()
        await update.message.reply_text("Kembali ke Menu Utama:", reply_markup=get_main_menu())

    elif text == "🔗 Request Link":
        if context.user_data.get('proof_completed'):
            await update.message.reply_text("⏳ Membuat link unik...")
            link = await generate_unique_link(context, user_name)
            if link:
                await update.message.reply_text(f"✅ <b>Link Akses:</b>\n{link}\n\nSilakan klik dan pilih 'Request to Join'.", parse_mode='HTML')
        else:
            await update.message.reply_text("⛔ Selesaikan bukti dulu!")

    elif text == "📊 Status Permintaan":
        status = "⏳ Menunggu Admin" if f"pending_{user_id}" in context.bot_data else "❌ Tidak ada permintaan aktif."
        await update.message.reply_text(f"Status: <b>{status}</b>", parse_mode='HTML')

    elif text == "❓ Bantuan":
         await update.message.reply_text(f"Hubungi Admin: <a href='tg://user?id={ADMIN_ID}'>Klik di Sini</a>", parse_mode='HTML')

# --- HANDLER GAMBAR ---
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('status') != 'uploading_proofs':
        await update.message.reply_text("Klik 📝 Registrasi dulu!")
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    current_count = context.user_data.get('proof_count', 0) + 1
    context.user_data['proof_count'] = current_count
    
    # Teruskan foto ke Admin
    photo_id = update.message.photo[-1].file_id
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=f"📩 <b>BUKTI {current_count}</b>\n👤 User: {user_name}\n🆔 ID: <code>{user_id}</code>",
            parse_mode='HTML'
        )
    except: pass

    if current_count < 2:
        await update.message.reply_text(f"✅ Bukti ke-{current_count} diterima. Kirim 1 foto lagi!")
    else:
        context.user_data['proof_completed'] = True
        context.user_data['status'] = 'completed'
        # DI SINI KEYBOARD BERGANTI LAGI KE MENU LINK:
        await update.message.reply_text(
            "✅ <b>SEMUA BUKTI DITERIMA!</b>\n\nData Anda sudah diteruskan ke Admin. Silakan ambil link Anda di bawah:",
            reply_markup=get_link_menu(),
            parse_mode='HTML'
        )

# --- SISANYA TETAP SAMA (Admin Approval Logic) ---
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
        await context.bot.approve_chat_join_request(c_id, u_id)
        await context.bot.send_message(u_id, "🥳 Disetujui!")
        await query.edit_message_text(f"✅ Approved {u_id}")
    else:
        await context.bot.decline_chat_join_request(c_id, u_id)
        await query.edit_message_text(f"❌ Declined {u_id}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot standby...")
    app.run_polling()

if __name__ == '__main__':
    main()
