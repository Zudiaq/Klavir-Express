# Klavir-Express 🎹

Klavir-Express is a feature-rich Telegram bot designed to provide users with personalized music recommendations, weather updates, motivational quotes, and more. The bot integrates with various APIs like Spotify, Last.fm, OpenWeatherMap, and YouTube to deliver a seamless and engaging experience.

---

## Table of Contents
- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [APIs and Integrations](#apis-and-integrations)
- [Usage](#usage)
- [Workflows](#workflows)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### 🎵 Music Recommendations
- Provides music recommendations based on the current weather and mood.
- Integrates with Spotify and Last.fm for high-quality suggestions.
- Automatically filters out duplicate or restricted songs.

### ⛅ Weather Updates
- Fetches real-time weather data using OpenWeatherMap.
- Sends periodic weather updates with UV index and other metrics.
- Supports dynamic updates to previously sent weather messages.

### ✨ Motivational Quotes
- Retrieves daily motivational quotes from ZenQuotes API.
- Translates quotes to Persian (Farsi) for bilingual support.
- Adds stylized text for an enhanced user experience.

### 📩 Admin Panel
- Allows admins to manage users, send broadcasts, and view API key statistics.
- Supports multi-admin functionality with rate-limited commands.
- Provides a user-friendly interface with inline buttons.

### 🔄 Automated Workflows
- Scheduled tasks for sending weather updates, quotes, and music recommendations.
- GitHub Actions workflows for restarting the bot and managing deployments.

---

## Setup and Installation

### Prerequisites
- Python 3.9 or higher
- Git
- A Telegram bot token (from [BotFather](https://core.telegram.org/bots#botfather))
- API keys for Spotify, Last.fm, OpenWeatherMap, and YouTube

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Zudiaq/Klavir-Express.git
   cd Klavir-Express
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and configure the required environment variables (see [Environment Variables](#environment-variables)).

4. Run the bot:
   ```bash
   python panel.py
   ```

---

## Environment Variables

The following environment variables are required for the bot to function:

| Variable Name              | Description                                      |
|----------------------------|--------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`       | Telegram bot token from BotFather               |
| `TELEGRAM_CHAT_ID`         | Default chat ID for sending messages            |
| `ADMIN_CHAT_ID`            | Comma-separated list of admin chat IDs          |
| `SPOTIFY_CLIENT_ID`        | Spotify API client ID                           |
| `SPOTIFY_CLIENT_SECRET`    | Spotify API client secret                       |
| `LASTFM_API_KEY`           | Last.fm API key                                 |
| `OPENWEATHERMAP_API_KEY`   | OpenWeatherMap API key                          |
| `YOUTUBE_API_KEY`          | YouTube Data API key                            |
| `GH_PAT`                   | GitHub Personal Access Token for private repos  |
| `CITY`                     | Default city for weather updates (e.g., Tehran) |
| `REGION`                   | Default region for weather updates (e.g., IR)   |
| `DEBUG_MODE`               | Set to `True` for debug logging                 |

---

## APIs and Integrations

### Spotify
- Used for fetching music recommendations based on mood.
- Supports both playlist-based and global searches.

### Last.fm
- Provides additional music recommendations when Spotify is unavailable.

### OpenWeatherMap
- Fetches real-time weather data, including UV index and detailed conditions.

### YouTube
- Searches for music videos and downloads MP3 files for Telegram sharing.

### ZenQuotes
- Retrieves daily motivational quotes.

---

## Usage

### Starting the Bot
Run the following command to start the bot:
```bash
python panel.py
```

### Admin Commands
- `/admin`: Opens the admin panel.
- `/start`: Registers a new user and sends a welcome message.
- `/lang`: Allows users to change their language (English or Persian).

### Scheduled Tasks
The bot automatically performs the following tasks:
- Sends weather updates at predefined intervals.
- Shares motivational quotes in the morning and evening.
- Recommends music based on the current mood and weather.

---

## Workflows

### GitHub Actions
The project includes the following workflows:
1. **Panel Restart**: Automatically restarts the bot every 5 hours.
2. **Scheduled Tasks**: Executes weather updates, quotes, and music recommendations at specific times.
3. **Panel**: Manages the bot's deployment and dependencies.

### Manual Trigger
You can manually trigger workflows using the GitHub Actions interface.

---

## Contributing

We welcome contributions to improve Klavir-Express! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or support, please contact the project maintainer:
- **GitHub**: [Zudiaq](https://github.com/Zudiaq)
- **Telegram**: [@Klavir_Express_Bot](https://t.me/Klavir_Express_Bot)

---
