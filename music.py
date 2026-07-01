"""
Music Plugin for Hexa Music Bot
"""

import asyncio
import os
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pytgcalls.types import AudioPiped

from config import (
    SUDO_USERS, MAX_QUEUE_SIZE, DEFAULT_VOLUME,
    OWNER_ID, BOT_USERNAME, BOT_NAME,
    OWNER_URL, CHANNEL_URL, SUPPORT_URL, ADD_BOT_URL
)
from utils.helpers import format_duration

queues = {}
active_chats = {}

from yt_dlp import YoutubeDL

YDL_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
}


def search_youtube(query):
    try:
        with YoutubeDL({"quiet": True, "default_search": "ytsearch", "noplaylist": True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if "entries" in info and info["entries"]:
                entry = info["entries"][0]
                return {
                    "title": entry.get("title", "Unknown"),
                    "duration": entry.get("duration", 0),
                    "id": entry.get("id", ""),
                    "url": entry.get("webpage_url", ""),
                    "thumbnail": entry.get("thumbnail", ""),
                    "uploader": entry.get("uploader", "Unknown"),
                    "uploader_url": entry.get("uploader_url", ""),
                    "views": entry.get("view_count", 0),
                    "upload_date": entry.get("upload_date", ""),
                    "description": entry.get("description", "")[:100] + "..." if entry.get("description") else "",
                }
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
    return None


def get_audio_stream(video_id):
    try:
        with YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)
            formats = [f for f in info.get("formats", [])
                      if f.get("acodec") != "none" and f.get("vcodec") == "none"]
            if formats:
                formats.sort(key=lambda x: x.get("abr", 0), reverse=True)
                return formats[0]["url"]
            for f in info.get("formats", []):
                if f.get("acodec") != "none":
                    return f["url"]
    except Exception as e:
        print(f"[STREAM ERROR] {e}")
    return None


def get_song_card_keyboard(song_info, chat_id):
    buttons = []
    buttons.append([
        InlineKeyboardButton("Pause", callback_data=f"pause|{chat_id}"),
        InlineKeyboardButton("Resume", callback_data=f"resume|{chat_id}"),
        InlineKeyboardButton("Skip", callback_data=f"skip|{chat_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("Vol -", callback_data=f"vol_down|{chat_id}"),
        InlineKeyboardButton("Vol +", callback_data=f"vol_up|{chat_id}"),
        InlineKeyboardButton("Loop", callback_data=f"loop|{chat_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("Queue", callback_data=f"queue|{chat_id}"),
        InlineKeyboardButton("Lyrics", callback_data=f"lyrics|{chat_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("Owner", url=OWNER_URL),
        InlineKeyboardButton("Channel", url=CHANNEL_URL),
    ])
    buttons.append([
        InlineKeyboardButton("Support", url=SUPPORT_URL),
        InlineKeyboardButton("Add Bot", url=ADD_BOT_URL),
    ])
    return InlineKeyboardMarkup(buttons)


def get_queue_card_keyboard(chat_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Shuffle", callback_data=f"shuffle|{chat_id}"),
            InlineKeyboardButton("Clear", callback_data=f"clear|{chat_id}"),
        ],
        [InlineKeyboardButton("Back to Player", callback_data=f"player|{chat_id}")],
    ])


def format_song_card(song_info, status="Now Playing", queue_pos=None):
    title = song_info.get("title", "Unknown")
    duration = format_duration(song_info.get("duration", 0))
    uploader = song_info.get("uploader", "Unknown")
    views = song_info.get("views", 0)
    requested_by = song_info.get("requested_by", "Unknown")

    if views >= 1000000:
        views_str = f"{views/1000000:.1f}M"
    elif views >= 1000:
        views_str = f"{views/1000:.1f}K"
    else:
        views_str = str(views)

    text = f"""{status}

**{title}**

Duration: `{duration}`
Channel: `{uploader}`
Views: `{views_str}`
Requested by: {requested_by}"""

    if queue_pos:
        text += f"\nQueue Position: #{queue_pos}"

    text += f"\n\n---\n{BOT_NAME}"
    return text.strip()


def is_admin_filter(_, __, message: Message):
    return message.from_user.id in SUDO_USERS or message.from_user.id == OWNER_ID


def setup_music_handlers(app, pytgcalls):

    @app.on_message(
        filters.command("play")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def play_handler(_, message: Message):
        chat_id = message.chat.id

        if len(message.command) < 2:
            return await message.reply_text(
                "Usage: /play <song name or YouTube link>\n\n"
                "Examples:\n"
                "/play Tum Hi Ho\n"
                "/play https://youtube.com/watch?v=..."
            )

        query = " ".join(message.command[1:])
        user = message.from_user

        search_msg = await message.reply_text(f"Searching... `{query}`")

        song = search_youtube(query)
        if not song:
            return await search_msg.edit("Song not found! Try another query.")

        song["requested_by"] = user.mention
        song["requester_id"] = user.id

        if chat_id in active_chats and active_chats[chat_id].get("playing"):
            if chat_id not in queues:
                queues[chat_id] = []

            if len(queues[chat_id]) >= MAX_QUEUE_SIZE:
                return await search_msg.edit(f"Queue full! Max {MAX_QUEUE_SIZE} songs.")

            queues[chat_id].append(song)

            queue_text = format_song_card(song, status="Added to Queue", queue_pos=len(queues[chat_id]))

            try:
                await search_msg.delete()
                await message.reply_photo(
                    photo=song["thumbnail"] or "https://telegra.ph/file/placeholder.jpg",
                    caption=queue_text,
                    reply_markup=get_queue_card_keyboard(chat_id),
                )
            except:
                await search_msg.edit(queue_text)
        else:
            await search_msg.edit("Found! Joining voice chat...")

            stream_url = get_audio_stream(song["id"])
            if not stream_url:
                return await search_msg.edit("Failed to get audio stream!")

            try:
                await pytgcalls.join_group_call(
                    chat_id,
                    AudioPiped(stream_url),
                )

                active_chats[chat_id] = {
                    "current": song,
                    "playing": True,
                    "loop": False,
                    "volume": DEFAULT_VOLUME,
                }

                now_playing_text = format_song_card(song, status="Now Playing")

                await search_msg.delete()

                try:
                    await message.reply_photo(
                        photo=song["thumbnail"] or "https://telegra.ph/file/placeholder.jpg",
                        caption=now_playing_text,
                        reply_markup=get_song_card_keyboard(song, chat_id),
                    )
                except Exception as e:
                    await message.reply_text(
                        now_playing_text,
                        reply_markup=get_song_card_keyboard(song, chat_id),
                        disable_web_page_preview=False,
                    )

            except Exception as e:
                print(f"[PLAY ERROR] {e}")
                await search_msg.edit(
                    f"Error: {str(e)}\n\n"
                    f"Make sure:\n"
                    f"- I'm admin in this group\n"
                    f"- I have voice chat permissions\n"
                    f"- A voice chat is active"
                )


    @app.on_message(
        filters.command("skip")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def skip_handler(_, message: Message):
        chat_id = message.chat.id

        if chat_id not in active_chats:
            return await message.reply_text("Nothing is playing right now!")

        skip_msg = await message.reply_text("Skipping...")

        try:
            await pytgcalls.leave_group_call(chat_id)
            await asyncio.sleep(1)

            if chat_id in queues and queues[chat_id]:
                next_song = queues[chat_id].pop(0)
                stream_url = get_audio_stream(next_song["id"])
                if stream_url:
                    await pytgcalls.join_group_call(chat_id, AudioPiped(stream_url))
                    active_chats[chat_id] = {
                        "current": next_song,
                        "playing": True,
                        "loop": False,
                        "volume": DEFAULT_VOLUME,
                    }

                    next_text = format_song_card(next_song, status="Now Playing")
                    await skip_msg.delete()

                    try:
                        await message.reply_photo(
                            photo=next_song["thumbnail"] or "https://telegra.ph/file/placeholder.jpg",
                            caption=next_text,
                            reply_markup=get_song_card_keyboard(next_song, chat_id),
                        )
                    except:
                        await message.reply_text(
                            next_text,
                            reply_markup=get_song_card_keyboard(next_song, chat_id),
                        )
            else:
                active_chats.pop(chat_id, None)
                await skip_msg.edit("Queue finished!")
        except Exception as e:
            await skip_msg.edit(f"Error: {e}")


    @app.on_message(
        filters.command(["pause", "ps"])
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def pause_handler(_, message: Message):
        chat_id = message.chat.id
        if chat_id not in active_chats:
            return await message.reply_text("Nothing is playing!")

        try:
            await pytgcalls.pause_stream(chat_id)
            active_chats[chat_id]["playing"] = False

            current = active_chats[chat_id]["current"]
            paused_text = format_song_card(current, status="Paused")

            await message.reply_text(
                paused_text,
                reply_markup=get_song_card_keyboard(current, chat_id),
            )
        except Exception as e:
            await message.reply_text(f"Error: {e}")


    @app.on_message(
        filters.command(["resume", "rs"])
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def resume_handler(_, message: Message):
        chat_id = message.chat.id
        if chat_id not in active_chats:
            return await message.reply_text("Nothing was playing!")

        try:
            await pytgcalls.resume_stream(chat_id)
            active_chats[chat_id]["playing"] = True

            current = active_chats[chat_id]["current"]
            resumed_text = format_song_card(current, status="Resumed")

            await message.reply_text(
                resumed_text,
                reply_markup=get_song_card_keyboard(current, chat_id),
            )
        except Exception as e:
            await message.reply_text(f"Error: {e}")


    @app.on_message(
        filters.command("stop")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def stop_handler(_, message: Message):
        chat_id = message.chat.id

        if chat_id in queues:
            queues[chat_id] = []
        active_chats.pop(chat_id, None)

        try:
            await pytgcalls.leave_group_call(chat_id)
        except:
            pass

        await message.reply_text(
            "Stopped!\n\nQueue cleared. Use /play to start again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Play Song", switch_inline_query_current_chat="")],
            ]),
        )


    @app.on_message(
        filters.command("queue")
        & filters.group
    )
    async def queue_handler(_, message: Message):
        chat_id = message.chat.id

        if chat_id not in active_chats:
            return await message.reply_text("Nothing is playing!")

        current = active_chats[chat_id].get("current", {})
        queue_list = queues.get(chat_id, [])

        text = f"Now Playing:\n- {current.get('title', 'Unknown')}\n\n"

        if queue_list:
            text += f"Queue ({len(queue_list)} songs):\n"
            for i, song in enumerate(queue_list[:15], 1):
                text += f"{i}. {song['title']} ({format_duration(song['duration'])})\n"
            if len(queue_list) > 15:
                text += f"\n...and {len(queue_list) - 15} more"
        else:
            text += "Queue is empty!"

        await message.reply_text(
            text,
            reply_markup=get_queue_card_keyboard(chat_id),
        )


    @app.on_message(
        filters.command("volume")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def volume_handler(_, message: Message):
        chat_id = message.chat.id

        if len(message.command) < 2:
            return await message.reply_text("Usage: /volume <1-200>\nExample: /volume 100")

        try:
            vol = int(message.command[1])
            if not 1 <= vol <= 200:
                return await message.reply_text("Volume must be between 1 and 200!")

            await pytgcalls.change_volume_call(chat_id, vol)
            if chat_id in active_chats:
                active_chats[chat_id]["volume"] = vol

            if vol >= 150:
                vol_emoji = "Loud"
            elif vol >= 100:
                vol_emoji = "Medium"
            elif vol >= 50:
                vol_emoji = "Low"
            else:
                vol_emoji = "Very Low"

            await message.reply_text(f"{vol_emoji} Volume set to {vol}%")
        except ValueError:
            await message.reply_text("Please provide a valid number!")
        except Exception as e:
            await message.reply_text(f"Error: {e}")


    @app.on_message(
        filters.command("shuffle")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def shuffle_handler(_, message: Message):
        chat_id = message.chat.id

        if chat_id not in queues or not queues[chat_id]:
            return await message.reply_text("Queue is empty!")

        import random
        random.shuffle(queues[chat_id])
        await message.reply_text("Queue shuffled!")


    @app.on_message(
        filters.command("loop")
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def loop_handler(_, message: Message):
        chat_id = message.chat.id

        if chat_id not in active_chats:
            return await message.reply_text("Nothing is playing!")

        current_loop = active_chats[chat_id].get("loop", False)
        active_chats[chat_id]["loop"] = not current_loop

        status = "Loop enabled! Song will repeat." if not current_loop else "Loop disabled!"
        await message.reply_text(status)


    @app.on_message(
        filters.command(["joinvc", "join"])
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def joinvc_handler(_, message: Message):
        chat_id = message.chat.id

        try:
            await pytgcalls.join_group_call(
                chat_id,
                AudioPiped("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"),
            )
            await message.reply_text(
                "Joined voice chat!\n\nUse /play <song> to start music.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Play Song", switch_inline_query_current_chat="")],
                ]),
            )
        except Exception as e:
            await message.reply_text(f"Error joining VC: {e}")


    @app.on_message(
        filters.command(["leavevc", "leave"])
        & filters.group
        & (filters.user(SUDO_USERS) | filters.create(is_admin_filter))
    )
    async def leavevc_handler(_, message: Message):
        chat_id = message.chat.id

        try:
            await pytgcalls.leave_group_call(chat_id)
            active_chats.pop(chat_id, None)
            await message.reply_text("Left voice chat!")
        except Exception as e:
            await message.reply_text(f"Error: {e}")


    @app.on_callback_query()
    async def music_callback_handler(_, callback_query):
        data = callback_query.data
        user_id = callback_query.from_user.id

        if "|" in data:
            action, chat_id_str = data.split("|", 1)
            chat_id = int(chat_id_str)
        else:
            action = data
            chat_id = callback_query.message.chat.id

        if user_id not in SUDO_USERS and user_id != OWNER_ID:
            return await callback_query.answer("Admin only!", show_alert=True)

        if action == "pause":
            try:
                await pytgcalls.pause_stream(chat_id)
                if chat_id in active_chats:
                    active_chats[chat_id]["playing"] = False
                await callback_query.answer("Paused!")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "resume":
            try:
                await pytgcalls.resume_stream(chat_id)
                if chat_id in active_chats:
                    active_chats[chat_id]["playing"] = True
                await callback_query.answer("Resumed!")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "skip":
            try:
                await pytgcalls.leave_group_call(chat_id)
                await asyncio.sleep(1)

                if chat_id in queues and queues[chat_id]:
                    next_song = queues[chat_id].pop(0)
                    stream_url = get_audio_stream(next_song["id"])
                    if stream_url:
                        await pytgcalls.join_group_call(chat_id, AudioPiped(stream_url))
                        active_chats[chat_id] = {
                            "current": next_song,
                            "playing": True,
                            "loop": False,
                            "volume": DEFAULT_VOLUME,
                        }
                        await callback_query.answer("Skipped!")

                        try:
                            next_text = format_song_card(next_song, status="Now Playing")
                            await callback_query.message.edit_media(
                                media=InputMediaPhoto(
                                    media=next_song["thumbnail"] or "https://telegra.ph/file/placeholder.jpg",
                                    caption=next_text,
                                ),
                                reply_markup=get_song_card_keyboard(next_song, chat_id),
                            )
                        except:
                            pass
                else:
                    active_chats.pop(chat_id, None)
                    await callback_query.answer("Queue finished!")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "stop":
            try:
                if chat_id in queues:
                    queues[chat_id] = []
                active_chats.pop(chat_id, None)
                await pytgcalls.leave_group_call(chat_id)
                await callback_query.answer("Stopped!")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "vol_up":
            try:
                current_vol = active_chats.get(chat_id, {}).get("volume", 100)
                new_vol = min(current_vol + 10, 200)
                await pytgcalls.change_volume_call(chat_id, new_vol)
                active_chats[chat_id]["volume"] = new_vol
                await callback_query.answer(f"Volume: {new_vol}%")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "vol_down":
            try:
                current_vol = active_chats.get(chat_id, {}).get("volume", 100)
                new_vol = max(current_vol - 10, 1)
                await pytgcalls.change_volume_call(chat_id, new_vol)
                active_chats[chat_id]["volume"] = new_vol
                await callback_query.answer(f"Volume: {new_vol}%")
            except Exception as e:
                await callback_query.answer(f"Error: {e}", show_alert=True)

        elif action == "loop":
            if chat_id in active_chats:
                current_loop = active_chats[chat_id].get("loop", False)
                active_chats[chat_id]["loop"] = not current_loop
                status = "enabled" if not current_loop else "disabled"
                await callback_query.answer(f"Loop {status}!")
            else:
                await callback_query.answer("Nothing playing!", show_alert=True)

        elif action == "queue":
            queue_list = queues.get(chat_id, [])
            if queue_list:
                text = "Queue:\n"
                for i, song in enumerate(queue_list[:10], 1):
                    text += f"{i}. {song['title']}\n"
            else:
                text = "Queue is empty!"
            await callback_query.answer(text[:200], show_alert=True)

        elif action == "lyrics":
            await callback_query.answer(
                "Lyrics feature coming soon! Use @GeniusBot for now.",
                show_alert=True,
            )

        elif action == "shuffle":
            if chat_id in queues and queues[chat_id]:
                import random
                random.shuffle(queues[chat_id])
                await callback_query.answer("Queue shuffled!")
            else:
                await callback_query.answer("Queue empty!", show_alert=True)

        elif action == "clear":
            if chat_id in queues:
                queues[chat_id] = []
            await callback_query.answer("Queue cleared!")

        elif action == "player":
            if chat_id in active_chats:
                current = active_chats[chat_id]["current"]
                text = format_song_card(current, status="Now Playing")
                try:
                    await callback_query.message.edit_text(
                        text,
                        reply_markup=get_song_card_keyboard(current, chat_id),
                    )
                except:
                    pass
            await callback_query.answer()
