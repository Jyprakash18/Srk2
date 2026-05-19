import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, OWNER_ID, DEFAULT_JOIN_CHANNEL_URL
from database import (
    init_db,
    add_admin,
    remove_admin,
    is_admin,
    add_channel,
    remove_channel,
    get_channels,
    save_analytics,
    analytics_count,
    set_setting,
    get_setting
)
from link_converter import extract_urls, convert_link
from product_fetcher import fetch_product
from ai_writer import generate_ai_description

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if not user or not is_admin(user.id, OWNER_ID):
            await update.effective_message.reply_text("❌ Access denied.")
            return

        return await func(update, context)

    return wrapper


def build_buttons(buy_url: str):
    join_url = get_setting("join_channel_url", DEFAULT_JOIN_CHANNEL_URL)

    keyboard = [
        [
            InlineKeyboardButton("✅ Buy Now", url=buy_url)
        ],
        [
            InlineKeyboardButton("Join Deals Channel", url=join_url),
            InlineKeyboardButton("Share Product", switch_inline_query=buy_url)
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def build_caption(product: dict, converted_url: str, ai_text: str = ""):
    title = product.get("title") or "Product"
    price = product.get("price") or ""
    mrp = product.get("mrp") or ""
    rating = product.get("rating") or ""

    lines = []

    lines.append(f"📦 {title}")

    if price and mrp:
        lines.append(f"💰 {mrp} → {price}")
    elif price:
        lines.append(f"💰 {price}")

    if rating:
        lines.append(f"⭐ {rating} Rating")

    if ai_text:
        lines.append("")
        lines.append(ai_text)

    lines.append("")
    lines.append(f"🔗 Short Link:\n{converted_url}")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Affiliate Link Converter Bot\n\n"
        "Amazon/Flipkart product link bhejo.\n"
        "Bot usko affiliate short link me convert karega.\n\n"
        "Admin commands ke liye /admin use karo."
    )
    await update.message.reply_text(text)


@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚙️ Admin Panel\n\n"
        "Commands:\n"
        "/addchannel @channelusername\n"
        "/removechannel @channelusername\n"
        "/channels\n"
        "/addadmin user_id\n"
        "/removeadmin user_id\n"
        "/analytics\n"
        "/setjoinurl [t.me](https://t.me/yourchannel\n\n)"
        "Auto post: kisi bhi Amazon/Flipkart link ya product post ko bot me bhejo."
    )
    await update.message.reply_text(text)


@admin_only
async def add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addchannel @channelusername")
        return

    chat_id = context.args[0]
    add_channel(chat_id, chat_id)
    await update.message.reply_text(f"✅ Channel added: {chat_id}")


@admin_only
async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removechannel @channelusername")
        return

    chat_id = context.args[0]
    remove_channel(chat_id)
    await update.message.reply_text(f"🗑 Channel removed: {chat_id}")


@admin_only
async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = get_channels()

    if not channels:
        await update.message.reply_text("No channels added.")
        return

    text = "📢 Channels:\n\n"
    for chat_id, title in channels:
        text += f"- {chat_id} | {title or ''}\n"

    await update.message.reply_text(text)


@admin_only
async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addadmin user_id")
        return

    user_id = int(context.args[0])
    add_admin(user_id)
    await update.message.reply_text(f"✅ Admin added: {user_id}")


@admin_only
async def remove_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removeadmin user_id")
        return

    user_id = int(context.args[0])
    remove_admin(user_id)
    await update.message.reply_text(f"🗑 Admin removed: {user_id}")


@admin_only
async def analytics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, by_platform = analytics_count()

    text = f"📊 Analytics Dashboard\n\nTotal conversions: {total}\n\n"

    if by_platform:
        text += "Platform wise:\n"
        for platform, count in by_platform:
            text += f"- {platform}: {count}\n"

    await update.message.reply_text(text)


@admin_only
async def set_join_url_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setjoinurl [t.me](https://t.me/yourchannel)")
        return

    url = context.args[0]
    set_setting("join_channel_url", url)
    await update.message.reply_text("✅ Join channel URL updated.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    text = message.text or message.caption or ""
    urls = extract_urls(text)

    if not urls:
        await message.reply_text("Amazon ya Flipkart link bhejo.")
        return

    platform, original_url = urls[0]
    converted_url = convert_link(platform, original_url, shorten=True)

    product = fetch_product(platform, original_url)
    ai_text = generate_ai_description(product)
    caption = build_caption(product, converted_url, ai_text)

    save_analytics(
        user_id=user.id if user else 0,
        original_url=original_url,
        converted_url=converted_url,
        platform=platform
    )

    reply_markup = build_buttons(converted_url)

    photo_url = product.get("image")

    if message.photo:
        photo_file = message.photo[-1].file_id
        await message.reply_photo(
            photo=photo_file,
            caption=caption,
            reply_markup=reply_markup
        )
    elif photo_url:
        await message.reply_photo(
            photo=photo_url,
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        await message.reply_text(
            caption,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )

    channels = get_channels()

    for chat_id, _ in channels:
        try:
            if message.photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif photo_url:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url,
                    caption=caption,
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
        except Exception as e:
            logging.error(f"Failed to post to {chat_id}: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Render Web Service ko active rakhne ke liye dummy server
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_dummy_server():
    # Render automatic PORT variable deta hai, nahi toh default 8080
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    print(f"Dummy Web Server started on port {port}")
    server.serve_forever()

# 2. Aapka main function (Jo pehle line 291 par tha)
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing in environment variables.")
    
    init_db()
    add_admin(OWNER_ID)
    
    # Background thread mein dummy web server ko start karna taaki Render Timeout na kare
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Aapke saare handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("addchannel", add_channel_cmd))
    app.add_handler(CommandHandler("removechannel", remove_channel_cmd))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("addadmin", add_admin_cmd))
    app.add_handler(CommandHandler("removeadmin", remove_admin_cmd))
    app.add_handler(CommandHandler("analytics", analytics_cmd))
    app.add_handler(CommandHandler("setjoinurl", set_join_url_cmd))
    
    app.add_handler(CallbackQueryHandler(button_callback))
    
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.CaptionRegex(".*") | filters.PHOTO,
            handle_message
        )
    )
    
    print("Bot running...")
    app.run_polling()

# 3. Naye Python (3.14) ke liye event loop handling aur execution
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        threading.Thread(target=main).start()
    else:
        main()
