import os
import shutil
import re
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI(title="Mast Maggan - Music Streaming Platform")

# Templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Static files mounting
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if os.path.exists(os.path.join(PROJECT_ROOT, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static")), name="static")
elif os.path.exists(os.path.join(BASE_DIR, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Direct MySQL Connection for Docker Setup
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:rootpassword@db:3306/mastmaggan_db")

# Fixing SQLite and MySQL creation engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    artist = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    songs = db.query(Song).all()
    return templates.TemplateResponse("index.html", {"request": request, "songs": songs})

# Dynamic Song Upload Endpoint
@app.post("/upload")
async def upload_song(
    title: str = Form(...),
    artist: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs("media/music", exist_ok=True)
    file_path = f"media/music/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_song = Song(title=title, artist=artist, file_path=file_path)
    db.add(new_song)
    db.commit()

    return {"status": "SUCCESS", "message": f"Song '{title}' uploaded successfully!"}

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "app": "Mast Maggan Multi-Track Engine"}


# =========================================================================
# CHANGE 1: Fully Robust HTTP 206 Range Stream Handler (Fixed Path + Headers)
# =========================================================================
@app.get("/stream/{song_id}")
async def stream_audio(song_id: int, request: Request, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # =========================================================================
    # CHANGE 2: Smart File Path Resolver (Checks direct, container, and static paths)
    # =========================================================================
    file_path = song.file_path
    if not os.path.exists(file_path):
        filename = os.path.basename(file_path)
        potential_paths = [
            os.path.join(BASE_DIR, "static", "audio", filename),
            os.path.join(PROJECT_ROOT, "static", "audio", filename),
            f"/app/static/audio/{filename}",
            f"/root/projects/mast-maggan-app/static/audio/{filename}"
        ]
        found = False
        for p in potential_paths:
            if os.path.exists(p):
                file_path = p
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail=f"Audio file not found on disk: {song.file_path}")

    file_size = os.path.getsize(file_path)
    
    # =========================================================================
    # CHANGE 3: Case-Insensitive Range Header Extraction
    # =========================================================================
    range_header = request.headers.get("range") or request.headers.get("Range")

    if range_header:
        # Regex se start aur end bytes accurately extract karte hain
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            def iterfile():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_left = length
                    chunk_size = 64 * 1024
                    while bytes_left > 0:
                        read_len = min(chunk_size, bytes_left)
                        data = f.read(read_len)
                        if not data:
                            break
                        bytes_left -= len(data)
                        yield data

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": "audio/mpeg",
            }
            # HTTP 206 Partial Content return hota hai browser seek ke liye
            return StreamingResponse(iterfile(), status_code=206, headers=headers)

    # Fallback to full file streaming if no Range header requested
    def iterfull():
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "audio/mpeg",
    }
    return StreamingResponse(iterfull(), status_code=200, headers=headers)
