import discord
from discord.ext import commands, tasks
import os
import traceback
from flask import Flask
import sys
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app for uptime pings (Render)
app = Flask(__name__)
bot_name = "Loading..."

@app.route("/")
def home():
    return f"✅ Bot {bot_name} is operational"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Token check
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Missing TOKEN in environment")

# Discord Bot
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.session = None

        # Define task here — AFTER method is defined
        self.update_status = self._create_status_loop()

    def _create_status_loop(self):
        @tasks.loop(minutes=5)
        async def loop():
             try:
                  activity = discord.Game("Clutch Info 📑")
                  await self.change_presence(status=discord.Status.dnd, activity=activity)
               except Exception as e:
                   print(f"⚠️ Failed to update status: {e}")        
        return loop

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()

        # Load cog(s)
        try:
            await self.load_extension("cogs.infoCommands")
            print("✅ Loaded InfoCommands cog")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
            traceback.print_exc()

        await self.tree.sync()
        self.update_status.start()

    async def on_ready(self):
        global bot_name
        bot_name = str(self.user)
        print(f"\n🔗 Logged in as {bot_name}")
        print(f"🌐 Serving {len(self.guilds)} servers")

        # Set DND + activity (one-time)
        activity = discord.Game("Clutch Info 📑")
        await self.change_presence(status=discord.Status.dnd, activity=activity)

        # Start Flask server on Render
        if os.environ.get("RENDER"):
            import threading
            threading.Thread(target=run_flask, daemon=True).start()
            print("🚀 Flask server started")

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

# Run bot
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

if __name__ == "__main__":
    if os.environ.get("RENDER"):
        asyncio.run(main())
    else:
        bot = Bot()
        bot.run(TOKEN)
