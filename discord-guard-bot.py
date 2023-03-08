
import re
import asyncio
from collections import deque
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from aiohttp import web, TCPConnector
import discord
from discord.ext import commands
import random
import string
import base64
import transformers


intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)

# Command whitelisting
@commands.check
async def check_allowed_users(ctx):
    allowed_users = [1234567890, 9876543210] # Replace with your own list of allowed user IDs
    return ctx.author.id in allowed_users

whitelist_command = commands.check_any(commands.is_owner(), commands.has_any_role('admin'), check_allowed_users)

# Command cooldowns
cooldowns = {}
cooldown_command = commands.cooldown(1, 60, commands.BucketType.user)

# Input sanitization
sanitize_command = commands.clean_content()

# Anti-spam measures
last_messages = deque(maxlen=5)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    last_messages.append(message.content)
    if len(set(last_messages)) == 1:
        await message.channel.send(f"{message.author.mention}, stop spamming!")
    else:
        await client.process_commands(message)

# Permission checks
admin_command = commands.has_permissions(administrator=True)

# Obfuscation and sandboxing
def obfuscate_code(code):
    code_bytes = code.encode('utf-8')
    encoded_bytes = base64.b64encode(code_bytes)
    return encoded_bytes.decode('utf-8')

@commands.command(name="eval")
@admin_command
async def command_eval(ctx, *, code):
    try:
        encoded_code = obfuscate_code(code)
        eval_code = f"exec(base64.b64decode('{encoded_code}').decode('utf-8'))"
        exec(eval_code, globals())
    except Exception as e:
        traceback.print_exc()
        await ctx.send(f"Error executing code: {str(e)}")



nlp = transformers.pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Set up raid protection variables
MAX_MENTIONS = 5
MAX_NEW_USERS = 5
MAX_NEW_USER_RATE = 0.5
NEW_USER_WINDOW = 60.0
ANTI_SPAM_DELAY = 10

# Keep track of new users for raid protection
new_users = []
new_user_timestamps = []

# Event: on_member_join
@client.event
async def on_member_join(member):
    join_age = (discord.utils.utcnow() - member.created_at).days
    if join_age < 7:
        await member.send("Sorry, you cannot join this server because your account is less than 7 days old.")
        await member.kick(reason="Account age < 7 days")
        return
    if len(new_users) > MAX_NEW_USERS and (discord.utils.utcnow() - new_user_timestamps[-1]).total_seconds() < NEW_USER_WINDOW:
        await member.send("Sorry, you cannot join this server at this time.")
        await member.kick(reason="Possible raid")
        return
    captcha_data = captcha.generate()
    with open("captcha.png", "wb") as f:
        f.write(captcha_data.image)
    await member.send(file=discord.File("captcha.png"))
    def check(message):
        return message.author == member and captcha_data.validate(message.content)
    try:
        response = await client.wait_for("message", check=check, timeout=60.0)
        await response.add_roles(your role here)
        await member.send("You have been verified.")
    except asyncio.TimeoutError:
        await member.kick(reason="Failed to complete CAPTCHA.")

# Event: on_message
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if re.match(r"^<@[!&]?\d+>$", message.content):
        await message.delete()
        return
    mentions = message.mentions
    if len(mentions) > MAX_MENTIONS:
        await message.delete()
        await message.channel.send(f"{message.author.mention} Do not mass mention.")
        return
    now = discord.utils.utcnow()
    new_users_in_window = [u for u, t in zip(new_users, new_user_timestamps) if (now - t).total_seconds() < NEW_USER_WINDOW]
    if len(new_users_in_window) > MAX_NEW_USERS and (len(new_users_in_window) / NEW_USER_WINDOW) > MAX_NEW_USER_RATE:
        await message.delete()
        await message.channel.send(f"{message.author.mention} Do not spam the chat.")
        return
    sentiment = nlp(message.content)[0]['label']
    if sentiment == 'NEGATIVE':
        await message.delete()
        await message.author.send("Your message was deleted because it contained negative sentiment.")
    elif sentiment == 'POSITIVE':
        pass
    else:
        await message.channel.send("I'm sorry, I couldn't understand the sentiment of your message.")
    await bot.process_commands(message)

# Command: set_slowmode
@client.command()
async def set_slowmode(ctx, seconds: int):
    await set_slowmode(ctx, 2)
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Set slowmode delay to {seconds} seconds.")
   
# Prevent abuse and unauthorized access
@set_slowmode.error
async def set_slowmode_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    else:
        await ctx.send("An error occurred while processing the command.")
mentions = {}
last_mention_time = None

async def on_ready():
    print('Bot is ready!')

async def on_message(message):
    global last_mention_time

    if message.author == bot.user:
        return

    if len([msg for msg in bot.cached_messages if msg.author == message.author and msg.created_at > message.created_at - discord.Duration(seconds=1)]) >= 5:
        await message.author.add_roles(discord.utils.get(message.guild.roles, name="muted"))
        await asyncio.sleep(30)
        await message.author.remove_roles(discord.utils.get(message.guild.roles, name="muted"))
        return

    if re.match(r"^<@[!&]?\d+>$", message.content):
        await message.delete()
        return

    mentions = message.mentions
    if message.author.id not in mentions:
        mentions[message.author.id] = 0
    mentions[message.author.id] += len(message.mentions)
    if mentions[message.author.id] > MAX_MENTIONS:
        await message.delete()
        await message.channel.send(f"{message.author.mention} Do not mass mention.")
        return

    now = discord.utils.utcnow()
    new_users_in_window = [u for u, t in zip(new_users, new_user_timestamps) if (now - t).total_seconds() < NEW_USER_WINDOW]
    if len(new_users_in_window) > MAX_NEW_USERS and (len(new_users_in_window) / NEW_USER_WINDOW) > MAX_NEW_USER_RATE:
        await message.delete()
        await message.channel.send(f"{message.author.mention} Do not spam the chat.")
        return

    # analyze the message for sentiment
    sentiment = nlp(message.content)[0]['label']

    # take action based on sentiment
    if sentiment == 'NEGATIVE':
        await message.delete()
        await message.author.send("Your message was deleted because it contained negative sentiment.")
    elif sentiment == 'POSITIVE':
        # do nothing
        pass
    else:
        await message.channel.send("I'm sorry, I couldn't understand the sentiment of your message.")

    await bot.process_commands(message)


RATE_LIMIT = 5
rate_limit_exceeded = asyncio.Event()

async def limit_rate():
    while True:
        rate_limit_exceeded.clear()
        await asyncio.sleep(1 / RATE_LIMIT)
        rate_limit_exceeded.set()

queue = deque(maxlen=5)

tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

blacklisted_channels = []
blacklisted_users = []
MENTION_THRESHOLD = 5
EMOJI_THRESHOLD = 10
ATTACHMENT_THRESHOLD = 5
UNICODE_THRESHOLD = 10

raid_detected = False
ddos_detected = False
num_msgs_in_last_second = 0
messages_in_last_second = []

async def on_socket_raw_receive(msg):
    global num_msgs_in_last_second, messages_in_last_second
    if msg.startswith('PRESENCE_UPDATE'):
        presence_data = json.loads(msg)
        if presence_data['user']['id'] != client.user.id:
            messages_in_last_second.append(presence_data)
            if len(messages_in_last_second) > 5:
                messages_in_last_second.pop(0)
            num_msgs_in_last_second += 1
            if num_msgs_in_last_second > 10:
                ddos_detected = True
                for guild in client.guilds:
                    for channel in guild.channels:
                        await channel.send('Possible DDoS detected. Disabling all channels...')
                        await channel.set_permissions(guild.default_role, send_messages=False)
            if len(messages_in_last_second) == 5 and len(set([message['guild_id'] for message in messages_in_last_second])) == 1:
                raid_detected = True
                for guild in client.guilds:
                    for channel in guild.channels:
                        await channel.send('Possible raid detected. Disabling all channels...')
                        await channel.set_permissions(guild.default_role, send_messages=False)
            await asyncio.sleep(1)
            num_msgs_in_last_second -= 1
            messages_in_last_second.pop(0)

async def on_message(message):
    if message.author.bot or message.webhook_id:
        return

    # Check for blacklisted channels and users
    if message.channel.id in blacklisted_channels or message.author.id in blacklisted_users:
        await message.delete()
        return

    # Check message length
    if len(message.content) > 2000:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, your message is too long.")

    # Check mentions
    if len(message.mentions) > MENTION_THRESHOLD:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please do not mention more than {MENTION_THRESHOLD} users in one message.")

    # Check emoji usage
    emoji_count = sum(map(lambda x: x.is_custom_emoji(), message.content))
    if emoji_count > EMOJI_THRESHOLD:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please do not use more than {EMOJI_THRESHOLD} custom emojis in one message.")

    # Check for other unwanted behavior
    if message.channel.id in blacklisted_channels or message.author.id in blacklisted_users:
        await message.delete()
        return

    if len(message.content) > 2000:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, your message is too long.")

    if len(message.mentions) > MENTION_THRESHOLD:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please do not mention more than {MENTION_THRESHOLD} users in one message.")


client.run("your discord token here")

