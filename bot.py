"""
🎵 TELEGRAM VOICE CHAT MUSIC BOT
Built with Pyrogram & Py-TgCalls
Features: YouTube Play, Queue, Skip, Pause, Resume, Volume
"""

import os
import asyncio
import random
import re
from datetime import datetime

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserAlreadyParticipant, ChatAdminRequired

from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, StreamType
from pytgcalls.types.input_stream import InputAudioStream

from yt_dlp import YoutubeDL

# ==========================
# CONFIGURATION
# ==========================
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
SESSION_STRING = os.environ.get("SESSION_STRING", "")  # User session for VC

OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# ==========================
# BOT INITIALIZATION
# ==========================
app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# User client for voice chat (bot can't join VC alone)
user = Client(
    "music_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING if SESSION_STRING else None
)

pytgcalls = PyTgCalls(user)

# ==========================
# DATA STORAGE
# ==========================
queues = {}  # {chat_id: [song1, song2, ...]}
active_chats = {}  # {chat_id: {"current": song_info, "playing": True}}

# ==========================
# YOUTUBE DOWNLOAD HELPERS
# ==========================
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


def search_youtube(query):
    """Search YouTube and return first result info"""
    try:
        with YoutubeDL({"quiet": True, "default_search": "ytsearch"}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
            return {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "url": info.get("webpage_url", ""),
                "id": info.get("id", ""),
                "thumbnail": info.get("thumbnail", ""),
                "uploader": info.get("uploader", "Unknown"),
            }
    except Exception as e:
        print(f"Search error: {e}")
        return None


def get_audio_url(video_id):
    """Get direct audio stream URL"""
    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)
            formats = [f for f in info["formats"] if f.get("acodec") != "none" and f.get("vcodec") == "none"]
            if formats:
                return formats[0]["url"]
            return info["formats"][0]["url"]
    except Exception as e:
        print(f"Audio URL error: {e}")
        return None


def format_duration(seconds):
    """Format seconds to mm:ss"""
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


def get_queue_keyboard():
    """Inline keyboard for music controls"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
            InlineKeyboardButton("▶️ Resume", callback_data="resume"),
        ],
        [
            InlineKeyboardButton("⏭ Skip", callback_data="skip"),
            InlineKeyboardButton("🔊 Vol+", callback_data="vol_up"),
            InlineKeyboardButton("🔉 Vol-", callback_data="vol_down"),
        ],
        [
            InlineKeyboardButton("📋 Queue", callback_data="show_queue"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop"),
        ],
    ])


# ==========================
# VOICE CHAT FUNCTIONS
# ==========================
async def join_voice_chat(chat_id):
    """Join voice chat using user client"""
    try:
        await user.join_chat(chat_id)
    except UserAlreadyParticipant:
        pass
    except Exception as e:
        print(f"Join chat error: {e}")

    try:
        await pytgcalls.join_group_call(
            chat_id,
            InputAudioStream(
                "downloads/silent.mp3",  # Placeholder, will be replaced
                StreamType().local_stream,
            ),
        )
        return True
    except Exception as e:
        print(f"Join VC error: {e}")
        return False


async def play_song(chat_id, song_info):
    """Play a song in voice chat"""
    try:
        audio_url = get_audio_url(song_info["id"])
        if not audio_url:
            return False

        await pytgcalls.change_stream(
            chat_id,
            AudioPiped(audio_url),
        )

        active_chats[chat_id] = {
            "current": song_info,
            "playing": True,
            "volume": 100,
        }
        return True
    except Exception as e:
        print(f"Play error: {e}")
        return False


async def handle_queue(chat_id):
    """Handle queue - play next song"""
    if chat_id in queues and queues[chat_id]:
        next_song = queues[chat_id].pop(0)
        success = await play_song(chat_id, next_song)
        if success:
            await app.send_message(
                chat_id,
                f"🎵 **Now Playing**\n\n"
                f"**Title:** {next_song['title']}\n"
                f"**Duration:** {format_duration(next_song['duration'])}\n"
                f"**Channel:** {next_song['uploader']}\n"
                f"**Requested by:** {next_song.get('requested_by', 'Unknown')}",
                reply_markup=get_queue_keyboard(),
            )
        else:
            await app.send_message(chat_id, "❌ Failed to play next song!")
            await handle_queue(chat_id)
    else:
        active_chats.pop(chat_id, None)
        await app.send_message(chat_id, "✅ Queue finished! Use /play to add more songs.")


# ==========================
# COMMAND HANDLERS
# ==========================
@app.on_message(filters.command("start"))
async def start_command(_, message: Message):
    """Start command"""
    await message.reply_text(
        "🎵 **Welcome to Music Bot!** 🎵\n\n"
        "I can play music in your voice chats!\n\n"
        "**Commands:**\n"
        "• `/play <song name>` - Play a song\n"
        "• `/skip` - Skip current song\n"
        "• `/stop` - Stop music\n"
        "• `/pause` - Pause music\n"
        "• `/resume` - Resume music\n"
        "• `/queue` - Show queue\n"
        "• `/volume <1-200>` - Set volume\n"
        "• `/lyrics <song>` - Get lyrics\n\n"
        "Made with ❤️ by @V3NOM_MUSIC_BOT style",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates", url="https://t.me/your_channel")],
        ]),
    )


@app.on_message(filters.command("help"))
async def help_command(_, message: Message):
    """Help command"""
    await message.reply_text(
        "📖 **Music Bot Help**\n\n"
        "**Voice Chat Commands:**\n"
        "• `/play <query>` - Search & play from YouTube\n"
        "• `/play <youtube link>` - Play direct link\n"
        "• `/skip` - Skip to next song\n"
        "• `/stop` - Stop & clear queue\n"
        "• `/pause` - Pause playback\n"
        "• `/resume` - Resume playback\n"
        "• `/volume 100` - Set volume (1-200)\n"
        "• `/queue` - View current queue\n"
        "• `/shuffle` - Shuffle queue\n"
        "• `/loop` - Loop current song\n\n"
        "**Admin Only:**\n"
        "• `/vc` - Join voice chat\n"
        "• `/leavevc` - Leave voice chat",
    )


@app.on_message(filters.command("play"))
async def play_command(_, message: Message):
    """Play command - main music functionality"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if query provided
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/play <song name>`\n"
            "Example: `/play Tum Hi Ho`"
        )

    query = " ".join(message.command[1:])

    # Send searching message
    search_msg = await message.reply_text("🔍 **Searching...** Please wait!")

    # Search YouTube
    song_info = search_youtube(query)
    if not song_info:
        return await search_msg.edit("❌ Song not found! Try another query.")

    # Add requester info
    song_info["requested_by"] = message.from_user.mention

    # Check if already playing
    if chat_id in active_chats and active_chats[chat_id].get("playing"):
        # Add to queue
        if chat_id not in queues:
            queues[chat_id] = []
        queues[chat_id].append(song_info)

        await search_msg.edit(
            f"✅ **Added to Queue** #{len(queues[chat_id])}\n\n"
            f"🎵 **{song_info['title']}**\n"
            f"⏱ Duration: {format_duration(song_info['duration'])}\n"
            f"👤 Requested by: {song_info['requested_by']}"
        )
    else:
        # Play immediately
        await search_msg.edit(
            f"🎵 **Found:** {song_info['title']}\n"
            f"⏱ Duration: {format_duration(song_info['duration'])}\n"
            f"🔄 Joining voice chat..."
        )

        # Join VC if not already
        try:
            await pytgcalls.join_group_call(
                chat_id,
                AudioPiped(get_audio_url(song_info["id"])),
            )

            active_chats[chat_id] = {
                "current": song_info,
                "playing": True,
                "volume": 100,
            }

            await search_msg.edit(
                f"🎵 **Now Playing**\n\n"
                f"**Title:** {song_info['title']}\n"
                f"**Duration:** {format_duration(song_info['duration'])}\n"
                f"**Channel:** {song_info['uploader']}\n"
                f"**Requested by:** {song_info['requested_by']}",
                reply_markup=get_queue_keyboard(),
            )
        except Exception as e:
            print(f"Play error: {e}")
            await search_msg.edit(
                f"❌ **Error playing song!**\n"
                f"Make sure I'm admin with voice chat permissions.\n\n"
                f"Also ensure you have set up the user session correctly."
            )


@app.on_message(filters.command("skip"))
async def skip_command(_, message: Message):
    """Skip current song"""
    chat_id = message.chat.id

    if chat_id not in active_chats:
        return await message.reply_text("❌ Nothing is playing right now!")

    await message.reply_text("⏭ **Skipping...**")
    await pytgcalls.leave_group_call(chat_id)
    await asyncio.sleep(1)
    await handle_queue(chat_id)


@app.on_message(filters.command("stop"))
async def stop_command(_, message: Message):
    """Stop music and clear queue"""
    chat_id = message.chat.id

    if chat_id in queues:
        queues[chat_id] = []
    active_chats.pop(chat_id, None)

    try:
        await pytgcalls.leave_group_call(chat_id)
    except:
        pass

    await message.reply_text("⏹ **Music stopped!** Queue cleared.")


@app.on_message(filters.command("pause"))
async def pause_command(_, message: Message):
    """Pause music"""
    chat_id = message.chat.id

    if chat_id not in active_chats:
        return await message.reply_text("❌ Nothing is playing!")

    try:
        await pytgcalls.pause_stream(chat_id)
        active_chats[chat_id]["playing"] = False
        await message.reply_text("⏸ **Paused!**")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("resume"))
async def resume_command(_, message: Message):
    """Resume music"""
    chat_id = message.chat.id

    if chat_id not in active_chats:
        return await message.reply_text("❌ Nothing was playing!")

    try:
        await pytgcalls.resume_stream(chat_id)
        active_chats[chat_id]["playing"] = True
        await message.reply_text("▶️ **Resumed!**")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("queue"))
async def queue_command(_, message: Message):
    """Show current queue"""
    chat_id = message.chat.id

    if chat_id not in active_chats:
        return await message.reply_text("❌ Nothing is playing!")

    current = active_chats[chat_id].get("current", {})
    queue_list = queues.get(chat_id, [])

    text = f"🎵 **Now Playing:**\n└ {current.get('title', 'Unknown')}\n\n"

    if queue_list:
        text += "📋 **Queue:**\n"
        for i, song in enumerate(queue_list[:10], 1):
            text += f"{i}. {song['title']} ({format_duration(song['duration'])})\n"
        if len(queue_list) > 10:
            text += f"\n...and {len(queue_list) - 10} more"
    else:
        text += "📋 **Queue is empty!**"

    await message.reply_text(text)


@app.on_message(filters.command("volume"))
async def volume_command(_, message: Message):
    """Set volume"""
    chat_id = message.chat.id

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/volume <1-200>`")

    try:
        vol = int(message.command[1])
        if not 1 <= vol <= 200:
            return await message.reply_text("❌ Volume must be between 1 and 200!")

        await pytgcalls.change_volume_call(chat_id, vol)
        if chat_id in active_chats:
            active_chats[chat_id]["volume"] = vol

        await message.reply_text(f"🔊 **Volume set to {vol}%**")
    except ValueError:
        await message.reply_text("❌ Please provide a valid number!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("shuffle"))
async def shuffle_command(_, message: Message):
    """Shuffle queue"""
    chat_id = message.chat.id

    if chat_id not in queues or not queues[chat_id]:
        return await message.reply_text("❌ Queue is empty!")

    random.shuffle(queues[chat_id])
    await message.reply_text("🔀 **Queue shuffled!**")


@app.on_message(filters.command("lyrics"))
async def lyrics_command(_, message: Message):
    """Get lyrics (placeholder - integrate with lyrics API)"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/lyrics <song name>`")

    query = " ".join(message.command[1:])
    await message.reply_text(
        f"📝 **Lyrics for:** {query}\n\n"
        f"_Lyrics feature coming soon!_\n"
        f"You can use @GeniusBot or @LyricsBot for now."
    )


# ==========================
# CALLBACK HANDLERS
# ==========================
@app.on_callback_query()
async def callback_handler(_, callback_query):
    """Handle inline button callbacks"""
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if data == "pause":
        try:
            await pytgcalls.pause_stream(chat_id)
            active_chats[chat_id]["playing"] = False
            await callback_query.answer("⏸ Paused!")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "resume":
        try:
            await pytgcalls.resume_stream(chat_id)
            active_chats[chat_id]["playing"] = True
            await callback_query.answer("▶️ Resumed!")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "skip":
        try:
            await pytgcalls.leave_group_call(chat_id)
            await asyncio.sleep(1)
            await handle_queue(chat_id)
            await callback_query.answer("⏭ Skipped!")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "stop":
        try:
            if chat_id in queues:
                queues[chat_id] = []
            active_chats.pop(chat_id, None)
            await pytgcalls.leave_group_call(chat_id)
            await callback_query.answer("⏹ Stopped!")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "vol_up":
        try:
            current_vol = active_chats.get(chat_id, {}).get("volume", 100)
            new_vol = min(current_vol + 10, 200)
            await pytgcalls.change_volume_call(chat_id, new_vol)
            active_chats[chat_id]["volume"] = new_vol
            await callback_query.answer(f"🔊 Volume: {new_vol}%")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "vol_down":
        try:
            current_vol = active_chats.get(chat_id, {}).get("volume", 100)
            new_vol = max(current_vol - 10, 1)
            await pytgcalls.change_volume_call(chat_id, new_vol)
            active_chats[chat_id]["volume"] = new_vol
            await callback_query.answer(f"🔉 Volume: {new_vol}%")
        except Exception as e:
            await callback_query.answer(f"Error: {e}")

    elif data == "show_queue":
        queue_list = queues.get(chat_id, [])
        if queue_list:
            text = "📋 **Queue:**\n"
            for i, song in enumerate(queue_list[:10], 1):
                text += f"{i}. {song['title']}\n"
        else:
            text = "📋 **Queue is empty!**"
        await callback_query.answer(text[:200], show_alert=True)


# ==========================
# MAIN RUNNER
# ==========================
async def main():
    """Start the bot"""
    await app.start()
    print("✅ Bot started!")

    if SESSION_STRING:
        await user.start()
        await pytgcalls.start()
        print("✅ User client & PyTgCalls started!")
    else:
        print("⚠️ No SESSION_STRING found! Voice chat features won't work.")
        print("Run generate_session.py to create a session string.")

    print("🎵 Music Bot is running!")
    await idle()

    await app.stop()
    if SESSION_STRING:
        await user.stop()
        await pytgcalls.stop()


if __name__ == "__main__":
    app.run(main())
