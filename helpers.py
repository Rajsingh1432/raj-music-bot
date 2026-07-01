"""
🛠️ Utility Functions
"""

import asyncio
import random
import time
from datetime import datetime

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def format_duration(seconds):
    """Format seconds to mm:ss or hh:mm:ss"""
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    if seconds >= 3600:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def format_bytes(size):
    """Format bytes to human readable"""
    power = 2**10
    n = 0
    units = ['B', 'KB', 'MB', 'GB']
    while size > power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"


def get_progress_bar(percentage):
    """Create a progress bar"""
    filled = int(percentage / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty


def get_music_control_keyboard():
    """Inline keyboard for music controls"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏮", callback_data="prev"),
            InlineKeyboardButton("⏸", callback_data="pause"),
            InlineKeyboardButton("▶️", callback_data="resume"),
            InlineKeyboardButton("⏭", callback_data="skip"),
        ],
        [
            InlineKeyboardButton("🔉", callback_data="vol_down"),
            InlineKeyboardButton("🔊", callback_data="vol_up"),
            InlineKeyboardButton("🔄", callback_data="loop"),
            InlineKeyboardButton("🔀", callback_data="shuffle"),
        ],
        [
            InlineKeyboardButton("📋 Queue", callback_data="show_queue"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop"),
        ],
    ])


def get_admin_keyboard():
    """Admin control keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("👥 Manage Admins", callback_data="manage_admins"),
            InlineKeyboardButton("🚫 Banned Users", callback_data="banned_users"),
        ],
    ])


def get_promo_keyboard():
    """Promo message keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Play Music", url="https://t.me/YourBot?startgroup=true"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/YourChannel"),
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/YourUsername"),
        ],
    ])


class Timer:
    """Simple timer for rate limiting"""
    def __init__(self):
        self.timers = {}

    def check(self, key, cooldown):
        """Check if cooldown has passed"""
        now = time.time()
        if key in self.timers:
            if now - self.timers[key] < cooldown:
                return False, int(cooldown - (now - self.timers[key]))
        self.timers[key] = now
        return True, 0


# Global timer instance
timer = Timer()
