# Timezone Discord Bot

A minimalistic Discord bot that displays a user's current time based on their set timezone. Supports multiple servers with separate timezone storage for each user.

## Features

- **Commands**:
  - `,tz`: Shows the user's current time in a minimalistic embed
  - `,tz @user`: Shows the mentioned user's current time (if their timezone is set)
  - `,settz [timezone]`: Sets the user's timezone (e.g., `America/New_York`, `Europe/London`)
  
- **Dynamic Embed Colors**:
  - Morning (6 AM–12 PM): Pastel yellow
  - Afternoon (12 PM–6 PM): Pastel blue
  - Evening (6 PM–12 AM): Pastel purple
  - Night (12 AM–6 AM): Pastel gray
  
- **Multi-Server Support**:
  - Stores user timezones per server
  - Users can have different timezones on different servers
  
## Installation

### Requirements
- Python 3.8 or higher
- A Discord bot token
- A VPS or hosting service to run the bot

### Setup Instructions

1. Clone this repository:
   ```
   git clone [repository-url]
   cd Timezone
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the bot:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file and add your Discord bot token.

4. Run the bot:
   ```
   python -m src.bot
   ```

## Setting Up as a Service on VPS

To run the bot continuously on a VPS, you can set it up as a systemd service:

1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/timezone-bot.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Timezone Discord Bot
   After=network.target

   [Service]
   User=your-username
   WorkingDirectory=/path/to/Timezone
   ExecStart=/usr/bin/python3 -m src.bot
   Restart=always
   RestartSec=10
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=timezonebot
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable timezone-bot.service
   sudo systemctl start timezone-bot.service
   ```

4. Check the status:
   ```
   sudo systemctl status timezone-bot.service
   ```

## Required Discord Bot Permissions

The bot needs the following permissions to function properly:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Manage Messages (to delete its own messages)
- Read Message History

## Timezone Format

The bot uses the IANA timezone database format. Common examples:
- `America/New_York`
- `Europe/London`
- `Asia/Tokyo`
- `Australia/Sydney`
- `Pacific/Auckland`

You can find a full list of valid timezones by running `pytz.all_timezones` in Python.

## Troubleshooting

- **Bot doesn't respond**: Ensure your bot token is correct and the bot has proper permissions
- **Invalid timezone error**: Make sure you're using a valid IANA timezone identifier
- **Bot crashes**: Check for errors in the console output and ensure all dependencies are installed

## License

This project is licensed under the MIT License - see the LICENSE file for details.