"""
⚙️ CONFIGURATION FILE
🔒 IMPORTANT: Is file ko kisi ke saath share mat karein!
"""

import os

# ==========================
# TELEGRAM API CREDENTIALS
# ==========================
# Step 1: my.telegram.org pe jao → API development tools → Create App
API_ID = int(os.environ.get("API_ID", "21505035"))  # <-- Aapka API_ID
API_HASH = os.environ.get("API_HASH", "32da80bb9e2dadc153337b8fb79350be")  # <-- Aapka API_HASH

# Step 2: @BotFather pe jao → /newbot → Name & Username do → Token copy karo
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8903619328:AAHKGiIPO5-AYKTy8JOg4XDQ8iqwo8ybfgk")  # <-- Aapka Bot Token

# Step 3: python generate_session.py run karo → StringSession milega
SESSION_STRING = os.environ.get("SESSION_STRING", "BQFIJAsAohY1Jc0JsLAH43GMUIjTq9Sq0Vwju-cmDk69RXuImlkgw-Prd3fCbkyOs_MeFgGE05zhd1vIU8H6SIyccnRqG3ImFZm2qmSnsGWcelh-OLW2-NWBjjwy3e2QKmyIju7OlSPXBILGzLjB12ah5Nrje0VQd0kNVpNq9KLLeGLYghuelh0dFYAvMpg6D75ldzaSdQRHrr5xVgaYoJvCob5yMIbETupx_Qk3oWx-Oc1wO_Oy1ZXqdL8WY9QGoXgJ4mMQwj5dB_0Jsk7v2O2AtaI0N_tBevlXY9H99a_1dydGp9hBNX4InpFQHUqgnl8xDOPhxBY1YBLGqezGx6leRisLzAAAAAGL6VdaAA")  # <-- User Session

# ==========================
# BOT SETTINGS
# ==========================
BOT_NAME = "🎵 Hexa Music Bot"
BOT_USERNAME = "Hexamusicc_bot"  # <-- Aapka bot ka username (WITHOUT @)
OWNER_ID = 1731816712  # <-- Aapka Telegram User ID (numeric)

# Admin IDs (Inke alawa koi admin command use nahi kar sakta)
SUDO_USERS = [1731816712]  # Yahan aur admin IDs add kar sakte ho

# ==========================
# BUTTON LINKS (CUSTOMIZE KARO!)
# ==========================
# Yeh links har song card mein dikhenge
OWNER_USERNAME = "its_raj_king"           # <-- Aapka Telegram username (bina @ ke)
OWNER_URL = "https://t.me/its_raj_king"

CHANNEL_USERNAME = "ITSRAJCHEATS"          # <-- Aapka channel username (bina @ ke)
CHANNEL_URL = "https://t.me/ITSRAJCHEATS"

SUPPORT_GROUP = "YourSupportGroup"        # <-- Aapka support group username
SUPPORT_URL = "https://t.me/+lnlWppOvT_Y0Zjg1"

# Bot add karne ka link
ADD_BOT_URL = "https://t.me/Hexamusicc_bot?startgroup=true"

# ==========================
# PROMO / BROADCAST SETTINGS
# ==========================
# Jis group/channel mein promo karna hai, unki IDs yahan add karo
PROMO_GROUPS = []  # Example: [-1001234567890, -1009876543210]

# Promo message cooldown (seconds)
PROMO_COOLDOWN = 300  # 5 minutes

# ==========================
# MUSIC SETTINGS
# ==========================
MAX_QUEUE_SIZE = 50  # Ek group mein max kitne songs queue mein
MAX_DOWNLOAD_SIZE = 100  # MB mein (100MB max)

# Default volume
DEFAULT_VOLUME = 100

# ==========================
# DATABASE (Optional - for stats)
# ==========================
# Agar aapko user stats, played songs history chahiye toh MongoDB use karein
MONGO_URI = os.environ.get("MONGO_URI", "")  # Optional

# ==========================
# MESSAGES
# ==========================
START_MSG = """
🎵 **Welcome to {bot_name}!** 🎵

I am your personal Music Assistant with Voice Chat support!

📌 **Features:**
• 🎶 Play YouTube songs in Voice Chat
• 📋 Smart Queue System
• 🔊 Volume Control
• 👑 Admin Only Controls
• 📢 Broadcast/Promo Support

🛠 **Commands:**
`/play` - Play a song
`/pause` - Pause music
`/resume` - Resume music
`/skip` - Skip song
`/stop` - Stop & clear queue
`/queue` - Show queue
`/volume` - Set volume
`/promo` - Broadcast message (Admin only)

💡 **Tip:** Add me to your group & make me admin with voice permissions!
"""

HELP_MSG = """
📖 **Command Guide**

🎵 **Music Commands:**
• `/play <song>` - Search & play
• `/play <youtube link>` - Play direct link
• `/pause` - Pause playback
• `/resume` - Resume playback
• `/skip` - Skip current
• `/stop` - Stop & clear
• `/queue` - View queue
• `/volume <1-200>` - Set volume
• `/shuffle` - Shuffle queue
• `/loop` - Loop current song

👑 **Admin Commands:**
• `/promo <message>` - Broadcast to all groups
• `/stats` - Bot statistics
• `/ban <user_id>` - Ban user
• `/unban <user_id>` - Unban user
• `/auth` - Authorize user as admin
• `/unauth` - Remove admin

⚙️ **VC Commands:**
• `/joinvc` - Join voice chat
• `/leavevc` - Leave voice chat
"""
