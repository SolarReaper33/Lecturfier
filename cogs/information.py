import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
import psutil
import time
import random
import string
import hashlib
from helper.lecture_scraper import scraper_test
from discord.ext.commands.cooldowns import BucketType
from helper import handySQL
from calendar import monthrange


def get_formatted_time(rem):
    if rem < 3600:
        return f"{round(rem / 60)} minutes"
    if rem < 86400:
        hours = rem // 3600
        return f"{int(hours)} hours {get_formatted_time(rem - hours * 3600)}"
    days = rem // 86400
    return f"{int(days)} days {get_formatted_time(rem - days * 86400)}"


def format_input_date(date):
    # Splits the date either on . or -
    res = date.split(".")
    if len(res) < 3:
        res = date.split("-")
    if len(res) < 3:
        return False
    date_dict = {}
    try:
        date_dict["day"] = int(res[0])
        date_dict["month"] = int(res[1])
        date_dict["year"] = int(res[2])
        if not is_valid_date(date_dict):
            return False
        return date_dict
    except ValueError:
        return False


def is_valid_date(date):
    # checks if a date hasnt passed yet
    if date["year"] < datetime.now().year:
        # Year is passed
        if datetime.now().year + 5 >= date["year"] + 2000 >= datetime.now().year:
            date["year"] = date["year"]+2000
        else:
            return False
    if date["year"] == datetime.now().year:
        if date["month"] < datetime.now().month or date["month"] > 12:
            return False
        if date["month"] == datetime.now().month:
            try:
                max_days = monthrange(date["year"], date["month"])[1]
            except ValueError:
                return False
            if date["day"] <= datetime.now().day or datetime.now().day > max_days:
                return False
    if date["year"] > datetime.now().year + 5:
        return False
    return True


def format_input_time(time_inp):
    # Splits the time on :
    res = time_inp.split(":")
    if len(res) < 2:
        return False
    time_dict = {}
    try:
        time_dict["hour"] = int(res[0])
        time_dict["minute"] = int(res[1])
        if is_valid_time(time_dict):
            return time_dict
        return False
    except ValueError:
        return False


def is_valid_time(time_dict):
    # checks if a time hasnt passed yet
    if 0 <= time_dict["hour"] < 24 and 0 <= time_dict["minute"] < 60:
        return True
    return False


def starting_in(string_date):
    dt = datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S")
    delta = dt - datetime.now()
    return get_formatted_time(delta.total_seconds())


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.script_start = time.time()
        self.db_path = "./data/discord.db"
        self.conn = handySQL.create_connection(self.db_path)

    def get_connection(self):
        """
        Retreives the current database connection
        :return: Database Connection
        """
        if self.conn is None:
            self.conn = handySQL.create_connection(self.db_path)
        return self.conn

    @commands.Cog.listener()
    async def on_ready(self):
        self.script_start = time.time()

    @commands.cooldown(2, 10, BucketType.user)
    @commands.command(aliases=["terms"])
    async def terminology(self, ctx, word=None):
        async with ctx.typing():
            terms = await scraper_test.terminology()
            if word is None:
                embed = discord.Embed(title="PPROG Terminology")
                cont = ""
                for key in terms.keys():
                    cont += f"**- {key}:** {terms[key]}\n"
                if len(cont) > 2000:
                    index = cont.rindex("\n", 0, 1900)
                    cont = cont[0:index]
                    cont += "\n..."
                embed.description = cont
                embed.set_footer(text="URL=https://cgl.ethz.ch/teaching/parallelprog21/pages/terminology.html")
                await ctx.send(embed=embed)
            else:
                if word in terms.keys():
                    cont = f"**{word}**:\n{terms[word]}"
                    embed = discord.Embed(title="PPROG Terminology", description=cont)
                    embed.set_footer(text="URL=https://cgl.ethz.ch/teaching/parallelprog21/pages/terminology.html")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Couldn't find word. soz...")

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(usage="guild")
    async def guild(self, ctx):
        """
        Used to display information about the server.
        """
        guild = ctx.message.guild
        embed = discord.Embed(title=f"Guild Statistics", color=discord.colour.Color.dark_blue())
        embed.add_field(name="Categories", value=f"Server Name:\n"
                                                 f"Server ID:\n"
                                                 f"Member Count:\n"
                                                 f"Categories:\n"
                                                 f"Text Channels:\n"
                                                 f"Voice Channels:\n"
                                                 f"Emoji Count / Max emojis:\n"
                                                 f"Owner:\n"
                                                 f"Roles:")
        embed.add_field(name="Values", value=f"{guild.name}\n"
                                             f"{guild.id}\n"
                                             f"{guild.member_count}\n"
                                             f"{len(guild.categories)}\n"
                                             f"{len(guild.text_channels)}\n"
                                             f"{len(guild.voice_channels)}\n"
                                             f"{len(guild.emojis)} / {guild.emoji_limit}\n"
                                             f"{guild.owner.mention}\n"
                                             f"{len(guild.roles)}")
        await ctx.send(embed=embed)

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(aliases=["source", "code"], usage="info")
    async def info(self, ctx):
        """
        Sends some info about the bot.
        """
        async with ctx.typing():
            b_time = time_up(time.time() - self.script_start)  # uptime of the script
            s_time = time_up(seconds_elapsed())  # uptime of the pc
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory()

            cont = f"**Instance uptime: **`{b_time}`\n" \
                   f"**Computer uptime: **`{s_time}`\n" \
                   f"**CPU: **`{round(cpu)}%` | **RAM: **`{round(ram.percent)}%`\n" \
                   f"**Discord.py Version:** `{discord.__version__}`\n" \
                   f"**Bot source code:** [Click here for source code](https://github.com/markbeep/Lecturfier)"
            embed = discord.Embed(title="Bot Information:", description=cont, color=0xD7D7D7,
                                  timestamp=datetime.now(timezone("Europe/Zurich")))
            embed.set_footer(text=f"Called by {ctx.author.display_name}")
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(usage="token")
    async def token(self, ctx):
        """
        Sends a bot token.
        """
        token = random_string(24) + "." + random_string(6) + "." + random_string(27)
        embed = discord.Embed(title="Bot Token", description=f"||`{token}`||")
        await ctx.send(embed=embed)

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(aliases=["pong", "ding", "pingpong"], usage="ping")
    async def ping(self, ctx):
        """
        Check the ping of the bot
        """
        title = "Pong!"
        if "pong" in ctx.message.content.lower():
            title = "Ping!"
        if "pong" in ctx.message.content.lower() and "ping" in ctx.message.content.lower():
            title = "Ding?"
        if "ding" in ctx.message.content.lower():
            title = "*slap!*"

        embed = discord.Embed(
            title=f"{title} 🏓",
            description=f"🌐 Ping: \n"
                        f"❤ HEARTBEAT:")

        start = time.perf_counter()
        ping = await ctx.send(embed=embed)
        end = time.perf_counter()
        embed = discord.Embed(
            title=f"{title} 🏓",
            description=f"🌐 Ping: `{round((end - start) * 1000)}` ms\n"
                        f"❤ HEARTBEAT: `{round(self.bot.latency * 1000)}` ms")
        await ping.edit(embed=embed)

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(aliases=["cypher"], usage="cipher <amount to displace> <msg>")
    async def cipher(self, ctx, amount=None, *msg):
        """
        This is Caesar's cipher, but instead of only using the alphabet, it uses all printable characters.
        Negative values are allowed and can be used to decipher messages.
        """
        printable = list(string.printable)
        printable = printable[0:-5]
        if len(msg) == 0:
            await ctx.send("No message specified.")
            raise discord.ext.commands.errors.BadArgument
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("Amount is not an int.")
            raise discord.ext.commands.errors.BadArgument
        msg = " ".join(msg)
        encoded_msg = ""
        amount = amount % len(printable)
        for letter in msg:
            index = printable.index(letter) + amount
            if index >= len(printable) - 1:
                index = index - (len(printable))
            encoded_msg += printable[index]

        await ctx.send(f"```{encoded_msg}```")

    @commands.cooldown(4, 10, BucketType.user)
    @commands.command(usage="hash <OpenSSL algo> <msg>")
    async def hash(self, ctx, algo=None, *msg):
        """
        Hash a message using an OpenSSL algorithm (sha256 for example).
        """
        if algo is None:
            await ctx.send("No Algorithm given. `$hash <OPENSSL algo> <msg>`")
            raise discord.ext.commands.errors.BadArgument
        try:
            joined_msg = " ".join(msg)
            msg = joined_msg.encode('UTF-8')
            h = hashlib.new(algo)
            h.update(msg)
            output = h.hexdigest()
            embed = discord.Embed(
                title=f"**Hashed message using {algo.lower()}**",
                colour=0x000000
            )
            embed.add_field(name="Input:", value=f"{joined_msg}", inline=False)
            embed.add_field(name="Output:", value=f"`{output}`", inline=False)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("Invalid hash type. Most OpenSSL algorithms are supported. Usage: `$hash <hash algo> <msg>`")
            raise discord.ext.commands.errors.BadArgument

    @commands.command(aliases=["events"], usage="event [add/view/edit/delete/join/leave] [event name] [date] [time] [description]")
    async def event(self, ctx, command=None, event_name=None, date=None, event_time=None, *event_info):
        """
        - The event command is used to keep track of upcoming events. Each user can add a maximum of two events (this might get changed).
        - When creating an event, the **event name** has to be in quotes if there are multiple words and it can be a maximum of 50 characters, \
        any more and the name gets cut off with "...".
        - The same thing goes for the **description**. The description can be a maximum of 700 characters, any more and it gets cut off with "...".
        - **Date** needs to be in the format `DD.MM.YYYY` or `DD.MM.YY` or `DD-MM-YYYY` or `DD-MM-YY`. Some examples are `13-03-2021` and `20.4.25`.
        - **Time** needs to be in the format `HH:MM`.

        Some examples:
        - `$event add "My Birthday" 13.03.2021 00:00 This day is my birthday hehe :)`
        - `$event add 420BlazeIt 20.4.21 4:20 Send me a dm if you wanna join this event!`
        """
        conn = self.get_connection()
        c = conn.cursor()
        try:
            guild_id = ctx.message.guild.id
            guild_name = ctx.message.guild.name
        except AttributeError:
            guild_id = 0
            guild_name = "Direct Message"

        # Deletes all older events
        c.execute("DELETE FROM Events WHERE EventStartingAt < ?", (str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), ))
        conn.commit()

        if command is None:
            # list all upcoming events sorted by upcoming order
            sql = """   SELECT E.EventName, E.EventStartingAt
                        FROM Events E
                        INNER JOIN DiscordMembers DM on DM.UniqueMemberID = E.UniqueMemberID
                        WHERE DM.DiscordGuildID=?
                        ORDER BY E.EventCreatedAt"""
            c.execute(sql, (guild_id,))
            results = c.fetchall()
            i = 0
            embed = discord.Embed(title=f"Upcoming Events On {guild_name}", color=0xFCF4A3)
            embed.set_footer(text="$event view <name> to get more details about an event")
            for e in results:
                if i == 10:
                    # a max of 10 events are shown
                    break
                dt = datetime.strptime(e[1], "%Y-%m-%d %H:%M:%S")
                form_time = starting_in(e[1])
                embed.add_field(name=e[0], value=f"**At:** {dt}\n**In:** {form_time}")
                i += 1
            if len(results) == 0:
                embed.description = "-- There are no upcoming events --"
            await ctx.send(embed=embed)
        elif command.lower() == "add":
            # check if uniquememberid already exists in db
            uniqueID = handySQL.get_uniqueMemberID(conn, ctx.message.author.id, guild_id)
            c.execute("SELECT EventName FROM Events WHERE UniqueMemberID=?", (uniqueID,))
            result = c.fetchall()
            if len(result) < 2:
                # add the event to the db
                # Make sure the inputs are correct
                if event_name is None or date is None or event_time is None:
                    await ctx.send("ERROR! Incorrect arguments given. Check `$help event` to get more "
                                   f"info about the event command.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument
                date = format_input_date(date)
                if not date:
                    await ctx.send("ERROR! Incorrect date format given or date is passed. Should be `DD.MM.YYYY` or `DD-MM-YYYY`. Check `$help event` to get more "
                                   f"info about the event command.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument
                event_time = format_input_time(event_time)
                if not event_time:
                    await ctx.send("ERROR! Incorrect time format given. Should be `HH:MM`. Check `$help event` to get more "
                                   f"info about the event command.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument

                # Adds the entry to the sql db
                event_description = " ".join(event_info)
                if len(event_description) > 700:
                    event_description = event_description[0: 700] + "..."
                if len(event_name) > 50:
                    event_name = event_name[0: 50] + "..."

                # Check if the same already exists and throw an error if needed
                c.execute("SELECT * FROM Events WHERE EventName LIKE ?", (event_name,))
                if c.fetchone() is not None:
                    await ctx.send("ERROR! There already exists an event with said name! Use a different event name.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument

                try:
                    dt = datetime(date["year"], date["month"], date["day"], event_time["hour"], event_time["minute"])
                except ValueError:
                    await ctx.send(
                        "ERROR! Incorrect date format given or date is passed. Should be `DD.MM.YYYY` or `DD-MM-YYYY`. Check `$help event` to get more "
                        f"info about the event command.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument

                # Inserts event into event database
                c.execute("INSERT INTO Events(EventName, EventCreatedAt, EventStartingAt, EventDescription, UniqueMemberID) VALUES (?,?,?,?,?)",
                          (event_name, str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), str(dt), event_description, uniqueID))
                conn.commit()

                # Inserts user as host to EventJoinedUsers for the newly added event
                row_id = c.lastrowid
                c.execute("SELECT EventID FROM Events WHERE ROWID=?", (row_id,))
                event_id = c.fetchone()[0]
                c.execute("INSERT INTO EventJoinedUsers(EventID, UniqueMemberID, IsHost) VALUES (?,?,?)", (event_id, uniqueID, 1))
                conn.commit()

                # Creates and sends the embed message
                embed = discord.Embed(title="Added New Event", color=0xFCF4A3)
                embed.add_field(name="Event Name", value=event_name, inline=False)
                embed.add_field(name="Event Host", value=ctx.message.author.mention, inline=False)
                embed.add_field(name="Event Starting At", value=str(dt), inline=False)
                embed.add_field(name="Event Description", value=event_description, inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("ERROR! Each member can only add **two** events. (Might get changed in the future)", delete_after=10)
                raise discord.ext.commands.errors.BadArgument
        elif command.lower() == "view":
            if event_name is None:
                await ctx.send(f"ERROR! {ctx.message.author.mention}, you did not specify what event to view. Check `$help event` to get more "
                               f"info about the event command.", delete_after=10)
                raise discord.ext.commands.errors.BadArgument
            else:
                sql = """   SELECT E.EventName, E.EventCreatedAt, E.EventStartingAt, E.EventDescription, DM.DiscordUserID, EventID
                            FROM Events E
                            INNER JOIN DiscordMembers DM on E.UniqueMemberID = DM.UniqueMemberID
                            WHERE E.EventName LIKE ? AND DM.DiscordGuildID=?
                            ORDER BY E.EventStartingAt"""
                c.execute(sql, (f"%{event_name}%", guild_id))
                results = c.fetchall()
                if len(results) == 0:
                    await ctx.send("ERROR! There is no event with a similar name. Simply type `$event` to get a list of upcoming events.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument
                embed = discord.Embed(title="Indepth Event View", color=0xFCF4A3)
                if len(results) > 2:
                    embed.add_field(name="NOTICE",
                                    value="There are more than 2 matches with that event name. Only showing the two closest events.",
                                    inline=False)
                i = 1
                for e in results:
                    # creates a list of all joined members
                    sql = """   SELECT D.DiscordUserID
                                FROM EventJoinedUsers E 
                                INNER JOIN DiscordMembers D on D.UniqueMemberID = E.UniqueMemberID
                                WHERE E.EventID=?"""
                    c.execute(sql, (e[5],))
                    res = c.fetchall()
                    joined_users_msg = f"Total: {len(res)}"
                    counter = 0
                    for row in res:
                        joined_users_msg += f"\n> <@{row[0]}>"
                        if counter >= 10:
                            break
                        counter += 1

                    embed.add_field(name="Event Name", value=e[0])
                    embed.add_field(name="Host", value=f"<@{e[4]}>")
                    embed.add_field(name="Joined Users", value=joined_users_msg)
                    embed.add_field(name="Date", value=e[2])
                    embed.add_field(name="Starting in", value=starting_in(e[2]))
                    embed.add_field(name="Created on", value=e[1])
                    embed.add_field(name="Event Description", value=e[3])

                    # if not last field, add a spacer
                    if i < len(results):
                        embed.add_field(name="\u200b", value="``` ```", inline=False)
                    i += 1
                await ctx.send(embed=embed)
        elif command.lower() == "delete":
            # delete the entry
            uniqueID = handySQL.get_uniqueMemberID(conn, ctx.message.author.id, guild_id)
            if event_name is None:
                event_name = ""
            c.execute("SELECT EventName FROM Events WHERE UniqueMemberID=? AND EventName LIKE ?", (uniqueID, f"%{event_name}%"))
            result = c.fetchall()
            if len(result) == 0:
                await ctx.send("ERROR! You don't have any active events or you might have misspelled the event name.")
                raise discord.ext.commands.errors.BadArgument
            if len(result) > 1:
                await ctx.send("ERROR! There are multiple events matching that name. Type the whole name to delete the event.\n"
                               f'`$event delete "{result[0][0]}"` or\n'
                               f'`$event delete "{result[1][0]}"`')
                raise discord.ext.commands.errors.BadArgument
            ev_name = result[0][0]
            if event_name is None or event_name.lower() != ev_name.lower():
                await ctx.send("ERROR! You did not specify what event to delete. To delete your event type "
                               f'`$event delete "{ev_name}"`')
                raise discord.ext.commands.errors.BadArgument
            c.execute("DELETE FROM Events WHERE UniqueMemberID=? AND EventName=?", (uniqueID, ev_name))
            conn.commit()
            embed = discord.Embed(title="Deleted Event",
                                  description=f"**Name of deleted event:** {event_name}\n"
                                              f"**Event host:** {ctx.message.author.mention}",
                                  color=0xFCF4A3)
            await ctx.send(embed=embed)
        elif command.lower() in ["join", "leave"]:
            if event_name is None:
                await ctx.send(f"ERROR! {ctx.message.author.mention}, you did not specify what event to {command.lower()}. Check `$help event` to get more "
                               f"info about the event command.", delete_after=10)
                raise discord.ext.commands.errors.BadArgument
            sql = """   SELECT E.EventID, E.EventName
                        FROM Events E
                        INNER JOIN DiscordMembers D on D.UniqueMemberID = E.UniqueMemberID
                        WHERE E.EventName LIKE ? AND D.DiscordGuildID=?"""
            c.execute(sql, (event_name, guild_id))
            event_result = c.fetchone()
            if event_result is None:
                await ctx.send(f"ERROR! {ctx.message.author.mention}, could not find an event with that name.", delete_after=10)
                raise discord.ext.commands.errors.BadArgument

            # Checks if the user already joined the event
            uniqueID = handySQL.get_uniqueMemberID(conn, ctx.message.author.id, guild_id)
            c.execute("SELECT IsHost FROM EventJoinedUsers WHERE EventID=? AND UniqueMemberID=?", (event_result[0], uniqueID))
            res = c.fetchone()

            if command.lower() == "join":
                if res is not None:
                    if res[0] == 1:
                        await ctx.send(f"ERROR! {ctx.message.author.mention}, you are the host of the event `{event_result[1]}`. "
                                       f"You don't need to join.", delete_after=10)
                    else:
                        await ctx.send(f"ERROR! {ctx.message.author.mention}, you already joined the event `{event_result[1]}`.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument

                # Joins the user to the event
                c.execute("INSERT INTO EventJoinedUsers(EventID, UniqueMemberID) VALUES (?,?)", (event_result[0], uniqueID))
                conn.commit()
                embed = discord.Embed(title="Joined Event", description=f"Added {ctx.message.author.mention} to event `{event_result[1]}`.", color=0xFCF4A3)
                await ctx.send(embed=embed)
            elif command.lower() == "leave":
                if res is None:
                    await ctx.send(f"ERROR! {ctx.message.author.mention}, you can't leave an event you haven't even joined yet. "
                                   f"The event in question: `{event_result[1]}`.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument
                if res[0] == 1:
                    await ctx.send(f"ERROR! {ctx.message.author.mention}, you are the host of `{event_result[1]}`. "
                                   f"You can't leave events you are the host of.", delete_after=10)
                    raise discord.ext.commands.errors.BadArgument

                # Removes the user from that event
                c.execute("DELETE FROM EventJoinedUsers WHERE EventID=? AND UniqueMemberID=?", (event_result[0], uniqueID))
                conn.commit()

                embed = discord.Embed(title="Left Event", description=f"Removed {ctx.message.author.mention} from event `{event_result[1]}`.", color=0xffa500)
                await ctx.send(embed=embed)

        else:
            await ctx.send(f"ERROR! {ctx.message.author.mention}, the command you used is not recognized. Check `$help event` to get more "
                           f"info about the event command.", delete_after=10)
            raise discord.ext.commands.errors.BadArgument


def setup(bot):
    bot.add_cog(Information(bot))


def time_up(t):
    if t <= 60:
        return f"{int(t)} seconds"
    elif 3600 > t > 60:
        minutes = t // 60
        seconds = t % 60
        return f"{int(minutes)} minutes and {int(seconds)} seconds"
    elif t >= 3600:
        hours = t // 3600  # Seconds divided by 3600 gives amount of hours
        minutes = (t % 3600) // 60  # The remaining seconds are looked at to see how many minutes they make up
        seconds = (t % 3600) - minutes * 60  # Amount of minutes remaining minus the seconds the minutes "take up"
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes and {int(seconds)} seconds"
        else:
            return f"{int(hours)} hours, {int(minutes)} minutes and {int(seconds)} seconds"


def seconds_elapsed():
    now = datetime.now()
    current_timestamp = time.mktime(now.timetuple())
    return current_timestamp - psutil.boot_time()


def random_string(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
