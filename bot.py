import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import urllib.parse

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

token = 'your-bot-token-here'

# Dictionary to keep track of events and their interested users
events = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    check_events.start()

@bot.event
async def on_scheduled_event_create(event):
    channel = discord.utils.get(event.guild.channels, name='events')
    if channel:
        message = await channel.send(f"{event.url}\nReact with 🔔 if you're interested")
        await message.add_reaction('🔔')
        events[message.id] = {'event': event, 'interested': []}

@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == '🔔' and payload.user_id != bot.user.id:
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)
        if message.id in events:
            if user not in events[message.id]['interested']:
                events[message.id]['interested'].append(user)
                # Send direct message with Google Calendar link
                event = events[message.id]['event']
                gcal_link = create_gcal_link(event)
                try:
                    await user.send(f"Click here to add the event {event.name} to your Google Calendar:\n{gcal_link}")
                except discord.Forbidden:
                    pass

def create_gcal_link(event):
    start_time = event.start_time.isoformat()
    end_time = event.end_time.isoformat()
    details = {
        'action': 'TEMPLATE',
        'text': event.name,
        'dates': f"{start_time}/{end_time}",
        'details': event.description,
        'location': event.location,
    }
    params = urllib.parse.urlencode(details)
    return f"https://www.google.com/calendar/render?{params}"

@tasks.loop(minutes=1)
async def check_events():
    now = datetime.utcnow()
    for message_id, data in list(events.items()):
        event = data['event']
        if now + timedelta(minutes=30) >= event.start_time:
            for user in data['interested']:
                try:
                    await user.send(f"Reminder: The event '{event.name}' is starting in 30 minutes!")
                except discord.Forbidden:
                    pass
            del events[message_id]

bot.run(token)
