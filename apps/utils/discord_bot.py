import discord
from discord.ext import commands
import datetime
import os
import asyncio

import configparser
import django
import shopify

if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()
from django.conf import settings
from apps.users.models import User, DiscordMessageLog

config = configparser.ConfigParser()
config.read('config.ini')

discord_token = settings.DISCORD_BOT_TOKEN
channel_ids = settings.DISCORD_BOT_CHANNELS

points_per_message = settings.POINTS_PER_MESSAGE
max_points_per_day = settings.MAX_POINTS_PER_DAY

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if str(message.channel.id) in channel_ids:
        user_id = message.author.id
        user = User.objects.filter(discord_id=user_id).first()
        discord_log = DiscordMessageLog.objects.filter(discord_id=user_id).first()
        if discord_log:
            if discord_log.log_date == datetime.date.today():
                discord_log.is_notify_reg = False
                discord_log.is_notify_max_rew = False
                discord_log.today_rew = 0
                discord_log.save()
        else:
            discord_log = DiscordMessageLog.objects.create(discord_id=user_id)
        if user:
            if discord_log.today_rew > max_points_per_day:
                if not discord_log.is_notify_max_rew:
                    reply = await message.channel.send(
                        f"""{message.author.mention} You have reached the maximum number of rewards today. Please continue to chat tomorrow.""")
                    discord_log.is_notify_max_rew = True
                    discord_log.save()
            else:
                user.level_points += points_per_message
                user.save()
                user.update_level()
                points = user.level_points
                level = user.level
                reply = await message.channel.send(f"""🎉Thanks for your affirmation and encouragement!!!💗
                        Name:{message.author.mention}
                        Reward:{points_per_message:.2f}🍬
                        Total:{points:.2f}
                        Level:VIP{level}""")
        else:
            if not discord_log.is_notify_reg:
                reply = await message.channel.send(
                    f"""{message.author.mention} You are not a member of the community yet. Please register and then bind your discord account.""")
                discord_log.is_notify_reg = True
                discord_log.save()
        await bot.process_commands(message)


def main():
    bot.run(discord_token)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
