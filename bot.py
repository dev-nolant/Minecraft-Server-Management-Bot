import discord
from discord.ext import commands
import requests
import os
import random
import subprocess
import asyncio
import json
import time

DISCORD_TOKEN = 'TOKEN'
MINECRAFT_SERVER_URL = "https://piston-data.mojang.com/v1/objects/45810d238246d90e811d896f87b14695b7fb6839/server.jar"
SESSION_FILE = "server_sessions.json"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# Store session data for each thread
bot.thread_sessions = {}

# Function to generate a random high port number
def generate_random_port():
    return random.randint(30000, 65535)

# Get the public IP of the Droplet
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org", timeout=60)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return "Unable to retrieve IP"

# Load server sessions from a file to persist data across bot restarts
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as file:
            bot.thread_sessions = json.load(file)

# Save server sessions to a file
def save_sessions():
    with open(SESSION_FILE, "w") as file:
        json.dump(bot.thread_sessions, file)

# Start the Minecraft server in a screen session
async def start_minecraft_server(screen_session_name, server_dir):
    try:
        start_command = f"screen -dmS {screen_session_name} sh -c 'java -Xmx1G -Xms1G -jar minecraft_server.jar nogui | tee server.log'"
        subprocess.run(start_command, shell=False, cwd=server_dir, check=True)
        log_file_path = os.path.join(server_dir, "server.log")
        server_ready = await wait_for_server_ready(log_file_path)
        return server_ready
    except subprocess.CalledProcessError as e:
        print(f"Error starting Minecraft server: {e}")
        return False

# Wait for the server to be ready by checking the log file for the "Done" message
async def wait_for_server_ready(log_file_path):
    for attempt in range(36):  # Check every 5 seconds for up to 3 minutes
        await asyncio.sleep(5)
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log_file:
                logs = log_file.read()
                if "Done" in logs:
                    print("Minecraft server is ready.")
                    return True
                else:
                    print("Waiting for Minecraft server to start...")
        else:
            print("Server log file not found yet, waiting...")
    print("Minecraft server startup timed out.")
    return False

# Stop the Minecraft server without removing the session data
async def stop_server(screen_session_name, thread):
    subprocess.run(f"screen -S {screen_session_name} -X stuff 'stop\n'", shell=True)
    await thread.send("The server has been stopped.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    load_sessions()
    await tree.sync()  # Sync commands globally
    print("Slash commands synced.")

# Create or retrieve the private thread for server management
async def get_or_create_thread(interaction, session_info):
    try:
        thread_id = session_info.get("thread_id")
        if thread_id:
            thread = interaction.guild.get_thread(thread_id)
            if thread:
                print(f"Thread found for user {interaction.user.id}")
                return thread
            else:
                print(f"No thread found for user {interaction.user.id}. Creating a new one.")
        
        # Create a new thread if not found or if it's the first time
        thread = await interaction.channel.create_thread(
            name=f"Server Management for {interaction.user.name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )
        
        # Add the user to their private thread
        await thread.add_user(interaction.user)
        print(f"Added user {interaction.user.id} to their private thread.")

        # Update thread ID in session info and save
        session_info["thread_id"] = thread.id
        save_sessions()
        return thread
    except Exception as e:
        print(f"Error creating thread: {e}")
        return None

@tree.command(name="minecraft", description="Start a Minecraft server.")
async def minecraft(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    server_dir = os.path.expanduser(f"~/minecraft_server_{user_id}")

    # Acknowledge interaction immediately to prevent timeout
    await interaction.response.send_message("Setting up your Minecraft server, please wait...", ephemeral=True)

    # Check if the user already has a server folder
    if user_id in bot.thread_sessions:
        # Existing user: Check for active screen session
        session_info = bot.thread_sessions[user_id]
        screen_session_name = session_info["screen_session"]
        port = session_info["port"]
        droplet_ip = session_info["ip"]

        # Ensure the private thread exists or create a new one
        thread = await get_or_create_thread(interaction, session_info)
        if not thread:
            await interaction.followup.send("Failed to create a server management thread. Please contact support.", ephemeral=True)
            return

        # Check if the screen session is active
        screen_check = subprocess.run(["screen", "-list", screen_session_name], stdout=subprocess.PIPE)
        if screen_check.returncode == 0:
            # Server is already running; notify the user in their private thread
            await thread.send(f"Your server is already running! Connect using IP: `{droplet_ip}:{port}`")
            return
        else:
            # Screen session is not active, restart server with existing data
            server_ready = await start_minecraft_server(screen_session_name, server_dir)
            if server_ready:
                await thread.send(f"Restarting your Minecraft server. Connect using IP: `{droplet_ip}:{port}`")
            else:
                await thread.send("Failed to start the Minecraft server. Please try again later.")
    else:
        # New user: Set up a new server
        os.makedirs(server_dir, exist_ok=True)
        server_jar_path = os.path.join(server_dir, "minecraft_server.jar")
        if not os.path.exists(server_jar_path):
            download_result = subprocess.run(["wget", "-O", server_jar_path, MINECRAFT_SERVER_URL], check=True)
            if download_result.returncode != 0:
                await interaction.followup.send("Failed to download Minecraft server. Please try again later.")
                return

        with open(os.path.join(server_dir, "eula.txt"), "w") as eula_file:
            eula_file.write("eula=true\n")

        # Generate a new port for the new user
        port = generate_random_port()
        with open(os.path.join(server_dir, "server.properties"), "w") as prop_file:
            prop_file.write(f"server-port={port}\n")
            prop_file.write("server-ip=0.0.0.0\n")

        screen_session_name = f"minecraft_{user_id}"
        droplet_ip = get_public_ip()

        # Create a new thread for server management
        thread = await get_or_create_thread(interaction, bot.thread_sessions.setdefault(user_id, {}))
        if not thread:
            await interaction.followup.send("Failed to create a server management thread. Please contact support.", ephemeral=True)
            return

        # Save session info
        bot.thread_sessions[user_id].update({
            "screen_session": screen_session_name,
            "server_dir": server_dir,
            "thread_id": thread.id,
            "creator_id": interaction.user.id,
            "ip": droplet_ip,
            "port": port
        })
        save_sessions()

        # Start the Minecraft server
        server_ready = await start_minecraft_server(screen_session_name, server_dir)
        if server_ready:
            await thread.send(f"Your Minecraft server is up and running! Connect using IP: `{droplet_ip}:{port}`")
        else:
            # Notify the user if startup times out or fails
            await thread.send("The Minecraft server is still starting up. Please check back in a few minutes.")

@tree.command(name="stop", description="Stop the Minecraft server.")
async def stop(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    session_info = bot.thread_sessions.get(user_id)
    if not session_info:
        await interaction.response.send_message("Please start a Minecraft server to use this command.", ephemeral=True)
        return
    
    if interaction.user.id != session_info["creator_id"]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    screen_session_name = session_info["screen_session"]
    thread = await get_or_create_thread(interaction, session_info)

    await stop_server(screen_session_name, thread)
    await interaction.response.send_message("The server is shutting down.", ephemeral=True)

@tree.command(name="op", description="Give a player operator privileges.")
async def op(interaction: discord.Interaction, username: str):
    user_id = str(interaction.user.id)
    session_info = bot.thread_sessions.get(user_id)
    if not session_info:
        await interaction.response.send_message("Please start a Minecraft server to use this command.", ephemeral=True)
        return
    
    if interaction.user.id != session_info["creator_id"]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    subprocess.run(f"screen -S {session_info['screen_session']} -X stuff 'op {username}\n'", shell=True)
    thread = await get_or_create_thread(interaction, session_info)
    await thread.send(f"Gave operator privileges to `{username}`.")

@tree.command(name="add", description="Add a user to the management thread.")
async def add(interaction: discord.Interaction, user: discord.Member):
    user_id = str(interaction.user.id)
    session_info = bot.thread_sessions.get(user_id)
    if not session_info:
        await interaction.response.send_message("Please start a Minecraft server to use this command.", ephemeral=True)
        return
    
    if interaction.user.id != session_info["creator_id"]:
        await interaction.response.send_message("You do not have permission to add members.", ephemeral=True)
        return
    
    thread = await get_or_create_thread(interaction, session_info)
    await thread.add_user(user)
    await interaction.response.send_message(f"Added {user.mention} to the server management thread.", ephemeral=True)

bot.run(DISCORD_TOKEN)
