"""
Session String Generator for Hexa Music Bot
"""

from pyrogram import Client

print("=" * 50)
print("Session String Generator")
print("=" * 50)
print()
print("IMPORTANT:")
print("- Real phone number dalna hoga")
print("- Yeh aapka personal account use karega")
print("- Isse bot voice chat join kar payega")
print()

API_ID = input("Enter your API_ID: ").strip()
API_HASH = input("Enter your API_HASH: ").strip()

if not API_ID or not API_HASH:
    print("ERROR: API_ID aur API_HASH required hain!")
    exit(1)

print("Generating session...")

app = Client(
    "session_generator",
    api_id=int(API_ID),
    api_hash=API_HASH,
    in_memory=True
)

async def main():
    async with app:
        session_string = await app.export_session_string()
        print("=" * 50)
        print("SESSION STRING GENERATED!")
        print("=" * 50)
        print(f"Your Session String: {session_string}")
        print("Isko safe rakhiye! Kisi ke saath share mat karein!")
        print("Isko config.py ke SESSION_STRING mein paste karein")
        print("=" * 50)

app.run(main())
