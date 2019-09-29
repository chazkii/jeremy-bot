import asyncio
import io
import logging
import os
import re

import discord
import requests
import sqlite3

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("Started: Database setup")
conn = sqlite3.connect("jeremy-bot.db")
c = conn.cursor()
c.execute(
    """
    CREATE TABLE IF NOT EXISTS guild(
        id          INTEGER PRIMARY KEY ASC,
        discord_id  INTEGER UNIQUE,
        name        TEXT,
        period_s    INTEGER DEFAULT 1200
    )
"""
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS channel(
        id          INTEGER PRIMARY KEY ASC, 
        name        TEXT,
        guild_id    INTEGER,
        FOREIGN KEY(guild_id) REFERENCES guild(id)
    )
"""
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS admin(
        id          INTEGER PRIMARY KEY ASC, 
        username    TEXT,
        guild_id    INTEGER,
        UNIQUE(username, guild_id),
        FOREIGN KEY(guild_id) REFERENCES guild(id)
    )
"""
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS entry(
        id          INTEGER PRIMARY KEY ASC, 
        message     TEXT,
        image_url   TEXT,
        guild_id    INTEGER,
        FOREIGN KEY(guild_id) REFERENCES guild(id)
    )
"""
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS display_name(
        id          INTEGER PRIMARY KEY ASC, 
        name        TEXT,
        guild_id    INTEGER,
        UNIQUE(name, guild_id)
        FOREIGN KEY(guild_id) REFERENCES guild(id)
    )
"""
)
conn.commit()
log.info("Finished: database setup")


IMAGE_URL = "https://picsum.photos/200"
DEFAULT_ADMIN = "ruckusmaker"
URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
CREATE_REGEX = fr"^\!create '([\d\w\s]*)' ({URL_REGEX})$"
create_regex = re.compile(CREATE_REGEX)


class MyClient(discord.Client):
    # TODO: define prefix to triggering bot

    async def on_ready(self):
        # TODO: create task per guild
        log.info("Started: Initial data setup")
        for guild in self.guilds:
            c.execute(
                """INSERT INTO guild(discord_id, name) VALUES(?, ?) ON CONFLICT(discord_id) DO NOTHING""",
                (guild.id, guild.name),
            )
            c.execute(
                """INSERT INTO admin(username, guild_id) VALUES(?, ?) ON CONFLICT(username, guild_id) DO NOTHING""",
                (DEFAULT_ADMIN, c.lastrowid)
            )
        conn.commit()
        log.info("Finished: Initial data setup")
        log.info("Started: Initial task scheduling")
        c.execute("SELECT name, period_s FROM guild")
        rows = c.fetchall()

        for guild in self.guilds:
            for row in rows:
                if guild.name == row[0]:
                    self.loop.create_task(self.spam_message(guild, row[1]))
                    break
        log.info("Finished: Initial task scheduling")

    async def on_message(self, message):
        c.execute("""SELECT admin.username FROM admin JOIN guild WHERE guild.discord_id = ?""",
                  (message.author.guild.id,))
        usernames = c.fetchall()
        if message.author.display_name not in [u[0] for u in usernames]:
            log.info(f"Author {message.author} is not an admin! ignoring message")
        else:
            result = create_regex.search(message.content)
            if not result:
                log.info(f"No understandable content in {message.content}")
                return
            quote = result.group(1)
            image_url = result.group(2)
            c.execute("""SELECT id from guild WHERE guild.discord_id = ?""",
                      (message.author.guild.id,))
            row = c.fetchone()
            guild_id = row[0]
            log.info((quote, image_url, guild_id))
            c.execute("""INSERT INTO entry(message, image_url, guild_id) VALUES(?,?,?)""",
                      (quote, image_url, guild_id))
            conn.commit()
            log.info(f"Loaded {quote} {image_url}")

    async def spam_message(self, guild, period_s):
        # TODO: make this reschedulable on update of period
        while True:
            channel = guild.channels[1]
            c.execute("SELECT message, image_url FROM entry JOIN guild WHERE guild.discord_id = ?",
                      (guild.id,))
            row = c.fetchone()
            if row is not None:
                message, image_url = row
                img_data = requests.get(image_url).content
                with open("image_data.jpg", "wb") as f:
                    f.write(img_data)
                # TODO: use a context manager scope temporary file or create cache
                # TODO: use filename in url or metadata for filename
                await channel.send(message, file=discord.File(open("image_data.jpg", "rb")))
                # TODO: have local cache for image
                print(f"Sleeping for {period_s} seconds")
                # TODO: change display name after every post as it is an async task
                # TODO: source display names from sqlite3
                # TODO: fix below as now working (not changing username or display name)
                await self.user.edit(username="charlierulestheworld")
            else:
                log.info("No available data! Please configure")
            await asyncio.sleep(period_s)


client = MyClient()
client.run(os.getenv("DISCORD_TOKEN"))
conn.close()
# how to add timer to event loop
