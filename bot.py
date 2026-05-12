import discord
import os
from dotenv import load_dotenv
from discord import app_commands
import sqlite3
import random
import urllib.parse

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

# --- 1. Database Setup ---
def setup_db():
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    # Create the players table if it doesn't exist yet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            discord_id INTEGER PRIMARY KEY,
            ign TEXT,
            primary_role TEXT,
            secondary_role TEXT,
            is_admin INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Run the setup right away
setup_db() 

# --- 2. Bot Setup ---
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # PUT YOUR SERVER ID HERE
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
        f"✅ Successfully registered **{ign}**!\n"
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

# --- 5. Generate Team Algorithm ---
@bot.tree.command(name="generate_team", description="[ADMIN ONLY] Drafts a 5-man team from the queue")
@app_commands.checks.has_permissions(administrator=True)
async def generate_team(interaction: discord.Interaction):
    if len(active_queue) < 5:
        await interaction.response.send_message(f"X Not enough players in queue! We need at least 5, but only have {len(active_queue)}.", ephemeral=True)
        return

    # 1. Fetch profiles of everyone in the queue from the database
    conn = sqlite3.connect('flex_roster.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(active_queue))
    cursor.execute(f"SELECT discord_id, ign, primary_role, secondary_role, is_admin FROM players WHERE discord_id IN ({placeholders})", tuple(active_queue))
    queued_players = cursor.fetchall()
    conn.close()

    # If someone in the queue never used /register, they won't be in the database
    if len(queued_players) < 5:
        await interaction.response.send_message("Some players in the queue haven't used `/register` yet!", ephemeral=True)
        return

    # 2. Separate Admins from Non-Admins
    admins = [p for p in queued_players if p[4] == 1]
    non_admins = [p for p in queued_players if p[4] == 0]

    if not admins:
        await interaction.response.send_message("No Admin-Leaders are currently in the queue! At least one must be queued.", ephemeral=True)
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
        final_roster[forced_role] = f"! {ign} (Auto-Filled) !"

    # 5. Generate OP.GG Link (Set to EUW based on your location)
    igns_only = [p[1] for p in selected_team]
    joined_igns = ','.join(igns_only)
    # URL encode the IGNs (converts spaces and symbols so the web link works)
    encoded_igns = urllib.parse.quote_plus(joined_igns)
    opgg_url = f"https://op.gg/lol/multisearch/euw?summoners={encoded_igns}"

    # 6. Format the Discord Message
    embed = discord.Embed(title="🎮 Flex Team Drafted!", color=discord.Color.green())
    embed.add_field(name="Top", value=final_roster.get("Top", "Missing"), inline=False)
    embed.add_field(name="Jungle", value=final_roster.get("Jungle", "Missing"), inline=False)
    embed.add_field(name="Mid", value=final_roster.get("Mid", "Missing"), inline=False)
    embed.add_field(name="ADC", value=final_roster.get("ADC", "Missing"), inline=False)
    embed.add_field(name="Support", value=final_roster.get("Support", "Missing"), inline=False)
    embed.add_field(name="Scouting", value=f"[Click here for OP.GG Multisearch]({opgg_url})", inline=False)
    
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)