import discord
import requests
import os
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# Load environment variables
# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "http://localhost:8001/api/chat")
# Optional: Restrict to specific channels (comma separated)
ALLOWED_CHANNELS = os.getenv("DISCORD_ALLOWED_CHANNELS", "")

if not DISCORD_TOKEN:
    logger.error("Error: DISCORD_BOT_TOKEN environment variable not set.")
    logger.error("Please set it in your .env file or export it.")
    exit(1)

# Parse allowed channels
allowed_channel_ids = []
if ALLOWED_CHANNELS:
    try:
        allowed_channel_ids = [int(id.strip()) for id in ALLOWED_CHANNELS.split(",") if id.strip()]
        logger.info(f"Restricting to channels: {allowed_channel_ids}")
    except ValueError:
        logger.error("Error: DISCORD_ALLOWED_CHANNELS must be a comma-separated list of IDs.")

# Discord Intents
intents = discord.Intents.default()
intents.message_content = True # Required to read message content

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Check allowed channels
    if allowed_channel_ids and message.channel.id not in allowed_channel_ids:
        return
        
    # Ignore empty messages
    if not message.content:
        return

    logger.info(f"Received message from {message.author}: {message.content}")

    # Send typing indicator
    async with message.channel.typing():
        try:
            # Prepare payload for OpenClaw
            payload = {
                "message": message.content,
                "sender": f"discord:{message.author.name}"
            }
            
            # Call OpenClaw API (run in executor to avoid blocking event loop)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(OPENCLAW_API_URL, json=payload)
            )
            
            if response.status_code == 200:
                data = response.json()
                reply_text = data.get("response", "I'm sorry, I couldn't process that.")
                
                # Split functionality for long messages (Discord limit is 2000 chars)
                if len(reply_text) > 2000:
                   for i in range(0, len(reply_text), 2000):
                       await message.channel.send(reply_text[i:i+2000])
                else:
                    await message.channel.send(reply_text)
                    
            else:
                logger.error(f"OpenClaw API Error: {response.status_code} - {response.text}")
                await message.channel.send("I'm having trouble connecting to my brain right now.")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await message.channel.send("Something went wrong while processing your request.")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
