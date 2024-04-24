import discord
from discord.ext import commands, tasks
import asyncio
import sqlite3
from itertools import cycle
from discord.ui import button, Button, View

# Initialize SQLite connection and cursor
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create user_channels table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS user_channels
             (channel_id int, user_id int)''')

# Create user_messages table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS user_messages
             (user_id int, message_id int)''')

client = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

bot_status = cycle(["Colosseum Roleplay"])
token = 'MTE2NzkwMzY1Mzg1NjgxMzA5Ng.GNolly.1FHsa-pDPE-4xp58kSlUgRgzbR3ZWabR84ixsw'

questions = [
    "```Ποιά είναι η πραγματική σας ηλικία;```",
    "```Πόσες ώρες FiveM έχετε; (θα πρέπει να πάτε στο προφιλ σας στο steam να πατήσετε δεξί κλικ να κάνετε αντιγραφή τον συνδεσμο και να μας τον στηλετε )```",
    "```Έχεις κάποια παρέα ή ομάδα στον Server ή θα έρθεις μόνος σου στην πόλη; [αν έχεις πρέπει να στήλεις το discord link της ομάδας]```",
    "```Περιέγραψε μας την ιστορία του χαρακτήρα που θέλεις να παίξεις; Δηλαδή εξήγησε μας το ποιος είναι και για ποιό λόγο ήρθε στην πόλη μας ;```",
    # Add more questions here...
]

user_answers = {}

@tasks.loop(seconds=5)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

@client.event
async def on_ready():
    # await client.tree.sync()  # Removing this line since 'tree' attribute doesn't exist
    print("Koster developer discord base")
    print()
    print("█████╗█████╗█████╗█████╗█████╗█████╗")
    print("╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝")
    print(f'Welcome aboard captain all systems online we have been logged in as {client.user}')
    change_status.start()

async def send_question_button(channel, question_number, user_id):
    if question_number < len(questions):
        create_button = CloseButton(channel.id, None)
        await channel.send(questions[question_number], view=create_button)

@client.event
async def on_message(message):
    channel = message.channel  # Define channel variable here
    if isinstance(channel, discord.DMChannel):
        return  # Ignore messages in DMs

    await client.process_commands(message)

    if channel.topic and "DO NOT CHANGE THE TOPIC OF THIS CHANNEL" in channel.topic:
        if message.author.id in user_answers:
            user_answers[message.author.id].append(message.content)
            if len(user_answers[message.author.id]) == len(questions):
                await send_answers_to_channel(channel)
            else:
                await send_question_button(channel, len(user_answers[message.author.id]), message.author.id)

    if channel.id == 1171529674858446868:
        await message.delete()
        await asyncio.sleep(1)
        await send_question_button(channel, 0, message.author.id)  # Send the first question as an embed

    # Check if all questions have been answered and send closing message
    if message.author.id in user_answers and len(user_answers[message.author.id]) == len(questions):
        closing_message = "**Το application σου έχει καταγραφεί. Μπορείτε να το κλείσετε πατώντας το κουμπί 'Close'.**"
        view = CloseButton(channel.id, None)  # Create the CloseButton view
        await channel.send(closing_message, view=view)  # Include the CloseButton in the message
        await send_log(
            title="Application Closed",
            description=f"Closed by {message.author.mention}",
            color=discord.Color.green(),
            guild=message.guild
        )

async def send_answers_to_channel(channel):
    # Retrieve the user's ID associated with the channel ID from the database
    c.execute("SELECT user_id FROM user_channels WHERE channel_id=?", (channel.id,))
    row = c.fetchone()
    if row:
        user_id = row[0]
    else:
        print("User ID not found for the channel.")
        return

    # Get the user object
    user = channel.guild.get_member(user_id)
    if user is None:
        print("User not found.")
        return

    answers = user_answers[user.id]
    user_mention = f"<@{user.id}>"  # Mentioning the user who answered
    embed = discord.Embed(title="Application Answers", color=discord.Color.green())
    embed.description = f"Answers submitted by: {user_mention}"  # Mentioning the user in the description
    for i, (question, answer) in enumerate(zip(questions, answers), start=1):
        embed.add_field(name=f"Question {i}", value=f"**{question}**\n{answer}", inline=False)
    destination_channel = client.get_channel(1231617691475906673)
    message = await destination_channel.send(embed=embed, view=CreateButtons(channel.id))  # Pass the channel ID here

    # Store the message ID associated with the user ID in the database for later reference
    c.execute("INSERT INTO user_messages VALUES (?, ?)", (user.id, message.id))
    conn.commit()

    await send_log(
        title="Application Answers Sent",
        description=f"Answers sent by {user_mention}",
        color=discord.Color.green(),
        guild=channel.guild
    )

async def send_log(title: str, guild: discord.Guild, description: str, color: discord.Color):
    log_channel = guild.get_channel(1231617910242541629)
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    await log_channel.send(embed=embed)

class CloseButton(View):
    def __init__(self, channel_id, embed):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.embed = embed

    @button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="trash")
    async def trash(self, interaction: discord.Interaction, button: Button):
     await interaction.response.defer()
     await interaction.channel.send("Το application σας θα διαγραφτεί σε 3 δευτερόλεπτα!")
     await asyncio.sleep(3)

     await interaction.channel.delete()
     await send_log(
        title="Το application διαγράφτηκε",
        description=f"**Απο τον/την** {interaction.user.mention}\n **Κανάλι:** `{interaction.channel.name}` • `{interaction.channel.id}`",
        color=discord.Color.red(),
        guild=interaction.guild
     )

class CreateButtons(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.correct_button_disabled = False
        self.decline_button_disabled = False
        self.trash_button_disabled = False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅", custom_id="correct_ticket")
    async def correct(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.correct_button_disabled:
            await interaction.response.defer()

            # Retrieve the user's ID associated with the channel ID from the database
            c.execute("SELECT user_id FROM user_channels WHERE channel_id=?", (self.channel_id,))
            row = c.fetchone()
            if row:
                user_id = row[0]
            else:
                print("User ID not found for the channel.")
                return

            # Get the user object
            user = interaction.guild.get_member(user_id)
            if user is None:
                print("User not found.")
                return

            # Send a private message to the user
            dm_message = f"**Η αίτηση για Allowlist του/της** {user.mention} **έγινε αποδεκτή, παρακαλώ θερμά διαβάστε τα** <#1166002470670045295>"
            await user.send(dm_message)

            # Assign the role to the user
            role_id = 1231618511734837322
            role = interaction.guild.get_role(role_id)
            if role:
                await user.add_roles(role)
                # Inform the server about the action (optional)
                await interaction.followup.send(f"Ο χρήστης {user.mention} έλαβε το μύνημα και πήρε τον ρόλο allowlist.", ephemeral=True)
            else:
                print("Role not found.")  # Handle if the role is not found in the server

            # Disable the button
            self.correct_button_disabled = True
            self.correct.disabled = True

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.secondary, emoji="❌", custom_id="decline_ticket")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.decline_button_disabled:
            await interaction.response.defer()

            # Retrieve the user's ID associated with the channel ID from the database
            c.execute("SELECT user_id FROM user_channels WHERE channel_id=?", (self.channel_id,))
            row = c.fetchone()
            if row:
                user_id = row[0]
            else:
                print("User ID not found for the channel.")
                return

            # Get the user object
            user = interaction.guild.get_member(user_id)
            if user is None:
                print("User not found.")
                return

            # Send a private message to the user
            dm_message = f"**Η αίτηση για Allowlist του/της** {user.mention} **απορρίφθηκε λόγο ελλιπής γνώσης. Έχεις το δικαίωμα να ξανά υποβάλεις νέα αίτηση μετά από 5 ημέρες.**"
            await user.send(dm_message)

            await send_log(
                title="Application Declined",
                description=f"Declined by {interaction.user.mention}, application: {self.channel_id}",
                color=discord.Color.red(),
                guild=interaction.guild
            )

            # Disable the button
            self.decline_button_disabled = True
            self.decline.disabled = True



    @discord.ui.button(label="Trash", style=discord.ButtonStyle.red, emoji="🗑️", custom_id="trash_ticket")
    async def trash(self, interaction: discord.Interaction, button: discord.ui.Button):
     if not self.trash_button_disabled:
        await interaction.response.defer()

        channel = interaction.guild.get_channel(self.channel_id)

        if channel:
            await channel.delete()
            print("Channel deleted successfully.")
        else:
            print("Channel not found. Channel ID:", self.channel_id)

        # Introduce a delay before attempting to fetch the channel again
        await asyncio.sleep(2)

        # Fetch the application channel/ticket
        application_channel = interaction.guild.get_channel(self.channel_id)

        if application_channel:
            await send_log(
                title="Το application διαγράφτηκε",
                description=f"**Απο τον/την** {interaction.user.mention}\n **Κανάλι:** {application_channel.mention} • `{self.channel_id}`",
                color=discord.Color.red(),
                guild=interaction.guild
            )
        else:
            print("Application channel not found. Channel ID:", self.channel_id)

        # Disable the button
        self.trash_button_disabled = True
        self.trash.disabled = True




@client.command(name="app")
@commands.has_permissions(administrator=True)
async def ticket(ctx):
    embed = discord.Embed(title="", description="```Για να αποκτήσετε Allowlist για τον server μας πατήστε το κουμπί και συμπληρώστε την φόρμα. Η αίτηση σας θα απαντηθεί εντός μερικών ωρών```", colour=discord.Colour(int("FF9933", 16)))  # Set the embed color here
    embed.set_author(name="Colosseum Roleplay", icon_url="https://cdn.discordapp.com/attachments/1141113959072682077/1226523615692984420/a_49827f07fbd5d1f0a0b6044750162cd9.gif?ex=66251421&is=66129f21&hm=46aac501bd26cd7e849b8a942d820aab43bce78bd74d8302e61a3a4c1b7ae401&")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1141113959072682077/1226523615692984420/a_49827f07fbd5d1f0a0b6044750162cd9.gif?ex=66251421&is=66129f21&hm=46aac501bd26cd7e849b8a942d820aab43bce78bd74d8302e61a3a4c1b7ae401&")
    view = CreateButton(ctx.channel.id, embed)  # Pass the channel ID and embed here
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

async def send_log(title: str, guild: discord.Guild, description: str, color: discord.Color, **kwargs):
    log_channel = guild.get_channel(1231617910242541629)
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    await log_channel.send(embed=embed)

class CreateButton(discord.ui.View):
    def __init__(self, channel_id, embed):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.embed = embed

    @discord.ui.button(label="Get Allowlist", style=discord.ButtonStyle.success, emoji="✅", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=1231617474445967430)
        for ch in category.text_channels:
            if ch.topic == f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!":
                await interaction.followup.send("Έχεις ίδη ένα application ανοιχτό {0}".format(ch.mention), ephemeral=True)
                return

        r1: discord.Role = interaction.guild.get_role(1225000387627581473)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await category.create_text_channel(
            name=f"✅allowlistapp-of-{interaction.user}",
            topic=f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!",
            overwrites=overwrites
        )

        # Store the channel ID and user ID in the database
        c.execute("INSERT INTO user_channels VALUES (?, ?)", (channel.id, interaction.user.id))
        conn.commit()

        user_answers[interaction.user.id] = []
        await channel.send(questions[0])

        await send_log(
            title="Το application δημιουργήθηκε",
          description=f"**Απο τον/την** {interaction.user.mention}\n **Κανάλι:** `{interaction.channel.name}` • `{interaction.channel.id}`",
            color=discord.Color.green(),
            guild=interaction.guild
        )

client.run(token)
