"""
Start Plugin for Hexa Music Bot
"""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import BOT_NAME, BOT_USERNAME, OWNER_ID, START_MSG, HELP_MSG


def setup_start_handlers(app):

    @app.on_message(filters.command("start"))
    async def start_handler(_, message: Message):
        user = message.from_user

        from plugins.admin import stats
        stats["total_users"].add(user.id)

        if message.chat.type in ["group", "supergroup"]:
            stats["total_groups"].add(message.chat.id)

        buttons = [
            [
                InlineKeyboardButton("Add to Group", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}?startgroup=true"),
                InlineKeyboardButton("Updates", url="https://t.me/your_channel"),
            ],
            [
                InlineKeyboardButton("Help", callback_data="help"),
                InlineKeyboardButton("Developer", url=f"tg://user?id={OWNER_ID}"),
            ],
        ]

        if user.id == OWNER_ID:
            buttons.append([InlineKeyboardButton("Admin Panel", callback_data="admin_panel")])

        await message.reply_text(
            START_MSG.format(bot_name=BOT_NAME),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
        )


    @app.on_message(filters.command("help"))
    async def help_handler(_, message: Message):
        await message.reply_text(
            HELP_MSG,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="start")],
            ]),
        )


    @app.on_callback_query()
    async def callback_handler(_, callback_query):
        data = callback_query.data
        user_id = callback_query.from_user.id

        if data == "help":
            await callback_query.message.edit_text(
                HELP_MSG,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="start")],
                ]),
            )

        elif data == "start":
            await callback_query.message.edit_text(
                START_MSG.format(bot_name=BOT_NAME),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Add to Group", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}?startgroup=true"),
                        InlineKeyboardButton("Updates", url="https://t.me/your_channel"),
                    ],
                    [
                        InlineKeyboardButton("Help", callback_data="help"),
                        InlineKeyboardButton("Developer", url=f"tg://user?id={OWNER_ID}"),
                    ],
                ]),
                disable_web_page_preview=True,
            )

        elif data == "admin_panel":
            if user_id != OWNER_ID:
                return await callback_query.answer("Owner only!", show_alert=True)

            from plugins.admin import SUDO_USERS, banned_users
            await callback_query.message.edit_text(
                f"Admin Panel\n\n"
                f"Owner: {OWNER_ID}\n"
                f"Sudo Users: {len(SUDO_USERS)}\n"
                f"Banned Users: {len(banned_users)}\n\n"
                f"Commands:\n"
                f"/promo <msg> - Broadcast to promo groups\n"
                f"/broadcast <msg> - Broadcast to ALL groups\n"
                f"/stats - Bot statistics\n"
                f"/ban <user_id> - Ban user\n"
                f"/unban <user_id> - Unban user\n"
                f"/auth <user_id> - Add admin\n"
                f"/unauth <user_id> - Remove admin",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="start")],
                ]),
            )

        elif data == "pause":
            from plugins.music import active_chats
            chat_id = callback_query.message.chat.id
            if chat_id in active_chats:
                await callback_query.answer("Use /pause command instead", show_alert=True)

        await callback_query.answer()
