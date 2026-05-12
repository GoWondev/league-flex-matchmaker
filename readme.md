# 🎮 League Flex-Queue Matchmaker Bot

Vibe coded af :D

A self-hosted Discord bot built with Python that completely automates 5-man Flex Queue matchmaking. It tracks your server's player roster, guarantees an Admin/Shotcaller is in every game, respects primary and secondary role choices, and instantly generates an OP.GG multi-search link for the drafted team.

No more awkward "who gets to play" conversations or accusations of favoritism!

## ✨ Features
* **Role Prioritization:** Attempts to give everyone their Primary role. If there's a conflict, it checks Secondary roles. Auto-fills as a last resort.
* **Admin Guarantee:** Ensures at least one designated "Admin-Leader" is drafted into every team composition.
* **Database Integration:** Uses a lightweight SQLite database to remember everyone's Riot ID and role preferences.
* **One-Click OP.GG:** Automatically generates an EUW OP.GG multi-search link for the 5 drafted players (supports the new `Name#Tag` Riot ID format).
* **Modern UI:** Uses Discord's Slash Commands and dropdown menus for a clean user experience.

## 🛠️ Prerequisites
* Python 3.8 or higher installed on your machine/server.
* A Discord Bot Application created in the [Discord Developer Portal](https://discord.com/developers/applications).
* **Important:** You must enable the **Server Members Intent** and **Message Content Intent** in your bot's Developer Portal settings.

## 🚀 Installation & Setup

**1. Clone the repository**
\`\`\`bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
\`\`\`

**2. Install dependencies**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

**3. Configure your Environment Variables**
Create a file named `.env` in the root directory of the project and add your Bot Token and Server ID:
\`\`\`env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_discord_server_id_here
\`\`\`

**4. Run the Bot**
\`\`\`bash
python bot.py
\`\`\`
*(On the first run, the bot will automatically generate the `flex_roster.db` SQLite database).*

## 📖 Command List

| Command | Description | Access |
| :--- | :--- | :--- |
| `/register [ign] [primary] [secondary]` | Creates or updates your player profile. | Everyone |
| `/queue [join/leave/view]` | Manages your status in the active playing pool. | Everyone |
| `/generate_team` | Drafts 5 players, assigns roles, and generates an OP.GG link. | Admins Only |

## 🌍 Changing the OP.GG Region
By default, the bot generates `euw` multi-search links. To change this, open `bot.py`, find the `generate_team` command, and change `euw` to your preferred region (e.g., `na`, `eune`, `kr`):
\`\`\`python
opgg_url = f"https://op.gg/lol/multisearch/na?summoners={encoded_igns}"
\`\`\`