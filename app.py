import os
import shutil
import hashlib
import pyminizip
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
API_ID = 12767104        # <-- apna daal
API_HASH = "a0ce1daccf78234927eb68a62f894b97"    # <-- apna daal
BOT_TOKEN = "8084824375:AAFDP5mZiGTUoedM8Xl5tvsfYfuj_sz-1rc"  # <-- apna daal

TMP = "temp"
os.makedirs(TMP, exist_ok=True)

app = Client(
    "zip_master_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_files = {}

# ================= UTILS =================
def clean(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ================= START =================
@app.on_message(filters.command("start"))
async def start(_, m):
    await m.reply(
        "✨ **ZIP MASTER FILE OPS BOT** ✨\n\n"
        "📦 Zip / 🔓 Unzip / ✏️ Rename\n"
        "🔐 Password optional\n"
        "🧹 Auto cleanup\n\n"
        "**बस file भेजो, बाकी जादू मैं करूंगा 😉**",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📦 Send a File", callback_data="noop")]]
        )
    )

# ================= FILE RECEIVE =================
@app.on_message(filters.document)
async def handle_file(_, m):
    uid = m.from_user.id
    user_dir = f"{TMP}/{uid}"
    os.makedirs(user_dir, exist_ok=True)

    file_path = await m.download(file_name=f"{user_dir}/{m.document.file_name}")
    user_files[uid] = file_path

    await m.reply(
        f"📁 **File Ready:** `{m.document.file_name}`\n\n"
        "👇 Choose Operation",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📦 ZIP", callback_data="zip"),
                InlineKeyboardButton("🔓 UNZIP", callback_data="unzip")
            ],
            [
                InlineKeyboardButton("✏️ Rename", callback_data="rename"),
                InlineKeyboardButton("ℹ️ Info", callback_data="info")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
    )

# ================= CALLBACKS =================
@app.on_callback_query()
async def cb(_, q):
    uid = q.from_user.id
    path = user_files.get(uid)

    if not path:
        await q.answer("❌ No active file", show_alert=True)
        return

    # ---------- ZIP ----------
    if q.data == "zip":
        await q.message.edit(
            "🔐 **Password लगाना है?**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Yes", callback_data="zip_pass"),
                    InlineKeyboardButton("❌ No", callback_data="zip_nopass")
                ]
            ])
        )

    elif q.data == "zip_nopass":
        zip_path = path + ".zip"
        pyminizip.compress(path, None, zip_path, 0)
        await q.message.reply_document(zip_path, caption="📦 **ZIP Ready (No Password)**")
        clean(f"{TMP}/{uid}")

    elif q.data == "zip_pass":
        await q.message.edit("🔑 **Password भेजो**")
        user_files[uid] = ("await_pass", path)

    # ---------- UNZIP ----------
    elif q.data == "unzip":
        await q.message.reply("🔓 **Unzip supported only for .zip**")
        clean(f"{TMP}/{uid}")

    # ---------- INFO ----------
    elif q.data == "info":
        size = os.path.getsize(path)
        h = file_hash(path)
        await q.message.reply(
            f"📄 **File Info**\n\n"
            f"📦 Size: `{size} bytes`\n"
            f"🔑 SHA256:\n`{h}`"
        )

    # ---------- RENAME ----------
    elif q.data == "rename":
        await q.message.reply("✏️ **New filename भेजो (extension के साथ)**")
        user_files[uid] = ("rename", path)

    elif q.data == "cancel":
        clean(f"{TMP}/{uid}")
        await q.message.edit("❌ Cancelled & cleaned")

# ================= TEXT HANDLER =================
@app.on_message(filters.text)
async def text_handler(_, m):
    uid = m.from_user.id
    data = user_files.get(uid)

    if not data:
        return

    mode, path = data

    # ---------- PASSWORD ZIP ----------
    if mode == "await_pass":
        zip_path = path + ".zip"
        pyminizip.compress(path, None, zip_path, m.text, 0)
        await m.reply_document(zip_path, caption="🔐 **Password ZIP Ready**")
        clean(f"{TMP}/{uid}")

    # ---------- RENAME ----------
    elif mode == "rename":
        new_path = os.path.join(os.path.dirname(path), m.text)
        os.rename(path, new_path)
        await m.reply_document(new_path, caption="✏️ **Renamed Successfully**")
        clean(f"{TMP}/{uid}")

# ================= RUN =================
print("🤖 ZIP MASTER BOT RUNNING")
app.run()