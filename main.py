import os
import uuid
import asyncio
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
    format: str  # "audio" or "video"

def sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " -_").strip()[:80]

@app.post("/analyze")
async def analyze(req: URLRequest):
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
        return {
            "title": info.get("title", "Unknown"),
            "channel": info.get("uploader", "Unknown"),
            "duration": info.get("duration", 0),
            "views": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
            "thumbnail": info.get("thumbnail", ""),
            "description": (info.get("description") or "")[:300],
        }
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download")
async def download(req: DownloadRequest):
    uid = uuid.uuid4().hex[:8]
    out_path = DOWNLOAD_DIR / uid

    if req.format == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(out_path) + ".%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }
        ext = "mp3"
        media_type = "audio/mpeg"
    else:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": str(out_path) + ".%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True,
        }
        ext = "mp4"
        media_type = "video/mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            title = sanitize(info.get("title", "download"))

        # find the downloaded file
        candidates = list(DOWNLOAD_DIR.glob(f"{uid}.*"))
        if not candidates:
            raise HTTPException(status_code=500, detail="File not found after download.")
        file_path = candidates[0]
        filename = f"{title}.{ext}"

        async def cleanup():
            await asyncio.sleep(60)
            try:
                file_path.unlink(missing_ok=True)
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
