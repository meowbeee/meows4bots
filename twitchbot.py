import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from datetime import datetime, timedelta

import asyncio
import logging
import random
from typing import TYPE_CHECKING

import asqlite

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-library-read,user-read-playback-state,user-modify-playback-state,user-read-currently-playing,app-remote-control,streaming"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=os.getenv("SP_CLIENT"), client_secret=os.getenv("SP_SECRET"), redirect_uri=os.getenv("SP_REDIR")))


if TYPE_CHECKING:
    import sqlite3


LOGGER: logging.Logger = logging.getLogger("Bot")

# Consider using a .env or another form of Configuration file!
CLIENT_ID: str = os.getenv("CLIENT")  # The CLIENT ID from the Twitch Dev Console
CLIENT_SECRET: str = os.getenv("SECRET")  # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = os.getenv("BOT")  # The Account ID of the bot user...
OWNER_ID = os.getenv("USER")  # Your personal User ID..


class Bot(commands.AutoBot):
    def __init__(self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]) -> None:
        self.token_database = token_database

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix=self.custom_prefix,
            subscriptions=subs,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(CommandComponent(self))

    async def custom_prefix(self, bot, message: twitchio.ChatMessage) -> None:
        # The prefix will be ? if the chatters name startswith "cool"
        # Otherwise it will default to "!"
        # This coroutine can be used to connect to a cache or database etc to provide
        # custom settable prefixes for example...

        if "gup" == message.text:
            return "g"

        return "!"

    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


class CommandComponent(commands.Component):
    # An example of a Component with some simple commands and listeners
    # You can use Components within modules for a more organized codebase and hot-reloading.

    def __init__(self, bot: Bot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot
        self.gup_time = datetime.now()

    # An example of listening to an event
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")

    @commands.command(aliases=["gupcord"])
    async def discord(self, ctx: commands.Context) -> None:
        """Command for providing the Discord invite to gupcord.

        !discord
        !gupcord
        """
        await ctx.reply(f"Join the gupcord here! https://discord.gg/FbtcAN5Ynh")

    @commands.command()
    async def up(self, ctx: commands.Context) -> None:
        """Sends gup. gup. gup. gup. gup.

        gup
        """
        if datetime.now() <= self.gup_time:
            print("unable to gup.")
            return
        else:
            self.gup_time = datetime.now() + timedelta(seconds=37)
        await ctx.reply(f"gup")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Command for reporting what is currently being listened to on Spotify.

        !np
        !nowplaying
        """
        playback = sp.current_playback()
        if playback['is_playing'] is False:
            await ctx.reply("nothing is currently playing on spotify")
        else:
            current_s = playback['progress_ms']//1000
            (current_m, current_s) = divmod(current_s, 60)
            current_play = f"{current_m:02.0f}:{current_s:02.0f}"

            total_s = playback['item']['duration_ms']//1000
            (total_m, total_s) = divmod(total_s, 60)
            total_play = f"{total_m:02.0f}:{total_s:02.0f}"

            # song_url = playback['item']['external_urls']['spotify']
            song_name = playback['item']['name']
            artists_len = len(playback['item']['artists'])
            for idx, artist in enumerate(playback['item']['artists']):
                name = artist['name']
                if idx == 0:
                    artists = name
                elif artists_len == 2:
                    artists += f" and {name}"
                elif idx == artists_len - 1:
                    artists += f", and {name}"
                else:
                    artists += f", {name}"
            await ctx.reply(f"meows is currently listening to {song_name} by {artists} ({current_play}/{total_play})")

    # @commands.command()
    # async def say(self, ctx: commands.Context, *, message: str) -> None:
    #     """Command which repeats what the invoker sends.

    #     !say <message>
    #     """
    #     await ctx.send(message)

    # @commands.command()
    # async def add(self, ctx: commands.Context, left: int, right: int) -> None:
    #     """Command which adds to integers together.

    #     !add <number> <number>
    #     """
    #     await ctx.reply(f"{left} + {right} = {left + right}")

    # @commands.command()
    # async def choice(self, ctx: commands.Context, *choices: str) -> None:
    #     """Command which takes in an arbitrary amount of choices and randomly chooses one.

    #     !choice <choice_1> <choice_2> <choice_3> ...
    #     """
    #     await ctx.reply(f"You provided {len(choices)} choices, I choose: {random.choice(choices)}")

    # @commands.command(aliases=["thanks", "thank"])
    # async def give(self, ctx: commands.Context, user: twitchio.User, amount: int, *, message: str | None = None) -> None:
    #     """A more advanced example of a command which has makes use of the powerful argument parsing, argument converters and
    #     aliases.

    #     The first argument will be attempted to be converted to a User.
    #     The second argument will be converted to an integer if possible.
    #     The third argument is optional and will consume the reast of the message.

    #     !give <@user|user_name> <number> [message]
    #     !thank <@user|user_name> <number> [message]
    #     !thanks <@user|user_name> <number> [message]
    #     """
    #     msg = f"with message: {message}" if message else ""
    #     await ctx.send(f"{ctx.chatter.mention} gave {amount} thanks to {user.mention} {msg}")

    # @commands.group(invoke_fallback=True)
    # async def socials(self, ctx: commands.Context) -> None:
    #     """Group command for our social links.

    #     !socials
    #     """
    #     await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

    # @socials.command(name="discord")
    # async def socials_discord(self, ctx: commands.Context) -> None:
    #     """Sub command of socials that sends only our discord invite.

    #     !socials discord
    #     """
    #     await ctx.send("discord.gg/...")


async def setup_tdb(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Create our token table, if it doesn't exist..
    # You should add the created files to .gitignore or potentially store them somewhere safer
    # This is just for example purposes...

    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens...
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == BOT_ID:
                continue

            subs.extend([eventsub.ChatMessageSubscription(broadcaster_user_id=row["user_id"], user_id=BOT_ID)])

    return tokens, subs


# async def setup_viewerdb(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:

# Our main entry point for our Bot
# Best to setup_logging here, before anything starts
def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb:
            tokens, subs = await setup_tdb(tdb)

            async with Bot(token_database=tdb, subs=subs) as bot:
                for pair in tokens:
                    await bot.add_token(*pair)

                await bot.start(load_tokens=False)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()
