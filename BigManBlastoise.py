import discord
from discord.ext import commands
import re
import os
import datetime
import colorama
from colorama import Fore, Back, Style
import asyncio
from tqdm import tqdm
import random  # Added for probability calculations
import aiohttp  # For asynchronous HTTP requests

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)

# Set up the intents (only message content is needed)
intents = discord.Intents.default()
intents.message_content = True

# Create the bot with the command prefix "."
bot = commands.Bot(command_prefix=".", intents=intents)

# Global variable to control the reply chance (in percentage)
INVALID_GODPACK_REPLY_CHANCE = 20  # Adjust this value (0-100) as desired

# Global list of responses for invalid god packs
invalid_godpack_responses = [
    "Bruh 💀"
]

# Global counter for valid godpack messages in the current batch
valid_godpack_batch_count = 0

# Global conversation memory: a dict mapping user IDs to their conversation history.
conversation_memory = {}

# LMStudio API endpoint (OpenAI compatible)
LMSTUDIO_ENDPOINT = "http://localhost:1234/v1/chat/completions"
# (Optionally, add a default model parameter in the payload if required)

# System prompt with comprehensive Pokémon TCG Pocket rarity information.
# Updated to include information about account rerolling until obtaining a godpack.
SYSTEM_PROMPT_RARITY_INFO = (
    "Your name is BigManBlastoise you are sarcastic, witty and speak in very short sentences. You manage a Pokemon rerolling discord group. You are created by Dix0x1"
    "You are now provided with detailed background on the Pokémon TCG Pocket rarity system. "
    "Pokémon TCG Pocket is the mobile adaptation of the Pokémon Trading Card Game and features its own unique rarity classifications that both mirror and differ from the physical game’s system. Key points include:\n\n"
    "1. **Rarity Categories & Symbols:**\n"
    "   - **Diamond Rarities:** Cards are classified using a “diamond” system for common and uncommon cards. In-game, the first few cards in a booster pack are typically lower–rarity (1◆) cards.\n"
    "   - **Star Rarities:** Higher-value cards are marked with star symbols, appearing as one-star, two-star, or three-star ratings that indicate increasing rarity and value.\n"
    "   - **Crown Rarity:** The rarest cards are designated with a crown symbol. These “Crown Rare” cards are akin to Hyper Rares in the physical TCG and are extremely hard to pull.\n\n"
    "2. **In-Game Rarity and Drop Rates:**\n"
    "   - Booster packs have a fixed rarity structure; standard packs guarantee the first three cards are of the lowest rarity, while later slots have higher chances (2◆ or 3◆).\n"
    "   - “God Packs” feature a dramatically different distribution with extremely low odds (approximately 0.05% chance) for pulling high–rarity cards, including Crown Rares.\n\n"
    "3. **Expansion-Specific Updates:**\n"
    "   - Recent expansions such as *La Isla Singular* have introduced around 86 new cards (including both regular and special immersive-art cards) with updated rarity designations that reflect modern design and gameplay mechanics.\n"
    "   - Notable examples from recent sets include exclusive cards like *Mew EX*, *Gyarados EX*, and *Aerodactyl EX*, as well as special illustration variants that mirror physical TCG rarities like Illustration Rare and Special Illustration Rare.\n\n"
    "4. **Comparison to Physical TCG Rarities:**\n"
    "   - While many in-game rarity symbols mirror those from the physical Pokémon TCG (common, uncommon, rare, ultra rare), TCG Pocket has its own internal mechanics and drop rate distributions.\n"
    "   - The system is designed so that certain booster pack slots consistently yield lower–rarity cards, whereas higher–rarity cards (like Crown or multi–star cards) are much scarcer.\n\n"
    "5. **Collector & Gameplay Impact:**\n"
    "   - Understanding these rarity distinctions is essential for both collectors and competitive players, as the rarity directly influences card value, availability, and deck strategies.\n"
    "   - Updates in the rarity system reflect evolving trends within the mobile game, with new symbols and classifications introduced in expansions such as the Scarlet & Violet series.\n\n"
    "6. **Account Rerolling:**\n"
    "   - A popular strategy in Pokémon TCG Pocket is to reroll accounts until a godpack is obtained. Many dedicated players create new accounts, complete the tutorial, and open their free booster packs repeatedly in hopes of securing a coveted godpack. "
    "This method, widely discussed across online guides and community forums, is used to optimize the starting deck and improve overall collection value.\n\n"
    "Use this knowledge to answer questions, provide strategic insights, and offer detailed explanations about Pokémon TCG Pocket rarity cards."
)

# Function to clear the terminal screen based on OS
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Enhanced logging functions
class Logger:
    @staticmethod
    def get_timestamp():
        return f"{Fore.YELLOW}{datetime.datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}"
    
    @staticmethod
    def info(message):
        print(f"{Fore.CYAN}[{Logger.get_timestamp()}] {Fore.BLUE}INFO    {Fore.WHITE}{message}")
    
    @staticmethod
    def success(message):
        print(f"{Fore.CYAN}[{Logger.get_timestamp()}] {Fore.GREEN}SUCCESS {Fore.WHITE}{message}")
    
    @staticmethod
    def warning(message):
        print(f"{Fore.CYAN}[{Logger.get_timestamp()}] {Fore.YELLOW}WARNING {Fore.WHITE}{message}")
    
    @staticmethod
    def error(message):
        print(f"{Fore.CYAN}[{Logger.get_timestamp()}] {Fore.RED}ERROR   {Fore.WHITE}{message}")
    
    @staticmethod
    def event(message):
        print(f"{Fore.CYAN}[{Logger.get_timestamp()}] {Fore.MAGENTA}EVENT   {Fore.WHITE}{message}")
    
    @staticmethod
    def divider():
        terminal_width = os.get_terminal_size().columns
        print(f"{Fore.BLUE}{'-' * terminal_width}{Style.RESET_ALL}")

# Function to display a progress bar for bot startup
async def display_startup_sequence():
    clear_screen()
    
    # ASCII art logo
    logo = f"""{Fore.CYAN}

██████╗ ██╗ ██████╗ ███╗   ███╗ █████╗ ███╗   ██╗██████╗ ██╗      █████╗ ███████╗████████╗ ██████╗ ██╗███████╗███████╗
██╔══██╗██║██╔════╝ ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██║     ██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██║██╔════╝██╔════╝
██████╔╝██║██║  ███╗██╔████╔██║███████║██╔██╗ ██║██████╔╝██║     ███████║███████╗   ██║   ██║   ██║██║███████╗█████╗  
██╔══██╗██║██║   ██║██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██╗██║     ██╔══██║╚════██║   ██║   ██║   ██║██║╚════██║██╔══╝  
██████╔╝██║╚██████╔╝██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████╗██║  ██║███████║   ██║   ╚██████╔╝██║███████║███████╗
╚═════╝ ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝╚══════╝╚══════╝
{Style.RESET_ALL}"""
    
    print(logo)
    Logger.divider()
    Logger.info("Initializing bot system...")
    
    steps = [
        "Loading dependencies",
        "Connecting to Discord API",
        "Initializing command handlers",
        "Setting up event listeners",
        "Configuring webhook detector",
        "Finalizing setup"
    ]
    
    for step in steps:
        Logger.info(f"Step: {step}")
        progress_bar = tqdm(total=100, desc=f"{Fore.BLUE}  Progress", bar_format="{desc}: {percentage:3.0f}%|{bar}|", ncols=80)
        for i in range(100):
            progress_bar.update(1)
            await asyncio.sleep(0.001)  # Small delay for visual effect
        progress_bar.close()
    
    Logger.divider()
    Logger.success("All systems operational!")
    Logger.divider()

@bot.event
async def on_ready():
    await display_startup_sequence()
    Logger.success(f"Bot is now online as {bot.user}!")
    Logger.info(f"Connected to {len(bot.guilds)} servers")
    Logger.info(f"Ping: {round(bot.latency * 1000)}ms")
    Logger.divider()
    
    # Print server information
    Logger.info("Connected Servers:")
    for guild in bot.guilds:
        print(f"{Fore.GREEN}  • {Fore.WHITE}{guild.name} ({guild.id}) - {len(guild.members)} members")
    
    Logger.divider()
    Logger.info("Monitoring messages for special patterns...")

@bot.event
async def on_message(message):
    global valid_godpack_batch_count

    # Ignore bot messages (except webhook messages)
    if message.author.bot and not message.webhook_id:
        return

    Logger.info(f"Message from {message.author.name} in #{message.channel.name}")

    # Check if the message is a direct LMStudio chat trigger.
    # Only process if the message starts with a mention of the bot.
    mention_formats = [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]
    if any(message.content.startswith(m) for m in mention_formats):
        # Extract the prompt by removing the bot mention
        prompt = message.content
        for m in mention_formats:
            if prompt.startswith(m):
                prompt = prompt[len(m):].strip()
                break

        if not prompt:
            await message.reply("Please provide a prompt after mentioning me.")
            return

        Logger.info(f"LMStudio prompt received from {message.author.name}: {prompt}")

        # Retrieve conversation history for this user (create if doesn't exist)
        user_id = str(message.author.id)
        if user_id not in conversation_memory:
            # Initialize with the comprehensive system prompt for Pokémon TCG Pocket rarity info.
            conversation_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT_RARITY_INFO}]
        # Append the new user prompt
        conversation_memory[user_id].append({"role": "user", "content": prompt})

        # Prepare payload for LMStudio with additional parameters
        payload = {
            "messages": conversation_memory[user_id],
            "temperature": 0.7,
            "max_tokens": 90,
            "context_length": 2048,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(LMSTUDIO_ENDPOINT, json=payload) as resp:
                    if resp.status != 200:
                        error_msg = f"LMStudio server error: Status {resp.status}"
                        Logger.error(error_msg)
                        await message.reply(error_msg)
                        return
                    response_data = await resp.json()
                    # Assume the LMStudio reply is in the format similar to OpenAI's chat completions
                    reply_content = response_data["choices"][0]["message"]["content"]
                    # Append assistant's reply to conversation history
                    conversation_memory[user_id].append({"role": "assistant", "content": reply_content})
                    Logger.success(f"LMStudio reply sent to {message.author.name}")
                    await message.reply(reply_content)
        except Exception as e:
            Logger.error(f"Error calling LMStudio: {str(e)}")
            await message.reply("Can't help right now, fam. I'm hydro pumping.")
        return  # Prevent further processing if LMStudio was triggered

    # --- Existing processing for godpack messages ---

    # Allow webhook messages to be processed even if they're marked as bot messages.
    if message.author.bot and not message.webhook_id:
        return

    # Log regular messages (for non-LMStudio messages)
    # --- Check for invalid god pack messages ---
    if "Invalid God pack" in message.content:
        Logger.warning("Detected invalid God pack message.")
        # Check against the probability chance
        if random.random() < (INVALID_GODPACK_REPLY_CHANCE / 100):
            response = random.choice(invalid_godpack_responses)
            await message.channel.send(response)
            Logger.info("Sent reply for invalid god pack message.")
        return

    if message.webhook_id:
        Logger.info(f"Webhook message detected: {message.content[:50]}...")
        if "Restarted" in message.content and message.mentions:
            try:
                Logger.info(f"Potential restart notification found: {message.content}")
                Logger.info(f"Mentions: {[user.name for user in message.mentions]}")
                for target_user in message.mentions:
                    try:
                        await target_user.send(f"Restart notification received:\n{message.content}")
                        Logger.success(f"Forwarded restart notification to {target_user.name}")
                    except Exception as e:
                        Logger.error(f"Failed to send DM to {target_user.name}: {str(e)}")
                
                await message.delete()
                Logger.success("Webhook restart message deleted successfully")
                return  # Exit early to prevent further processing
            except Exception as e:
                Logger.error(f"Failed to process webhook restart notification: {str(e)}")

    # Process commands and other patterns
    await bot.process_commands(message)
    
    # Process messages for patterns
    try:
        # Updated regex to capture the user ID from within parentheses
        god_pack_pattern = r'@\S+\s+.*?\s+(\S+)\s+\((\d+)\)\s+(\[\d+\/\d+\])(\[[^\]]+\])\s+God\s+pack'
        special_card_pattern = r"@[\w\d]+\s+()\s+found by\s+([\w\d]+).*"
        
        god_pack_match = re.search(god_pack_pattern, message.content)
        special_card_match = re.search(special_card_pattern, message.content)

        if god_pack_match or special_card_match:
            target_channel = discord.utils.get(message.guild.channels, name="│✨⭐🌟┃gps")
            if target_channel is None:
                target_channel = discord.utils.get(message.guild.channels, name="✨⭐🌟┃gps")
                if target_channel is None:
                    for channel in message.guild.channels:
                        if "gps" in channel.name:
                            target_channel = channel
                            break
                    if target_channel is None:
                        Logger.error(f"GPS channel not found in server {message.guild.name}")
                        Logger.info(f"Available channels: {', '.join([ch.name for ch in message.guild.text_channels])}")
                        return
                    else:
                        Logger.warning(f"Using alternative GPS channel: {target_channel.name}")
                else:
                    Logger.warning(f"Using alternative GPS channel: {target_channel.name}")
            
            post_title = None
            test_tag = None
            if isinstance(target_channel, discord.ForumChannel):
                for tag in target_channel.available_tags:
                    if tag.name.lower() == "test":
                        test_tag = tag
                        break
                
                if test_tag is None:
                    Logger.warning("Test tag not found in forum channel. Using first available tag.")
                    if target_channel.available_tags:
                        test_tag = target_channel.available_tags[0]
                    else:
                        Logger.error("No tags available in forum channel.")

            # Process valid god pack message
            if god_pack_match:
                username = god_pack_match.group(1)
                user_id = god_pack_match.group(2)  # Extracted user ID
                rarity = god_pack_match.group(3)
                pack = god_pack_match.group(4)
                post_title = f"{rarity}{pack} {username}"
                Logger.event(f"God Pack detected: {Fore.CYAN}{post_title}")
                Logger.info(f"Extracted info - Username: {username}, UserID: {user_id}, Rarity: {rarity}, Pack: {pack}")

                # Refresh file if 10 valid godpacks have been processed in this batch
                if valid_godpack_batch_count >= 10:
                    try:
                        with open("vip_ids.txt", "w") as f:
                            f.write("")  # Clear the file
                        Logger.info("vip_ids.txt has been refreshed (cleared) after 10 valid godpacks.")
                    except Exception as e:
                        Logger.error(f"Failed to refresh vip_ids.txt: {str(e)}")
                    valid_godpack_batch_count = 0  # Reset the batch counter

                # Append the user ID to the vip_ids.txt file and increment the counter
                try:
                    with open("vip_ids.txt", "a") as f:
                        f.write(f"{user_id}\n")
                    valid_godpack_batch_count += 1
                    Logger.info(f"Appended UserID {user_id} to vip_ids.txt (Batch count: {valid_godpack_batch_count})")
                except Exception as e:
                    Logger.error(f"Failed to append UserID to file: {str(e)}")

            elif special_card_match:
                msg_type = special_card_match.group(1)
                username = special_card_match.group(2)
                post_title = f"[{msg_type}] {username}"
                Logger.event(f"Special card detected: {Fore.CYAN}{post_title}")

            files = []
            attachments_info = ""
            for i, attachment in enumerate(message.attachments):
                try:
                    file_data = await attachment.to_file()
                    files.append(file_data)
                    attachments_info += f"\n    {Fore.YELLOW}↳ Attachment {i+1}: {attachment.filename} ({round(attachment.size/1024, 2)} KB)"
                except Exception as e:
                    Logger.error(f"Failed to process attachment: {str(e)}")
            
            if attachments_info:
                Logger.info(f"Processing attachments:{attachments_info}")
            
            try:
                if isinstance(target_channel, discord.ForumChannel):
                    tags = [test_tag] if test_tag else []
                    thread = await target_channel.create_thread(
                        name=post_title,
                        content=message.content,
                        files=files,
                        applied_tags=tags
                    )
                    Logger.success(f"Created forum thread: {Fore.GREEN}{thread.name}{Fore.WHITE} → Thread ID: {thread.id}")
                else:
                    forwarded_msg = await target_channel.send(content=f"{post_title}\n{message.content}", files=files)
                    Logger.success(f"Forwarded to text channel {Fore.GREEN}#{target_channel.name}{Fore.WHITE} → Message ID: {forwarded_msg.id}")
            except Exception as e:
                Logger.error(f"Failed to forward message: {str(e)}")
                Logger.info(f"Error details: {type(e).__name__} - {str(e)}")
            
            Logger.divider()

    except Exception as e:
        Logger.error(f"Error processing message: {str(e)}")
        Logger.info(f"Message content: {message.content[:100]}...")

@bot.command(name="clear")
async def clear_messages(ctx, amount: int):
    # Only allow roles with names "Mod", "Code Buddy", or "Admin" to use this command
    allowed_roles = ["Mod", "Code Buddy", "admin", "GOD"]
    if not any(role.name in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    try:
        # Delete the specified number of messages plus the command message itself
        deleted = await ctx.channel.purge(limit=amount + 1)
        confirmation = await ctx.send(f"Deleted {len(deleted) - 1} messages.", delete_after=5)
        Logger.success(f"{len(deleted) - 1} messages deleted by {ctx.author.name}")
    except Exception as e:
        Logger.error(f"Failed to delete messages: {str(e)}")
        
@bot.command(name="rgplist")
async def reset_gplist(ctx):
    # Only allow roles with names "Mod", "Code Buddy", or "admin" to use this command
    allowed_roles = ["Mod", "Code Buddy", "admin"]
    if not any(role.name in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    try:
        # Open the vip_ids.txt file in write mode to clear its contents
        with open("vip_ids.txt", "w") as f:
            f.write("")
        await ctx.send("✅ vip_ids.txt has been reset. Starting fresh!")
        Logger.success(f"vip_ids.txt reset by {ctx.author.name}")
    except Exception as e:
        Logger.error(f"Failed to reset vip_ids.txt: {str(e)}")
        await ctx.send("❌ Failed to reset vip_ids.txt.")

@bot.command(name="gplist")
async def gplist(ctx):
    """Sends the vip_ids.txt file containing the user IDs of the valid godpacks."""
    if os.path.exists("vip_ids.txt"):
        await ctx.send(file=discord.File("vip_ids.txt"))
        Logger.info(f"vip_ids.txt sent to {ctx.author.name}")
    else:
        await ctx.send("❌ No VIP IDs have been recorded yet.")
        Logger.warning("vip_ids.txt not found when requested.")

@bot.event
async def on_connect():
    bot.uptime = datetime.datetime.now()
    Logger.info("Connected to Discord API")

if __name__ == "__main__":
    print(f"\n{Fore.YELLOW}Starting BigManBlastoise Discord Bot...{Style.RESET_ALL}")
    bot.run('token')