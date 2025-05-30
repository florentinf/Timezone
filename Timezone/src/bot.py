import os
import json
import discord
from discord.ext import commands
import pytz
from datetime import datetime
from dotenv import load_dotenv
import asyncio
from src.utils.timezone_parser import parse_timezone, get_current_time, list_timezone_examples

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=',', intents=intents)

# Constants
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'timezones.json')
COLORS = {
    'morning': 0xFFF8DC,   # Pastel yellow
    'afternoon': 0xADD8E6, # Pastel blue
    'evening': 0xCCCCFF,   # Pastel purple
    'night': 0xD3D3D3      # Pastel gray
}

# Ensure data directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Load or create timezone data
def load_timezone_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading timezone data file. Creating a new one.")
            return {}
    else:
        return {}

# Save timezone data
def save_timezone_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Get color based on time of day
def get_color_by_time(dt):
    hour = dt.hour
    if 6 <= hour < 12:
        return COLORS['morning']
    elif 12 <= hour < 18:
        return COLORS['afternoon']
    elif 18 <= hour < 24:
        return COLORS['evening']
    else:
        return COLORS['night']

# Validate timezone (using our enhanced parser)
def is_valid_timezone(tz_str):
    timezone_id, _, _ = parse_timezone(tz_str)
    return timezone_id is not None

@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')

@bot.command(name='tz')
async def timezone(ctx, member: discord.Member = None):
    timezones = load_timezone_data()
    server_id = str(ctx.guild.id)
    
    # Use mentioned member or message author
    target_user = member if member else ctx.author
    user_id = str(target_user.id)
    
    # Check if server exists in data
    if server_id not in timezones:
        timezones[server_id] = {}
    
    # Check if user has set timezone
    if user_id not in timezones[server_id]:
        examples = list_timezone_examples()
        msg = await ctx.send(f"{target_user.mention} hasn't set a timezone. "
                            f"Please set it with `,settz [timezone]`.\n"
                            f"Examples: {examples}")
        await asyncio.sleep(20)
        await msg.delete()
        return
    
    # Get user's timezone and current time
    timezone_str = timezones[server_id][user_id]
    try:
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        formatted_time = current_time.strftime('%I:%M %p, %A, %b %d')
        
        # Create embed with color based on time of day
        embed = discord.Embed(
            title=f"Current time for {target_user.display_name}",
            description=f"{formatted_time} ({timezone_str})",
            color=get_color_by_time(current_time)
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        msg = await ctx.send(f"Error displaying timezone for {target_user.mention}: {str(e)}")
        await asyncio.sleep(20)
        await msg.delete()

@bot.command(name='settz')
async def set_timezone(ctx, *, timezone_str: str = None):
    if not timezone_str:
        examples = list_timezone_examples()
        msg = await ctx.send(f"Please provide a timezone. Examples: {examples}")
        await asyncio.sleep(20)
        await msg.delete()
        return
    
    # Process and validate timezone using enhanced parser
    timezone_id, message, exact = parse_timezone(timezone_str)
    
    if not timezone_id:
        examples = list_timezone_examples()
        msg = await ctx.send(f"{message}\nExamples: {examples}")
        await asyncio.sleep(20)
        await msg.delete()
        return
    
    # Load data
    timezones = load_timezone_data()
    server_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    
    # Initialize server data if not exists
    if server_id not in timezones:
        timezones[server_id] = {}
    
    # Set timezone
    timezones[server_id][user_id] = timezone_id
    save_timezone_data(timezones)
    
    # Confirmation message with additional info if timezone was guessed
    confirmation = f"Timezone set to {timezone_id}."
    if message:
        confirmation += f" {message}"
    
    msg = await ctx.send(confirmation)
    await asyncio.sleep(10)
    await msg.delete()

def main():
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()