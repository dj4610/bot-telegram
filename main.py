import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, ChatJoinRequestHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler

# --- KONFIGURASI (Mengambil dari Railway Environment Variables) ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
GROUP_CHAT_ID = int(os.getenv('GROUP_ID', '0'))
YT_LINK = os.getenv('YT_LINK', 'https://youtube.com')

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
    u_id = update.effective_user
