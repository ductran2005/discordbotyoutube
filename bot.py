import asyncio
import os
from collections import defaultdict, deque

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError('Thiếu DISCORD_TOKEN trong file .env')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
queues = defaultdict(deque)
text_channels = {}

ydl_options = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch1'}

def extract(query):
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = next((item for item in info['entries'] if item), None)
        if not info:
            raise ValueError('Không tìm thấy bài hát.')
        return {'title': info.get('title', 'Không rõ tên'), 'url': info['webpage_url']}

def stream_url(page_url):
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(page_url, download=False)
        return info['url']

async def play_next(guild_id):
    guild = bot.get_guild(guild_id)
    voice = guild.voice_client if guild else None
    if not voice or not voice.is_connected() or not queues[guild_id]:
        return
    item = queues[guild_id].popleft()
    try:
        url = await asyncio.to_thread(stream_url, item['url'])
        source = discord.FFmpegOpusAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        loop = asyncio.get_running_loop()
        voice.play(source, after=lambda error: asyncio.run_coroutine_threadsafe(after_song(guild_id, error), loop))
        channel = bot.get_channel(text_channels.get(guild_id))
        if channel:
            await channel.send(f"🎵 Đang phát: **{discord.utils.escape_markdown(item['title'])}**")
    except Exception as exc:
        channel = bot.get_channel(text_channels.get(guild_id))
        if channel:
            await channel.send(f'Không phát được bài này: {exc}')
        await play_next(guild_id)

async def after_song(guild_id, error):
    if error:
        print(f'Lỗi phát nhạc: {error}')
    await play_next(guild_id)

@bot.event
async def on_ready():
    if not getattr(bot, '_synced', False):
        await bot.tree.sync()
        bot._synced = True
    print(f'Bot đã sẵn sàng: {bot.user}')

@bot.tree.command(name='play', description='Phát nhạc từ link YouTube hoặc tìm theo tên')
@app_commands.describe(query='Link YouTube hoặc tên bài hát')
async def play(interaction: discord.Interaction, query: str):
    if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.voice:
        await interaction.response.send_message('Bạn cần vào kênh thoại trước.', ephemeral=True)
        return
    voice = interaction.guild.voice_client
    if voice and voice.channel != interaction.user.voice.channel:
        await interaction.response.send_message('Bot đang ở kênh thoại khác.', ephemeral=True)
        return
    await interaction.response.defer()
    try:
        item = await asyncio.to_thread(extract, query)
        if not voice:
            voice = await interaction.user.voice.channel.connect()
        queues[interaction.guild.id].append(item)
        text_channels[interaction.guild.id] = interaction.channel_id
        await interaction.followup.send(f"Đã thêm: **{discord.utils.escape_markdown(item['title'])}**")
        if not voice.is_playing():
            await play_next(interaction.guild.id)
    except Exception as exc:
        await interaction.followup.send(f'Không thêm được bài hát: {exc}')

@bot.tree.command(name='skip', description='Bỏ qua bài hiện tại')
async def skip(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if not voice or not voice.is_playing():
        await interaction.response.send_message('Không có bài nào đang phát.', ephemeral=True)
        return
    if not interaction.user.voice or interaction.user.voice.channel != voice.channel:
        await interaction.response.send_message('Hãy vào cùng kênh thoại với bot.', ephemeral=True)
        return
    voice.stop()
    await interaction.response.send_message('Đã bỏ qua bài hát.')

@bot.tree.command(name='stop', description='Dừng nhạc và xóa hàng đợi')
async def stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if not voice or not interaction.user.voice or interaction.user.voice.channel != voice.channel:
        await interaction.response.send_message('Hãy vào cùng kênh thoại với bot.', ephemeral=True)
        return
    queues[interaction.guild.id].clear()
    if voice.is_playing():
        voice.stop()
    await interaction.response.send_message('Đã dừng và xóa hàng đợi.')

@bot.tree.command(name='leave', description='Cho bot rời kênh thoại')
async def leave(interaction: discord.Interaction):
    voice = interaction.guild.voice_client if interaction.guild else None
    if not voice or not interaction.user.voice or interaction.user.voice.channel != voice.channel:
        await interaction.response.send_message('Hãy vào cùng kênh thoại với bot.', ephemeral=True)
        return
    queues[interaction.guild.id].clear()
    await voice.disconnect()
    await interaction.response.send_message('Bot đã rời kênh thoại.')

bot.run(TOKEN)
