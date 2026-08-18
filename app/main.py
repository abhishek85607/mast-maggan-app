import os
import re
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI(title="Mast Maggan - Music Streaming Platform")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:rootpassword@mysql-svc:3306/mastmaggan_db")

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

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "app": "Mast Maggan Multi-Track Engine"}

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    songs = db.query(Song).all()
    return templates.TemplateResponse("index.html", {"request": request, "songs": songs})

@app.get("/stream/{song_id}")
async def stream_audio(song_id: int, request: Request, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    filename = os.path.basename(song.file_path)
    potential_paths = [
        f"/tmp/audio/{filename}",
        os.path.join(PROJECT_ROOT, "static", "audio", filename),
        os.path.join(BASE_DIR, "static", "audio", filename),
        f"/app/static/audio/{filename}",
        song.file_path
    ]

    file_path = None
    for p in potential_paths:
        if os.path.exists(p):
            file_path = p
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range") or request.headers.get("Range")

    if range_header:
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
                    while bytes_left > 0:
                        chunk = f.read(min(64 * 1024, bytes_left))
                        if not chunk:
                            break
                        bytes_left -= len(chunk)
                        yield chunk

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": "audio/mpeg",
            }
            return StreamingResponse(iterfile(), status_code=206, headers=headers)

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
