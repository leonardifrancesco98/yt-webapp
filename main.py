import os
import uuid
import asyncio
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YT Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path("./downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

class URLRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format: str   # "audio" or "video"
    quality: str  # "best", "1080", "720", "480", "360"

def sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " -_").strip()[:80]

def normalize_url(url: str) -> str:
    return url.strip()

def get_cookies_file() -> str | None:
    """Write YOUTUBE_COOKIES env var to a temp file and return its path."""
    cookies = os.environ.get("YOUTUBE_COOKIES", "").strip()
    print(f"[COOKIES] env var present: {bool(cookies)}, length: {len(cookies)}", flush=True)
    if not cookies:
        print("[COOKIES] WARNING: No YOUTUBE_COOKIES env var found!", flush=True)
        return None
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(cookies)
    tmp.close()
    print(f"[COOKIES] Written to temp file: {tmp.name}", flush=True)
    # Verify first line looks like a cookies.txt header
    first_line = cookies.split("\n")[0]
    print(f"[COOKIES] First line: {first_line[:80]}", flush=True)
    return tmp.name

def base_opts() -> dict:
    """Base yt-dlp options, with cookies and authcheck skip."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "no_check_certificate": True,
        "extractor_args": {"youtubetab": {"skip": ["authcheck"]}},
    }
    cookies_file = get_cookies_file()
    if cookies_file:
        opts["cookiefile"] = cookies_file
    return opts

@app.post("/analyze")
async def analyze(req: URLRequest):
    url = normalize_url(req.url)
    ydl_opts = {**base_opts(), "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", [])
        heights = sorted(set(
            f["height"] for f in formats
            if f.get("height") and f.get("vcodec") != "none"
        ), reverse=True)
        qualities = []
        for h in heights:
            if h >= 144:
                qualities.append({"label": f"{h}p", "value": str(h)})
        if not qualities:
            qualities = [{"label": "Best available", "value": "best"}]
        else:
            qualities.insert(0, {"label": "Best available", "value": "best"})

        return {
            "title": info.get("title", "Unknown"),
            "channel": info.get("uploader", "Unknown"),
            "duration": info.get("duration", 0),
            "views": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
            "thumbnail": info.get("thumbnail", ""),
            "qualities": qualities,
        }
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
async def download(req: DownloadRequest):
    url = normalize_url(req.url)
    uid = uuid.uuid4().hex[:8]
    out_path = DOWNLOAD_DIR / uid
    cookies_file = get_cookies_file()

    if req.format == "audio":
        ydl_opts = {
            **base_opts(),
            "format": "bestaudio/best",
            "outtmpl": str(out_path) + ".%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        ext = "mp3"
        media_type = "audio/mpeg"
    else:
        q = req.quality
        if q == "best":
            fmt = "bestvideo+bestaudio/best/bestvideo/best"
        else:
            fmt = (
                f"bestvideo[height<={q}]+bestaudio"
                f"/bestvideo[height<={q}]"
                f"/best[height<={q}]"
                f"/bestvideo+bestaudio"
                f"/best"
            )
        ydl_opts = {
            **base_opts(),
            "format": fmt,
            "outtmpl": str(out_path) + ".%(ext)s",
            "merge_output_format": "mp4",
            "format_sort": ["res", "ext:mp4:m4a", "tbr", "br"],
        }
        ext = "mp4"
        media_type = "video/mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = sanitize(info.get("title", "download"))

        candidates = list(DOWNLOAD_DIR.glob(f"{uid}.*"))
        if not candidates:
            raise HTTPException(status_code=500, detail="File not found after download.")
        file_path = candidates[0]
        filename = f"{title}.{ext}"

        async def cleanup():
            await asyncio.sleep(60)
            try:
                file_path.unlink(missing_ok=True)
                if cookies_file:
                    Path(cookies_file).unlink(missing_ok=True)
            except Exception:
                pass

        asyncio.create_task(cleanup())

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
        )
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")
