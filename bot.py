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
        print(f"❌ ERROR SYSTEM saat membuat link: {e}")
        return None

# --- KEYBOARD MENU ---
def get_main_menu():
    keyboard = [
        [KeyboardButton("📝 Registrasi"), KeyboardButton("❓ Bantuan")],
        [KeyboardButton("📊 Status Permintaan")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_link_menu():
    # Menu khusus yang muncul HANYA setelah kirim 2 bukti
    keyboard = [
        [KeyboardButton("🔗 Request Link")],
        [KeyboardButton("🔙 Kembali ke Menu Utama")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    # Reset status bukti user saat start ulang
    context.user_data['proof_count'] = 0
    
    await update.message.reply_text(
        f"Halo {user_name}! 👋\nSaya adalah Bot Verifikasi.\n\n"
        "Silakan pilih menu **📝 Registrasi** untuk memulai proses bergabung.",
        reply_markup=get_main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # --- LOGIKA REGISTRASI ---
    if text == "📝 Registrasi":
        # Reset hitungan bukti agar user mulai dari 0
        context.user_data['proof_count'] = 0
        context.user_data['status'] = 'uploading_proofs'
        
        msg = (
            "🔒 **SYARAT REGISTRASI**\n\n"
            "Agar bisa mendapatkan Link Grup, Anda wajib:\n"
            f"1. **Subscribe** channel ini: {YT_LINK}\n"
            "2. **Like** video terbaru.\n\n"
            "📸 **TUGAS ANDA:**\n"
            "Silakan kirimkan **2 (Dua) Screenshot** bukti (1 SS Subscribe & 1 SS Like) ke sini sekarang.\n\n"
            "⚠️ *Bot akan menolak jika Anda hanya mengirim 1 bukti.*"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    # --- LOGIKA REQUEST LINK (Hanya bisa diakses jika sudah lolos bukti) ---
    elif text == "🔗 Request Link":
        # Cek apakah user benar-benar sudah kirim 2 bukti (security check)
        if context.user_data.get('proof_completed', False):
            await update.message.reply_text("⏳ Memproses Link Unik untuk Anda...")
            
            link = await generate_unique_link(context, user_name)
            
            if link:
                msg = (
                    f"✅ **Link Akses Siap!**\n\n"
                    f"🔗 {link}\n\n"
                    "**LANGKAH TERAKHIR:**\n"
                    "1. Klik link di atas.\n"
                    "2. Klik **'Request to Join'**.\n"
                    "3. Admin akan menyetujui request Anda karena bukti sudah diterima."
                )
                await update.message.reply_text(msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Gagal membuat link. Hubungi Admin.")
        else:
            await update.message.reply_text("⛔ **AKSES DITOLAK.**\nAnda belum menyelesaikan tugas screenshot. Silakan klik menu Registrasi ulang.")

    elif text == "📊 Status Permintaan":
        if f"pending_{user_id}" in context.bot_data:
            await update.message.reply_text("Status: ⏳ **Menunggu Approval Admin**\n(Bukti Anda sudah diteruskan ke Admin)")
        else:
            await update.message.reply_text("Status: ❌ **Belum ada permintaan join.**")

    elif text == "🔙 Kembali ke Menu Utama":
        context.user_data['proof_count'] = 0 # Reset
        await update.message.reply_text("Menu Utama:", reply_markup=get_main_menu())
        
    elif text == "❓ Bantuan":
         await update.message.reply_text(f"Hubungi Admin: tg://user?id={ADMIN_ID}")

# --- HANDLER GAMBAR/SCREENSHOT (CORE LOGIC) ---
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    # Cek apakah user sedang dalam mode registrasi
    status = context.user_data.get('status')
    
    if status == 'uploading_proofs':
        # Tambah counter bukti
        current_count = context.user_data.get('proof_count', 0) + 1
        context.user_data['proof_count'] = current_count
        
        # Forward bukti langsung ke Admin (Untuk arsip pengecekan nanti)
        try:
            caption_admin = f"📸 Bukti ke-{current_count} dari {user_name} (ID: {user_id})"
            await update.message.forward(chat_id=ADMIN_ID)
            await context.bot.send_message(chat_id=ADMIN_ID, text=caption_admin)
        except:
            pass # Error ignore jika bot diblok admin

        # Logika Pengecekan Jumlah
        if current_count == 1:
            await update.message.reply_text(
                "⚠️ **Baru 1 Bukti Diterima.**\n"
                "Mohon kirimkan **1 Screenshot lagi** (Pastikan ada bukti Subscribe DAN Like).\n"
                "Bot belum memberikan akses link jika bukti belum lengkap."
            )
        
        elif current_count >= 2:
            # Sukses
            context.user_data['proof_completed'] = True
            context.user_data['status'] = 'completed' # Stop mode upload
            
            await update.message.reply_text(
                "✅ **DATA LENGKAP!**\n"
                "Terima kasih, bukti Subscribe & Like sudah diterima.\n\n"
                "👇 **Silakan klik tombol di bawah untuk mengambil Link Grup:**",
                reply_markup=get_link_menu()
            )
            
    else:
        # Jika user kirim gambar tanpa klik Registrasi dulu
        await update.message.reply_text("🤔 Gambar apa ini? Silakan klik menu **'📝 Registrasi'** terlebih dahulu sebelum mengirim bukti.")

# --- LOGIKA APPROVAL (ADMIN) ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.from_user.id
    user_name = update.chat_join_request.from_user.full_name
    chat_id = update.chat_join_request.chat.id
    
    # Simpan data pending
    context.bot_data[f"pending_{user_id}"] = chat_id
    
    # Tombol Approval untuk Admin
    keyboard = [[
        InlineKeyboardButton("Approve ✅", callback_data=f"app_{user_id}_{chat_id}"),
        InlineKeyboardButton("Decline ❌", callback_data=f"dec_{user_id}_{chat_id}")
    ]]
    
    admin_msg = (
        f"🚨 **ADA REQUEST JOIN BARU!**\n\n"
        f"👤 **Nama:** {user_name}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        "User ini baru saja masuk lewat link. **Cek Screenshot yang diteruskan bot sebelumnya di chat ini.**\n"
        "Jika bukti di atas valid, silakan Approve."
    )
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Info ke User
    try:
        await context.bot.send_message(chat_id=user_id, text="⏳ **Request Terkirim!** Mohon tunggu Admin memverifikasi bukti Anda.")
    except:
        pass

# --- HANDLER TOMBOL ADMIN ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action, u_id, c_id = data[0], int(data[1]), int(data[2])

    if action == "app":
        try:
            await context.bot.approve_chat_join_request(chat_id=c_id, user_id=u_id)
            await context.bot.send_message(chat_id=u_id, text="🥳 **SELAMAT BERGABUNG!**\nPermintaan Anda telah disetujui Admin.")
            await query.edit_message_text(f"✅ User ID {u_id} Telah di-APPROVE.")
            if f"pending_{u_id}" in context.bot_data: del context.bot_data[f"pending_{u_id}"]
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal: {e}")
            
    else: # Decline
        try:
            await context.bot.decline_chat_join_request(chat_id=c_id, user_id=u_id)
            await context.bot.send_message(chat_id=u_id, text="❌ **DITOLAK.** Admin menilai bukti Anda kurang valid/lengkap.")
            await query.edit_message_text(f"❌ User ID {u_id} Telah di-TOLAK.")
        except Exception as e:
            await query.edit_message_text(f"❌ Gagal: {e}")

# --- MAIN ---
def main():
    print("Bot Registrasi berjalan...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
