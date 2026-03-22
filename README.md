# YTDL — YouTube Downloader Web App

A self-hosted web app to download YouTube videos as **MP3 (audio)** or **MP4 (video)** from any device on your network — phone, tablet, or computer.

---

## Project Structure

```
yt-webapp/
├── main.py              # FastAPI backend
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose config
├── static/
│   └── index.html       # Frontend UI (served by FastAPI)
└── README.md
```

---

## Option 1 — Run Locally (Python)

### Prerequisites
- Python 3.10 or higher
- `ffmpeg` installed on your system

#### Install ffmpeg
| OS | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |
| Windows | Download from https://ffmpeg.org/download.html and add to PATH |

### Setup & Run

```bash
# 1. Go into the project folder
cd yt-webapp

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Open in your browser
```
http://localhost:8000
```

### Access from phone or tablet (same Wi-Fi)
1. Find your computer's local IP:
   - macOS/Linux: `ifconfig | grep "inet "` → look for `192.168.x.x`
   - Windows: `ipconfig` → look for `IPv4 Address`
2. On your phone browser, open: `http://192.168.x.x:8000`

---

## Option 2 — Run with Docker (Recommended)

Docker handles everything — Python, ffmpeg, dependencies — in one command.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### Run with Docker Compose

```bash
# 1. Go into the project folder
cd yt-webapp

# 2. Build and start
docker compose up --build

# To run in the background (detached mode)
docker compose up --build -d
```

### Open in your browser
```
http://localhost:8000
```

### Stop the app
```bash
docker compose down
```

### Update yt-dlp (if YouTube changes break downloads)
```bash
docker compose down
docker compose up --build   # rebuilds with latest yt-dlp
```

---

## Option 3 — Deploy to the Cloud (Access from Anywhere)

### Deploy to Railway (Free tier available)

1. Push your project to a GitHub repository
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repo — Railway auto-detects the Dockerfile
5. Go to **Settings → Networking → Generate Domain**
6. Your app is live at `https://your-app-name.up.railway.app`

### Deploy to Render (Free tier available)

1. Push your project to GitHub
2. Go to [render.com](https://render.com) and sign in
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repo
5. Set:
   - **Environment**: Docker
   - **Port**: 8000
6. Click **"Create Web Service"**
7. Your app is live at `https://your-app-name.onrender.com`

> **Note**: Free tiers on Render spin down after 15 minutes of inactivity. First load may take ~30 seconds.

### Deploy to a VPS (DigitalOcean, Hetzner, etc.)

```bash
# On your server:
git clone https://github.com/your-username/yt-webapp.git
cd yt-webapp
docker compose up --build -d

# Optional: set up Nginx as a reverse proxy with SSL (Let's Encrypt)
```

---

## How to Use the App

1. **Paste** a YouTube URL into the input field
2. Click **ANALYZE** (or press Enter)
3. The app shows: thumbnail, title, channel, views, duration
4. Click **MP3 Audio** to download audio only
5. Click **MP4 Video** to download video + audio
6. The file downloads automatically to your device

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "DownloadError: Video unavailable" | Video is private, region-locked, or deleted |
| MP3 download fails | Make sure `ffmpeg` is installed (or use Docker) |
| Can't access from phone | Make sure both devices are on the same Wi-Fi |
| Download is slow | Normal — depends on your internet speed |
| yt-dlp error after YouTube update | Rebuild Docker: `docker compose up --build` |

---

## Notes & Legal

- This app is for **personal use only**
- Only download content you have the right to download
- Respect YouTube's Terms of Service and copyright laws
- Downloaded files are automatically deleted from the server after 60 seconds
