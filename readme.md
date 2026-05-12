# 🎮 League Flex-Queue Matchmaker Bot

A completely self-hosted, plug-and-play Discord bot that automates 5-man Flex Queue matchmaking. It tracks your server's player roster, guarantees an Admin/Shotcaller is in every game, respects primary and secondary role choices, and instantly generates an OP.GG multi-search link for the drafted team.

No more awkward "who gets to play" conversations, tracking spreadsheets, or accusations of favoritism!

## ✨ Features
* **Role Prioritization:** Attempts to give everyone their Primary role. Checks Secondary roles if there's a conflict. Auto-fills as a last resort.
* **Admin Guarantee:** Ensures at least one designated "Admin-Leader" is drafted into every team composition.
* **One-Click OP.GG:** Automatically generates an OP.GG multi-search link for the 5 drafted players.
* **Dynamic Regions:** Change your server's OP.GG region on the fly straight from Discord (EUW, NA, KR, etc.).
* **Zero-Code Setup:** No Python or Git required. Just download, paste your credentials, and run.

---

## 🛠️ Step-by-Step Setup Guide

To get this bot running, you need two hidden pieces of information from Discord: a **Bot Token** (its password) and a **Server ID** (its home). Follow these exact steps to get them.

### Step 1: Create the Bot and Get Your Token
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in with your normal Discord account.
2. Click the **New Application** button in the top right. Name it "Flex Matchmaker" (or whatever you want) and click Create.
3. On the left-hand menu, click on the **Bot** tab.
4. Look for the "Token" section and click **Reset Token** (or Copy). 
5. **⚠️ IMPORTANT:** Copy this long string of text and paste it somewhere safe (like a Notepad file). You will need this later. Do not share this with anyone!

### Step 2: Grant Necessary Permissions (Intents)
While still on the **Bot** tab, scroll down until you see **Privileged Gateway Intents**. 
The bot needs permission to read your server's member list and commands to work.
1. Turn **ON** the switch for `Server Members Intent`.
2. Turn **ON** the switch for `Message Content Intent`.
3. Click the green **Save Changes** button at the bottom.

### Step 3: Invite the Bot to Your Server
Now we need to create the invite link to bring the bot into your server.
1. On the left-hand menu, click on **OAuth2** -> **URL Generator**.
2. Under **Scopes**, check the boxes for `bot` AND `applications.commands`.
3. Scroll down to **Bot Permissions** and check `Administrator`. *(This ensures the bot can post embeds and read commands properly without you manually configuring channel permissions).*
4. Scroll to the very bottom, **Copy** the generated URL, and paste it into a new tab in your web browser.
5. Select your server from the dropdown list and click **Authorize**. The bot is now in your server!

### Step 4: Get Your Server ID
The bot needs to know exactly which server to push its slash commands to.
1. Open your standard Discord app.
2. Go to your User Settings (the gear icon next to your name at the bottom).
3. Scroll down the left menu to **Advanced**.
4. Turn **ON** the switch for `Developer Mode`.
5. Exit settings. Right-click your Server's Icon on the far left server list, and click **Copy Server ID** at the very bottom of the menu.
6. Paste this number into your Notepad with your Token.

---

## 🚀 Running the Bot

Now that you have your **Token** and **Server ID**, you are 10 seconds away from being done.

1. Go to the [Releases page](../../releases) of this repository and download the latest `.zip` file for Windows.
2. Extract the folder to your desktop (or wherever you want the bot to live).
3. Double-click the `bot.exe` file.
4. A black console window will open and ask for your credentials. 
5. Paste your **Bot Token** and hit Enter.
6. Paste your **Server ID** and hit Enter.

**Boom.** The bot will save these locally, generate its own database, and go online. Next time you run the `.exe`, it will log in automatically without asking!

---

## 📖 Command List

| Command | Description | Access |
| :--- | :--- | :--- |
| `/register [ign] [primary] [secondary]` | Creates or updates your player profile. | Everyone |
| `/queue [join/leave/view]` | Manages your status in the active playing pool. | Everyone |
| `/generate_team` | Drafts 5 players, assigns roles, and generates an OP.GG link. | Admins Only |
| `/set_region [region]` | Changes the server's default OP.GG region. | Admins Only |

*Note: You must have Discord Administrator permissions to use the team generation and region commands.*

## 🤝 Contributing
Feel free to fork this repository, submit Pull Requests, or open issues if you want to request new features!