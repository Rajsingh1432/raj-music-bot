"""
Admin Plugin for Hexa Music Bot
"""

import asyncio
import time
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from config import SUDO_USERS, OWNER_ID, PROMO_GROUPS, PROMO_COOLDOWN
from utils.helpers import get_admin_keyboard, timer

banned_users = set()
stats = {
    "total_plays": 0,
    "total_users": set(),
    "total_groups": set(),
    "start_time": time.time(),
}


def is_sudo(_, __, message: Message):
    return message.from_user.id in SUDO_USERS or message.from_user.id == OWNER_ID


def setup_admin_handlers(app):

    @app.on_message(filters.command("promo") & filters.create(is_sudo))
    async def promo_handler(_, message: Message):
        if len(message.command) < 2 and not message.reply_to_message:
            return await message.reply_text(
                "Usage:\n"
                "/promo <your message>\n"
                "Reply to any message with /promo"
            )

        can_send, remaining = timer.check("promo", PROMO_COOLDOWN)
        if not can_send:
            return await message.reply_text(
                f"Cooldown active! Wait {remaining} seconds before next promo."
            )

        if message.reply_to_message:
            promo_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        else:
            promo_text = " ".join(message.command[1:])

        if not promo_text:
            return await message.reply_text("Message is empty!")

        full_text = f"Broadcast\n\n{promo_text}\n\n"
        full_text += "---\n"
        full_text += "Powered by Hexa Music Bot\n"
        full_text += f"Add me to your group: https://t.me/{app.me.username}?startgroup=true"

        if not PROMO_GROUPS:
            return await message.reply_text(
                "No promo groups configured! Add group IDs to config.py -> PROMO_GROUPS"
            )

        sent_count = 0
        failed_count = 0
        status_msg = await message.reply_text("Sending promo...")

        for group_id in PROMO_GROUPS:
            try:
                await app.send_message(group_id, full_text, disable_web_page_preview=True)
                sent_count += 1
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await app.send_message(group_id, full_text)
                    sent_count += 1
                except:
                    failed_count += 1
            except Exception as e:
                print(f"[PROMO ERROR] {group_id}: {e}")
                failed_count += 1

        await status_msg.edit(
            f"Promo Sent!\n\n"
            f"Successful: {sent_count}\n"
            f"Failed: {failed_count}\n"
            f"Total Groups: {len(PROMO_GROUPS)}"
        )


    @app.on_message(filters.command("broadcast") & filters.create(is_sudo))
    async def broadcast_handler(_, message: Message):
        if len(message.command) < 2 and not message.reply_to_message:
            return await message.reply_text(
                "Usage:\n"
                "/broadcast <message>\n"
                "Reply to any message with /broadcast"
            )

        if message.reply_to_message:
            broadcast_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        else:
            broadcast_text = " ".join(message.command[1:])

        if not broadcast_text:
            return await message.reply_text("Message is empty!")

        status_msg = await message.reply_text("Getting chat list...")

        chats = []
        async for dialog in app.get_dialogs():
            if dialog.chat.type in ["group", "supergroup"]:
                chats.append(dialog.chat.id)

        await status_msg.edit(f"Broadcasting to {len(chats)} groups...")

        sent = 0
        failed = 0

        for chat_id in chats:
            try:
                await app.send_message(chat_id, broadcast_text)
                sent += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                failed += 1
                print(f"[BROADCAST ERROR] {chat_id}: {e}")

        await status_msg.edit(
            f"Broadcast Complete!\n\n"
            f"Sent: {sent}\n"
            f"Failed: {failed}\n"
            f"Total: {len(chats)}"
        )


    @app.on_message(filters.command("stats") & filters.create(is_sudo))
    async def stats_handler(_, message: Message):
        uptime = time.time() - stats["start_time"]
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        await message.reply_text(
            f"Bot Statistics\n\n"
            f"Uptime: {uptime_str}\n"
            f"Total Plays: {stats['total_plays']}\n"
            f"Unique Users: {len(stats['total_users'])}\n"
            f"Total Groups: {len(stats['total_groups'])}\n\n"
            f"Owner: {OWNER_ID}\n"
            f"Sudo Users: {len(SUDO_USERS)}",
            reply_markup=get_admin_keyboard(),
        )


    @app.on_message(filters.command("ban") & filters.create(is_sudo))
    async def ban_handler(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /ban <user_id>")

        try:
            user_id = int(message.command[1])
            banned_users.add(user_id)
            await message.reply_text(f"User {user_id} banned!")
        except ValueError:
            await message.reply_text("Invalid user ID!")


    @app.on_message(filters.command("unban") & filters.create(is_sudo))
    async def unban_handler(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /unban <user_id>")

        try:
            user_id = int(message.command[1])
            banned_users.discard(user_id)
            await message.reply_text(f"User {user_id} unbanned!")
        except ValueError:
            await message.reply_text("Invalid user ID!")


    @app.on_message(filters.command("auth") & filters.create(is_sudo))
    async def auth_handler(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /auth <user_id>")

        try:
            user_id = int(message.command[1])
            if user_id not in SUDO_USERS:
                SUDO_USERS.append(user_id)
                await message.reply_text(f"User {user_id} is now admin!")
            else:
                await message.reply_text("User is already admin!")
        except ValueError:
            await message.reply_text("Invalid user ID!")


    @app.on_message(filters.command("unauth") & filters.create(is_sudo))
    async def unauth_handler(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /unauth <user_id>")

        try:
            user_id = int(message.command[1])
            if user_id in SUDO_USERS and user_id != OWNER_ID:
                SUDO_USERS.remove(user_id)
                await message.reply_text(f"User {user_id} removed from admin!")
            elif user_id == OWNER_ID:
                await message.reply_text("Cannot remove owner!")
            else:
                await message.reply_text("User is not admin!")
        except ValueError:
            await message.reply_text("Invalid user ID!")


    @app.on_message(filters.command("admin") & filters.create(is_sudo))
    async def admin_panel_handler(_, message: Message):
        await message.reply_text(
            f"Admin Panel\n\n"
            f"Owner: {OWNER_ID}\n"
            f"Sudo Users: {len(SUDO_USERS)}\n"
            f"Banned Users: {len(banned_users)}\n\n"
            f"Use buttons below to manage:",
            reply_markup=get_admin_keyboard(),
        )
