import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

# --- KONFIGURASI ---
TOKEN = '8370842756:AAEbjHtrnZNPnduqGNl-mTyuVmE8iuNB4fE'
ADMIN_ID = 7655136272
GROUP_CHAT_ID = -1003649901491
YT_LINK = "https://www.youtube.com/channel/UCePnGN0-MkIt_dNjm1viwug"

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- FUNGSI GENERATE LINK ---
async def generate_unique_link(context: ContextTypes.DEFAULT_TYPE, user_name):
    try:
        link_name = f"Link untuk {user_name}"
        new_link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_CHAT_ID,
            name=link_name,
            creates_join_request=True
        )
        return new_link.invite_link
    except Exception as e:
        logging.error(f"Error saat membuat link: {e}")
        return None

# --- KEYBOARD MENU ---
def get_main_menu():
    keyboard = [
        [KeyboardButton("📝 Registrasi"), KeyboardButton("❓ Bantuan")],
        [KeyboardButton("📊 Status Permintaan")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_link_menu():
    keyboard = [
        [KeyboardButton("🔗 Request Link")],
        [KeyboardButton("🔙 Kembali ke Menu Utama")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    context.user_data['proof_count'] = 0
    context.user_data['proof_completed'] = False
    
    await update.message.reply_text(
        f"Halo <b>{user_name}</b>! 👋\nSaya adalah Bot Verifikasi.\n\n"
        "Silakan pilih menu <b>📝 Registrasi</b> untuk memulai proses bergabung.",
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
            "🔒 <b>SYARAT REGISTRASI</b>\n\n"
            "Agar bisa mendapatkan Link Grup, Anda wajib:\n"
            f"1. <b>Subscribe</b> channel ini: {YT_LINK}\n"
            "2. <b>Like</b> video terbaru.\n\n"
            "📸 <b>TUGAS ANDA:</b>\n"
            "Silakan kirimkan <b>2 (Dua) Screenshot</b> bukti (1 SS Subscribe & 1 SS Like) ke sini sekarang.\n\n"
            "⚠️ <i>Bot akan menolak jika Anda hanya mengirim 1 bukti.</i>"
        )
        await update.message.reply_text(msg, parse_mode='HTML')

    elif text == "🔗 Request Link":
        if context.user_data.get('proof_completed', False):
            await update.message.reply_text("⏳ Memproses Link Unik untuk Anda...")
            link = await generate_unique_link(context, user_name)
            
            if link:
                msg = (
                    f"✅ <b>Link Akses Siap!</b>\n\n"
                    f"🔗 {link}\n\n"
                    "<b>LANGKAH TERAKHIR:</b>\n"
                    "1. Klik link di atas.\n"
                    "2. Klik <b>'Request to Join'</b>.\n"
                    "3. Admin akan menyetujui request Anda karena bukti sudah diterima."
                )
                await update.message.reply_text(msg, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ Gagal membuat link. Hubungi Admin.")
        else:
            await update.message.reply_text("⛔ <b>AKSES DITOLAK.</b>\nAnda belum menyelesaikan tugas screenshot.", parse_mode='HTML')

    elif text == "📊 Status Permintaan":
        if f"pending_{user_id}" in context.bot_data:
            await update.message.reply_text("Status: ⏳ <b>Menunggu Approval Admin</b>", parse_mode='HTML')
        else:
            await update.message.reply_text("Status: ❌ <b>Belum ada permintaan join.</b>", parse_mode='HTML')

    elif text == "🔙 Kembali ke Menu Utama":
        context.user_data['proof_count'] = 0
        await update.message.reply_text("Menu Utama:", reply_markup=get_main_menu())
        
    elif text == "❓ Bantuan":
         await update.message.reply_text(f"Hubungi Admin: <a href='tg://user?id={ADMIN_ID}'>Klik di Sini</a>", parse_mode='HTML')

# --- HANDLER GAMBAR ---
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    if context.user_data.get('status') == 'uploading_proofs':
        current_count = context.user_data.get('proof_count', 0) + 1
        context.user_data['proof_count'] = current_count
        
        # Kirim bukti ke Admin menggunakan send_photo (lebih stabil)
        photo_file_id = update.message.photo[-1].file_id
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_file_id,
                caption=f"📩 <b>BUKTI BARU</b>\n👤 User: {user_name}\n🆔 ID: <code>{user_id}</code>\n📸 Bukti ke-{current_count}",
                parse_mode='HTML'
            )
        except:
            pass

        if current_count < 2:
            await update.message.reply_text(f"⚠️ <b>Baru {current_count} Bukti Diterima.</b>\nMohon kirim 1 bukti lagi.", parse_mode='HTML')
        else:
            context.user_data['proof_completed'] = True
            context.user_data['status'] = 'completed'
            await update.message.reply_text(
                "✅ <b>DATA LENGKAP!</b>\nSilakan klik tombol di bawah untuk mengambil Link Grup:",
                reply_markup=get_link_menu(),
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text("Silakan klik <b>📝 Registrasi</b> dulu.")

# --- LOGIKA JOIN REQUEST ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.from_user.id
    user_name = update.chat_join_request.from_user.full_name
    chat_id = update.chat_join_request.chat.id
    
    context.bot_data[f"pending_{user_id}"] = chat_id
    
    keyboard = [[
        InlineKeyboardButton("Approve ✅", callback_data=f"app_{user_id}_{chat_id}"),
        InlineKeyboardButton("Decline ❌", callback_data=f"dec_{user_id}_{chat_id}")
    ]]
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🚨 <b>REQUEST JOIN</b>\n👤 Nama: {user_name}\n🆔 ID: <code>{user_id}</code>\n\nCek bukti screenshot di atas sebelum Approve!",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action, u_id, c_id = data[0], int(data[1]), int(data[2])

    if action == "app":
        try:
            await context.bot.approve_chat_join_request(chat_id=c_id, user_id=u_id)
            await context.bot.send_message(chat_id=u_id, text="🥳 <b>SELAMAT BERGABUNG!</b>\nPermintaan Anda telah disetujui Admin.", parse_mode='HTML')
            await query.edit_message_text(f"✅ User ID {u_id} Telah di-APPROVE.")
            context.bot_data.pop(f"pending_{u_id}", None)
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal: {e}")
    else:
        try:
            await context.bot.decline_chat_join_request(chat_id=c_id, user_id=u_id)
            await context.bot.send_message(chat_id=u_id, text="❌ <b>DITOLAK.</b> Bukti Anda dinilai tidak valid.", parse_mode='HTML')
            await query.edit_message_text(f"❌ User ID {u_id} Telah di-TOLAK.")
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal: {e}")

def main():
    print("Bot berjalan...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
