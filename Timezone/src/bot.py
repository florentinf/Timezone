import os
import json
import discord
from discord.ext import commands
import pytz
from datetime import datetime
from dotenv import load_dotenv
import asyncio
from typing import Optional, List
from src.utils.timezone_parser import parse_timezone, get_current_time, list_timezone_examples

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))  # Default to 0 if not set

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=',', intents=intents)

# Constants
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'timezones.json')
SERVER_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'server_data.json')
COLORS = {
    'morning': 0xFFF8DC,   # Pastel yellow
    'afternoon': 0xADD8E6, # Pastel blue
    'evening': 0xCCCCFF,   # Pastel purple
    'night': 0xD3D3D3,     # Pastel gray
    'admin': 0xFF5733      # Orange-red for admin commands
}

# Ensure data directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Load or create server data (for tracking banned servers)
def load_server_data():
    if os.path.exists(SERVER_DATA_FILE):
        try:
            with open(SERVER_DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading server data file. Creating a new one.")
            return {"banned_servers": []}
    else:
        return {"banned_servers": []}

# Save server data
def save_server_data(data):
    with open(SERVER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

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

# Check if user is the bot owner
def is_owner():
    async def predicate(ctx):
        return ctx.author.id == BOT_OWNER_ID
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    
    # Check for banned servers and leave them
    server_data = load_server_data()
    banned_servers = server_data.get("banned_servers", [])
    
    for guild in bot.guilds:
        if str(guild.id) in banned_servers:
            print(f"Leaving banned server: {guild.name} (ID: {guild.id})")
            try:
                await guild.leave()
            except Exception as e:
                print(f"Error leaving server {guild.id}: {e}")
    
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

# Owner-only commands for server management
@bot.command(name='servers')
@is_owner()
async def list_servers(ctx):
    """Lists all servers the bot is in (Owner only)"""
    if ctx.author.id != BOT_OWNER_ID:
        return
    
    embed = discord.Embed(
        title="Server List",
        description=f"Currently in {len(bot.guilds)} servers",
        color=COLORS['admin']
    )
    
    for i, guild in enumerate(sorted(bot.guilds, key=lambda g: g.member_count, reverse=True)):
        if i < 25:  # Discord embed field limit
            member_count = guild.member_count
            embed.add_field(
                name=f"{guild.name}",
                value=f"ID: {guild.id}\nMembers: {member_count}\nOwner: {guild.owner}",
                inline=(i % 2 == 0)
            )
    
    if len(bot.guilds) > 25:
        embed.set_footer(text=f"Showing 25/{len(bot.guilds)} servers")
    
    await ctx.send(embed=embed)

@bot.command(name='leaveserver')
@is_owner()
async def leave_server(ctx, server_id: int):
    """Leave a server by ID (Owner only)"""
    if ctx.author.id != BOT_OWNER_ID:
        return
    
    guild = bot.get_guild(server_id)
    if guild:
        guild_name = guild.name
        try:
            await guild.leave()
            await ctx.send(f"Successfully left server: {guild_name} (ID: {server_id})")
        except Exception as e:
            await ctx.send(f"Error leaving server: {str(e)}")
    else:
        await ctx.send(f"Could not find a server with ID {server_id}")

@bot.command(name='banserver')
@is_owner()
async def ban_server(ctx, server_id: int):
    """Ban a server by ID and leave it (Owner only)"""
    if ctx.author.id != BOT_OWNER_ID:
        return
    
    server_data = load_server_data()
    if str(server_id) not in server_data["banned_servers"]:
        server_data["banned_servers"].append(str(server_id))
        save_server_data(server_data)
    
    guild = bot.get_guild(server_id)
    if guild:
        guild_name = guild.name
        try:
            await guild.leave()
            await ctx.send(f"Successfully banned and left server: {guild_name} (ID: {server_id})")
        except Exception as e:
            await ctx.send(f"Server banned but error leaving server: {str(e)}")
    else:
        await ctx.send(f"Server ID {server_id} banned. The bot will leave it once it encounters the server.")

@bot.command(name='unbanserver')
@is_owner()
async def unban_server(ctx, server_id: int):
    """Unban a server by ID (Owner only)"""
    if ctx.author.id != BOT_OWNER_ID:
        return
    
    server_data = load_server_data()
    if str(server_id) in server_data["banned_servers"]:
        server_data["banned_servers"].remove(str(server_id))
        save_server_data(server_data)
        await ctx.send(f"Successfully unbanned server ID {server_id}")
    else:
        await ctx.send(f"Server ID {server_id} was not banned")

@bot.command(name='bannedservers')
@is_owner()
async def list_banned_servers(ctx):
    """List all banned server IDs (Owner only)"""
    if ctx.author.id != BOT_OWNER_ID:
        return
    
    server_data = load_server_data()
    banned_servers = server_data.get("banned_servers", [])
    
    if not banned_servers:
        await ctx.send("No servers are banned.")
        return
    
    embed = discord.Embed(
        title="Banned Servers",
        description=f"{len(banned_servers)} servers are banned",
        color=COLORS['admin']
    )
    
    for i, server_id in enumerate(banned_servers):
        guild = bot.get_guild(int(server_id))
        name = guild.name if guild else "Unknown Server"
        embed.add_field(name=f"Server {i+1}", value=f"ID: {server_id}\nName: {name}", inline=False)
    
    await ctx.send(embed=embed)

@bot.event
async def on_guild_join(guild):
    """Check if a server is banned when joining"""
    server_data = load_server_data()
    banned_servers = server_data.get("banned_servers", [])
    
    if str(guild.id) in banned_servers:
        print(f"Leaving banned server: {guild.name} (ID: {guild.id})")
        try:
            await guild.leave()
        except Exception as e:
            print(f"Error leaving banned server {guild.id}: {e}")
    else:
        print(f"Joined new server: {guild.name} (ID: {guild.id})")

def main():
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()