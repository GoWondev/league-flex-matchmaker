import os
import discord
from discord import app_commands
import sqlite3
import random
import urllib.parse

# --- 1. Database & First-Time Setup ---
def init_and_get_credentials():
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            discord_id INTEGER PRIMARY KEY,
            ign TEXT,
            primary_role TEXT,
            secondary_role TEXT,
            is_admin INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')
    
    # Check if credentials already exist
    cursor.execute("SELECT setting_value FROM server_settings WHERE setting_key = 'discord_token'")
    token_row = cursor.fetchone()
    cursor.execute("SELECT setting_value FROM server_settings WHERE setting_key = 'guild_id'")
    guild_row = cursor.fetchone()
    
    # If they are missing, trigger the Setup Wizard
    if not token_row or not guild_row:
        print("=====================================")
        print("  FLEX MATCHMAKER - FIRST TIME SETUP ")
        print("=====================================")
        print("No configuration found. Let's set up your bot!")
        token = input("Enter your Discord Bot Token: ").strip()
        guild = input("Enter your Server (Guild) ID: ").strip()
        
        cursor.execute("INSERT OR REPLACE INTO server_settings (setting_key, setting_value) VALUES ('discord_token', ?)", (token,))
        cursor.execute("INSERT OR REPLACE INTO server_settings (setting_key, setting_value) VALUES ('guild_id', ?)", (guild,))
        
        # Set default region to EUW while we are here
        cursor.execute("INSERT OR IGNORE INTO server_settings (setting_key, setting_value) VALUES ('region', 'euw')")
        
        conn.commit()
        print("\nCredentials saved to database! Starting bot...\n")
    else:
        token = token_row[0]
        guild = guild_row[0]
        
    conn.close()
    return token, int(guild)

# Fetch the credentials securely from the local database
TOKEN, GUILD_ID = init_and_get_credentials()

# --- 2. Bot Setup ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        MY_GUILD = discord.Object(id=GUILD_ID) 
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        print(f"Synced slash commands instantly to test server!")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = MyBot()

# --- 3. The Register Command ---
@bot.tree.command(name="register", description="Set up your Flex profile!")
@app_commands.describe(
    ign="Your exact in-game name (for OP.GG)",
    primary="Your main role",
    secondary="Your backup role"
)
@app_commands.choices(primary=[
    app_commands.Choice(name="Top", value="Top"),
    app_commands.Choice(name="Jungle", value="Jungle"),
    app_commands.Choice(name="Mid", value="Mid"),
    app_commands.Choice(name="ADC", value="ADC"),
    app_commands.Choice(name="Support", value="Support"),
], secondary=[
    app_commands.Choice(name="Top", value="Top"),
    app_commands.Choice(name="Jungle", value="Jungle"),
    app_commands.Choice(name="Mid", value="Mid"),
    app_commands.Choice(name="ADC", value="ADC"),
    app_commands.Choice(name="Support", value="Support"),
    app_commands.Choice(name="Fill", value="Fill"),
])
async def register(interaction: discord.Interaction, ign: str, primary: app_commands.Choice[str], secondary: app_commands.Choice[str]):
    
    # Check if the person using the command is a Discord Server Admin
    is_admin = 1 if interaction.permissions.administrator else 0

    # Save to the database
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    
    # INSERT OR REPLACE means if they run the command again, it just updates their existing profile
    cursor.execute('''
        INSERT OR REPLACE INTO players (discord_id, ign, primary_role, secondary_role, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', (interaction.user.id, ign, primary.value, secondary.value, is_admin))
    
    conn.commit()
    conn.close()

    # Reply to the user
    await interaction.response.send_message(
        f"Successfully registered **{ign}**!\n"
        f"**Primary:** {primary.value} | **Secondary:** {secondary.value}"
    )

# --- 4. The Active Queue ---
active_queue = set()

@bot.tree.command(name="queue", description="Join or leave the active matchmaking queue")
@app_commands.choices(action=[
    app_commands.Choice(name="Join", value="join"),
    app_commands.Choice(name="Leave", value="leave"),
    app_commands.Choice(name="View", value="view")
])
async def queue_manager(interaction: discord.Interaction, action: app_commands.Choice[str]):
    if action.value == "join":
        active_queue.add(interaction.user.id)
        await interaction.response.send_message(f"You've joined the queue! ({len(active_queue)} players waiting)")
    
    elif action.value == "leave":
        active_queue.discard(interaction.user.id)
        await interaction.response.send_message(f"You left the queue. ({len(active_queue)} players waiting)")
    
    elif action.value == "view":
        await interaction.response.send_message(f"There are currently **{len(active_queue)}** players in queue.")

# --- 5. Dynamic Region Setting ---
@bot.tree.command(name="set_region", description="[ADMIN ONLY] Change the OP.GG region for the server")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(region=[
    app_commands.Choice(name="EU West (EUW)", value="euw"),
    app_commands.Choice(name="North America (NA)", value="na"),
    app_commands.Choice(name="EU Nordic & East (EUNE)", value="eune"),
    app_commands.Choice(name="Korea (KR)", value="kr"),
    app_commands.Choice(name="Oceania (OCE)", value="oce"),
])
async def set_region(interaction: discord.Interaction, region: app_commands.Choice[str]):
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE server_settings SET setting_value = ? WHERE setting_key = 'region'", (region.value,))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"OP.GG multi-search region successfully updated to **{region.name}**!")

# --- 6. Generate Team Algorithm ---
@bot.tree.command(name="generate_team", description="[ADMIN ONLY] Drafts a 5-man team from the queue")
@app_commands.checks.has_permissions(administrator=True)
async def generate_team(interaction: discord.Interaction):
    if len(active_queue) < 5:
        await interaction.response.send_message(f"Not enough players in queue! We need at least 5, but only have {len(active_queue)}.", ephemeral=True)
        return

    # 1. Fetch profiles of everyone in the queue from the database
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(active_queue))
    cursor.execute(f"SELECT discord_id, ign, primary_role, secondary_role, is_admin FROM players WHERE discord_id IN ({placeholders})", tuple(active_queue))
    queued_players = cursor.fetchall()

    # If someone in the queue never used /register, they won't be in the database
    if len(queued_players) < 5:
        await interaction.response.send_message("Some players in the queue haven't used `/register` yet!", ephemeral=True)
        conn.close()
        return

    # 2. Separate Admins from Non-Admins
    admins = [p for p in queued_players if p[4] == 1]
    non_admins = [p for p in queued_players if p[4] == 0]

    if not admins:
        await interaction.response.send_message("No Admin-Leaders are currently in the queue! At least one must be queued.", ephemeral=True)
        conn.close()
        return

    # 3. Draft the 5 players
    selected_team = []
    
    # Pick 1 random admin
    chosen_admin = random.choice(admins)
    selected_team.append(chosen_admin)
    
    # Pick 4 others (could be other admins if not enough non-admins, but prioritizes non-admins)
    remaining_pool = [p for p in queued_players if p[0] != chosen_admin[0]]
    selected_team += random.sample(remaining_pool, 4)

    # Remove drafted players from the active queue
    for player in selected_team:
        active_queue.discard(player[0])

    # 4. Assign Roles (Greedy Algorithm)
    roles_needed = ["Top", "Jungle", "Mid", "ADC", "Support"]
    final_roster = {}
    unassigned_players = []

    # Pass 1: Try to give everyone their Primary Role
    for player in selected_team:
        ign, primary, secondary = player[1], player[2], player[3]
        if primary in roles_needed:
            final_roster[primary] = f"{ign} (Primary)"
            roles_needed.remove(primary)
        else:
            unassigned_players.append(player)

    # Pass 2: Try to give unassigned players their Secondary Role
    still_unassigned = []
    for player in unassigned_players:
        ign, primary, secondary = player[1], player[2], player[3]
        if secondary in roles_needed and secondary != "Fill":
            final_roster[secondary] = f"{ign} (Secondary)"
            roles_needed.remove(secondary)
        else:
            still_unassigned.append(player)

    # Pass 3: Auto-Fill the rest
    for player in still_unassigned:
        ign = player[1]
        forced_role = roles_needed.pop(0)
        final_roster[forced_role] = f"⚠️ {ign} (Auto-Filled) ⚠️"

    # 5. Generate OP.GG Link (Dynamically fetch region from database)
    cursor.execute("SELECT setting_value FROM server_settings WHERE setting_key = 'region'")
    region = cursor.fetchone()[0]
    conn.close()

    igns_only = [p[1] for p in selected_team]
    joined_igns = ','.join(igns_only)
    
    # URL encode the IGNs (converts spaces and symbols so the web link works)
    encoded_igns = urllib.parse.quote_plus(joined_igns)
    opgg_url = f"https://op.gg/lol/multisearch/{region}?summoners={encoded_igns}"

    # 6. Format the Discord Message
    embed = discord.Embed(title="Flex Team Drafted!", color=discord.Color.green())
    embed.add_field(name="Top", value=final_roster.get("Top", "Missing"), inline=False)
    embed.add_field(name="Jungle", value=final_roster.get("Jungle", "Missing"), inline=False)
    embed.add_field(name="Mid", value=final_roster.get("Mid", "Missing"), inline=False)
    embed.add_field(name="ADC", value=final_roster.get("ADC", "Missing"), inline=False)
    embed.add_field(name="Support", value=final_roster.get("Support", "Missing"), inline=False)
    embed.add_field(name="Scouting", value=f"[Click here for OP.GG Multisearch]({opgg_url})", inline=False)
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)