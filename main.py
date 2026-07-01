"""
🎵 V3NOM MUSIC PRO BOT
Advanced Telegram Music Bot with Voice Chat Support
Features: YouTube Play, Queue, Admin Controls, Broadcast/Promo

Author: Your Name
Version: 2.0 Pro
"""

import os
import sys
import asyncio
import logging

from pyrogram import Client, idle
from pytgcalls import PyTgCalls

# Import config
from config import (
    API_ID, API_HASH, BOT_TOKEN, SESSION_STRING,
    BOT_NAME, OWNER_ID
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ==========================
# BOT CLIENT
# ==========================
app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=100,
)

# ==========================
# USER CLIENT (for Voice Chat)
# ==========================
user = None
pytgcalls = None

if SESSION_STRING and SESSION_STRING != "YOUR_SESSION_STRING_HERE":
    try:
        user = Client(
            "music_user",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            workers=100,
        )
        pytgcalls = PyTgCalls(user)
        logger.info("✅ User client initialized!")
    except Exception as e:
        logger.error(f"❌ Failed to init user client: {e}")
        user = None
        pytgcalls = None
else:
    logger.warning("⚠️ No SESSION_STRING found! Voice chat features disabled.")
    logger.warning("Run: python generate_session.py")

# ==========================
# LOAD PLUGINS
# ==========================
from plugins.start import setup_start_handlers
from plugins.music import setup_music_handlers
from plugins.admin import setup_admin_handlers

setup_start_handlers(app)

if pytgcalls:
    setup_music_handlers(app, pytgcalls)
else:
    logger.warning("⚠️ Music handlers not loaded - no user session")

setup_admin_handlers(app)

# ==========================
# MAIN FUNCTION
# ==========================
async def main():
    """Start the bot"""
    logger.info("=" * 50)
    logger.info(f"🎵 {BOT_NAME}")
    logger.info("=" * 50)

    # Start bot
    await app.start()
    logger.info("✅ Bot client started!")

    # Start user client & PyTgCalls
    if user and pytgcalls:
        await user.start()
        await pytgcalls.start()
        logger.info("✅ User client & PyTgCalls started!")
        logger.info(f"🎤 Assistant ID: {(await user.get_me()).id}")

    # Get bot info
    me = await app.get_me()
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"👑 Owner: {OWNER_ID}")
    logger.info("🚀 Bot is running!")
    logger.info("=" * 50)

    # Keep running
    await idle()

    # Shutdown
    logger.info("🛑 Shutting down...")
    await app.stop()
    if user:
        await user.stop()
    if pytgcalls:
        await pytgcalls.stop()
    logger.info("✅ Bot stopped!")


if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
