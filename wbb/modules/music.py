"""
MIT License

Copyright (c) 2021 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import unicode_literals
from urllib.parse import urlparse
import youtube_dl
import aiohttp
import aiofiles
import os
import ffmpeg
from random import randint
from hurry.filesize import size as format_size
from pyrogram import filters
from wbb import app, SUDOERS, arq
from wbb.core.decorators.errors import capture_err
from wbb.utils.pastebin import paste
from wbb.utils.functions import file_size_from_url


__MODULE__ = "Music"
__HELP__ = """/ytmusic [link] To Download Music From Various Websites Including Youtube.
/saavn [query] To Download Music From Saavn.
/deezer [query] To Download Music From Deezer.
/lyrics [query] To Get Lyrics Of A Song."""

is_downloading = False


@app.on_message(filters.command("ytmusic") & ~filters.edited)
@capture_err
async def music(_, message):
    global is_downloading
    if len(message.command) != 2:
        await message.reply_text("/ytmusic needs a link as argument")
        return
    link = message.text.split(None, 1)[1]
    if is_downloading:
        await message.reply_text("Another download is in progress, try again after sometime.")
        return
    is_downloading = True
    m = await message.reply_text(f"Downloading {link}",
                                 disable_web_page_preview=True)
    try:
        with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            if int(float(info_dict['duration'])) > 600:
                await m.edit("This music cannot be downloaded as it's too long.")
                is_downloading = False
                return
            ydl.process_info(info_dict)
            audio_file = ydl.prepare_filename(info_dict)
            basename = audio_file.rsplit(".", 1)[-2]
            if info_dict['ext'] == 'webm':
                audio_file_opus = basename + ".opus"
                ffmpeg.input(audio_file).output(audio_file_opus, codec="copy").run()
                os.remove(audio_file)
                audio_file = audio_file_opus
            title = info_dict['title']
            performer = info_dict['uploader']
            duration = int(float(info_dict['duration']))
    except Exception as e:
        is_downloading = False
        await m.edit(str(e))
        return
    await message.reply_audio(audio_file, duration=duration, performer=performer,
                              title=title)
    await m.delete()
    os.remove(audio_file)
    is_downloading = False


# Funtion To Download Song
async def download_song(url):
    song_name = f"{randint(6969, 6999)}.mp3"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(song_name, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return song_name


# Jiosaavn Music


@app.on_message(filters.command("saavn") & ~filters.edited)
@capture_err
async def jssong(_, message):
    global is_downloading
    if len(message.command) < 2:
        await message.reply_text("/saavn requires an argument.")
        return
    if is_downloading:
        await message.reply_text("Another download is in progress, try again after sometime.")
        return
    is_downloading = True
    text = message.text.split(None, 1)[1]
    query = text.replace(" ", "%20")
    m = await message.reply_text("Searching...")
    try:
        songs = await arq.saavn(query)
        sname = songs[0].song
        slink = songs[0].media_url
        ssingers = songs[0].singers
        await m.edit("Downloading")
        song = await download_song(slink)
        await m.edit("Uploading")
        await message.reply_audio(
                audio=song,
                title=sname,
                caption=f"「 `{format_size(await file_size_from_url(slink))}` 」",
                performer=ssingers,
                duration=int(songs[0].duration)
                )
        os.remove(song)
        await m.delete()
    except Exception as e:
        is_downloading = False
        await m.edit(str(e))
        return
    is_downloading = False

# Deezer Music


@app.on_message(filters.command("deezer") & ~filters.edited)
@capture_err
async def deezsong(_, message):
    global is_downloading
    if len(message.command) < 2:
        await message.reply_text("/deezer requires an argument.")
        return
    if is_downloading:
        await message.reply_text("Another download is in progress, try again after sometime.")
        return
    is_downloading = True
    text = message.text.split(None, 1)[1]
    query = text.replace(" ", "%20")
    m = await message.reply_text("Searching...")
    try:
        songs = await arq.deezer(query, 1)
        title = songs[0].title
        url = songs[0].url
        artist = songs[0].artist
        await m.edit("Downloading")
        song = await download_song(url)
        await m.edit("Uploading")
        await message.reply_audio(
                audio=song,
                title=title,
                performer=artist,
                duration=songs[0].duration,
                caption=f"「 `{format_size(await file_size_from_url(url))}` 」")
        os.remove(song)
        await m.delete()
    except Exception as e:
        is_downloading = False
        await m.edit(str(e))
        return
    is_downloading = False

# Lyrics


@app.on_message(filters.command("lyrics"))
async def lyrics_func(_, message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:**\n/lyrics [QUERY]")
        return
    m = await message.reply_text("**Searching**")
    query = message.text.strip().split(None, 1)[1]
    song = await arq.lyrics(query)
    lyrics = song.lyrics
    if len(lyrics) < 4095:
        await m.edit(f"__{lyrics}__")
        return
    lyrics = await paste(lyrics)
    await m.edit(f"**LYRICS_TOO_LONG:** [URL]({lyrics})")
