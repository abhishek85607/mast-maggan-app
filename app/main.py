import os
import shutil
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI(title="Mast Maggan - Music Streaming Platform")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Direct MySQL Connection for Docker Setup
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:rootpassword@db:3306/mastmaggan_db")

# SQLite aur MySQL dono ke engine creation fix
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

@app.get("/stream/{song_id}")
def stream_audio(song_id: int, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song or not os.path.exists(song.file_path):
        raise HTTPException(status_code=404, detail="Song file not found")

    def iterfile():
        with open(song.file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/mpeg")    
