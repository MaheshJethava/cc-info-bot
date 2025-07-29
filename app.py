import discord
from discord.ext import commands, tasks
import os
import traceback
from flask import Flask
import sys
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Flask app setup for uptime pings
app = Flask(__name__)
bot_name = "Loading..."

@app.route('/')
def home():
    return f"✅ Bot {bot_name} is operational"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Get bot token from environment
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Missing TOKEN in environment")

# Define custom bot class
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.session = None
        self.update_status = tasks.loop(minutes=5)(self._update_status)

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        # Load extension
        try:
            await self.load_extension("cogs.infoCommands")
            print("✅ Successfully loaded InfoCommands cog")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
            traceback.print_exc()

        await self.tree.sync()
        self.update_status.start()

    async def _update_status(self):
        try:
            activity = discord.Activity(type=discord.ActivityType.playing, name="Clutch Info 📑")
            await self.change_presence(activity=activity, status=discord.Status.dnd)
        except Exception as e:
            print(f"⚠️ Failed to update status: {e}")

    async def on_ready(self):
        global bot_name
        bot_name = str(self.user)
        print(f"\n🔗 Logged in as {bot_name}")
        print(f"🌐 Serving {len(self.guilds)} servers")

        # Only start Flask on Render or Replit
        if os.environ.get("RENDER") or os.environ.get("REPL_ID"):
            import threading
            threading.Thread(target=run_flask, daemon=True).start()
            print("🚀 Flask server started")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

# Main bot runner
async def main():
    bot = Bot()
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        print(f"💥 Critical error: {e}")
        traceback.print_exc()
        await bot.close()

# Entry point
if __name__ == "__main__":
    if os.environ.get("RENDER") or os.environ.get("REPL_ID"):
        asyncio.run(main())
    else:
        bot = Bot()
        bot.run(TOKEN)
