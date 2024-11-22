
# Minecraft Server Management Bot

This is a Discord bot that allows users to manage Minecraft servers directly from Discord. It integrates with a Minecraft server running on a DigitalOcean droplet, allowing users to start, stop, and configure their server, as well as perform various administrative tasks. The bot uses a combination of `discord.py`, `subprocess`, and `asyncio` to interact with the server and manage it in real-time.

## Features

### 1. **Start a Minecraft Server**
   - Users can start their own Minecraft server with a single command: `/minecraft`.
   - The bot will automatically create a new Minecraft server folder, download the server JAR file, and start the server in a detached `screen` session.
   - A private thread is created in Discord for managing the server, where users can get the server's public IP and port to connect.

### 2. **Stop the Server**
   - The server owner can stop the server anytime using the `/stop` command.
   - The bot sends a message in the private management thread confirming the server has stopped.

### 3. **Server Management Thread**
   - Each user gets a private thread where they can manage their server.
   - The bot tracks each user's session, including server details like screen session, IP, and port.
   - Users can interact with the bot via the private thread to manage their server, including adding other users to the thread.

### 4. **Grant Operator Permissions**
   - Users can grant operator (admin) permissions to players in their server using the `/op` command.
   - The bot sends a message in the server management thread once the operation is complete.

### 5. **Add Users to Management Thread**
   - Server owners can add users to the private server management thread using the `/add` command.
   - Only the server creator can add users.

### 6. **Persistent Session Data**
   - The bot keeps track of each user's server session in a local JSON file (`server_sessions.json`).
   - Data stored includes server folder path, screen session name, and server IP/port, ensuring the bot is aware of the user's server even after a restart.

### 7. **Automatic Server Setup**
   - When a new user starts their server, the bot sets up everything automatically, including downloading the Minecraft server JAR file, agreeing to the EULA, and generating a random port for the server.

## Commands

### `/minecraft`
   - Starts a new Minecraft server or restarts an existing one.
   - The bot creates or retrieves a private thread for server management.
   - The user receives the server IP and port.

### `/stop`
   - Stops the Minecraft server and sends a confirmation message in the private thread.
   - Only the server creator (owner) can stop the server.

### `/op <username>`
   - Grants operator (admin) privileges to the specified Minecraft player.
   - Only the server creator can use this command.

### `/add <user>`
   - Adds a user to the server management thread.
   - Only the server creator can add users.

## Installation

### Prerequisites
1. **Python 3.8+**: Ensure that Python is installed on your system.
2. **Discord Bot Token**: You’ll need a bot token to run the bot.
3. **Minecraft Server JAR**: The bot automatically downloads the server JAR, but you can customize the URL if needed.
4. **`screen`**: The bot uses `screen` to run the Minecraft server in a detached session.

### Steps to Set Up the Bot
1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/your-username/minecraft-server-bot.git
   cd minecraft-server-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Discord bot token in the `DISCORD_TOKEN` variable in the `main.py` file.

4. Run the bot:
   ```bash
   python main.py
   ```

### Additional Configuration
- The bot stores session data in a file called `server_sessions.json`. Make sure this file is stored securely.
- You can modify the server JAR download URL (`MINECRAFT_SERVER_URL`) to use a custom version of the server.

## Usage

Once the bot is up and running, invite it to your server and interact with it by using the slash commands in Discord. When you use the `/minecraft` command for the first time, the bot will set up your Minecraft server and provide you with the necessary connection details.

### Example Workflow:
1. User types `/minecraft`.
2. The bot sets up the server (downloads server JAR, creates necessary files).
3. The bot starts the server and sends the IP and port to the user in their private thread.
4. User can manage the server via their private thread, including stopping the server, granting operator privileges, and adding users.

## Files

- **`server_sessions.json`**: Stores session data for each user’s Minecraft server, including the server folder path, screen session name, IP, and port.
- **`server.log`**: Contains the server logs from the running Minecraft server. It is used by the bot to determine when the server is ready.
- **`eula.txt`**: Automatically created by the bot to agree to Minecraft’s End User License Agreement.

## Troubleshooting

### Bot Not Starting
- Ensure you have the necessary Python version installed.
- Check that your Discord token is correct.
- Verify that `screen` is installed on your system.

### Server Not Starting
- Ensure that your server has sufficient resources to run the Minecraft server.
- Check the logs for any errors related to the server startup.

### Server Management Thread Not Found
- Make sure the bot has permissions to create threads in the server.
- If the thread is missing, the bot will create a new one when the user runs a command again.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
