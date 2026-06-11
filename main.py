from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
from database import engine, SessionLocal
from models import Base, User , LikedSong
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from midiutil import MIDIFile
from midi2audio import FluidSynth

import random
import os
from datetime import datetime

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="covercomposer_secret"
)
Base.metadata.create_all(bind=engine)
RECENT_SONGS = [
    {
        "name": "Kesariya",
        "file": "/static/songs/Kesariya.mp3"
    },
    {
        "name": "Love Me Like You Do",
        "file": "/static/songs/love_me_like_you_do.mp3"
    },
    {
        "name": "Don't Stop",
        "file": "/static/songs/dont_stop.mp3"
    }
]
LIKED_SONGS = []

# -----------------------------
# Paths
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(STATIC_DIR, "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATE_DIR)


templates = Jinja2Templates(directory=TEMPLATE_DIR)

# -----------------------
# Signup Page
# -----------------------

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="signup.html"
)

@app.post("/signup")
async def signup_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    user = User(
        username=username,
        email=email,
        password=password
    )

    db.add(user)
    db.commit()

    db.close()

    return RedirectResponse(
        "/login",
        status_code=303
    )

# -----------------------
# Login Page
# -----------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )
@app.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == email,
        User.password == password
    ).first()

    db.close()

    if user:

        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["email"] = user.email

    
        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    return HTMLResponse(
        "Invalid Login",
        status_code=401
    )


@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303
    )

# -----------------------
# Home Page
# -----------------------

@app.get("/dashboard")
async def dashboard(request: Request):

    print("SESSION DATA =", dict(request.session))

    if "user_id" not in request.session:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )
#@app.get("/search")
#async def search_page(request: Request):

   # return templates.TemplateResponse(
       # request=request,
       # name="search.html"
    #)


#@app.get("/playlists")
#async def playlist_page(request: Request):

   # return templates.TemplateResponse(
       # request=request,
        #name="playlists.html",
       # context={
           # "songs": LIKED_SONGS
        #}
    #)
@app.get("/profile")
async def profile_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "username":
            request.session.get("username"),

            "email":
            request.session.get("email")
        }
    )

@app.get("/change-password")
async def change_password_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="change_password.html"
    )

@app.post("/change-password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...)
):

    db = SessionLocal()

    user_id = request.session.get("user_id")

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        db.close()
        return RedirectResponse(
            "/login",
            status_code=303
        )

    if str(user.password) != old_password:
        db.close()
        return HTMLResponse(
            "Wrong Current Password"
        )

    setattr(
        user,
        "password",
        new_password
    )

    db.commit()
    db.close()

    return HTMLResponse(
    """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Password Changed</title>

        <style>

        body{
            background:#0f172a;
            font-family:Arial, sans-serif;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            margin:0;
        }

        .success-card{
            background:white;
            padding:40px;
            border-radius:20px;
            text-align:center;
            width:420px;
            box-shadow:0 10px 30px rgba(0,0,0,0.3);
        }

        .icon{
            font-size:70px;
            color:#22c55e;
        }

        h2{
            color:#111827;
            margin-top:10px;
        }

        p{
            color:#6b7280;
        }

        .btn{
            display:inline-block;
            margin-top:20px;
            padding:12px 25px;
            background:#2563eb;
            color:white;
            text-decoration:none;
            border-radius:10px;
            font-weight:bold;
        }

        .btn:hover{
            background:#1d4ed8;
        }

        </style>
    </head>

    <body>

        <div class="success-card">

            <div class="icon">✅</div>

            <h2>Password Changed Successfully</h2>

            <p>
                Your account password has been updated successfully.
            </p>

            <a href="/settings" class="btn">
                Back To Settings
            </a>

        </div>

    </body>
    </html>
    """
)


@app.get("/settings")
async def settings_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="settings.html"
    )

@app.get("/recent", response_class=HTMLResponse)
async def recent_songs(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="recent.html",
        context={
            "songs": RECENT_SONGS
        }
    )


@app.get("/liked", response_class=HTMLResponse)
async def liked_songs(request: Request):

    db = SessionLocal()

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    songs = db.query(LikedSong).filter(
        LikedSong.user_id == user_id
    ).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="liked.html",
        context={
            "songs": songs
        }
    )

@app.post("/like-song")
async def like_song(
    request: Request,
    audio_file: str = Form(...),
    song_name: str = Form(...),
    song_type: str = Form(...)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    liked = LikedSong(
        user_id=user_id,
        song_name=song_name,
        song_file=audio_file,
        song_type=song_type
    )

    db.add(liked)
    db.commit()
    db.close()

    return RedirectResponse(
        "/liked",
        status_code=303
    )

# DELETE LIKED SONG
@app.post("/delete-liked-song")
async def delete_liked_song(
    request: Request,
    song_id: int = Form(...)
):

    db = SessionLocal()

    song = db.query(LikedSong).filter(
        LikedSong.id == song_id
    ).first()

    if song:
        db.delete(song)
        db.commit()

    db.close()

    return RedirectResponse(
        "/liked",
        status_code=303
    )



@app.get("/mp3-songs", response_class=HTMLResponse)
async def mp3_songs(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="mp3songs.html"
    )
@app.post("/play-mp3")
async def play_mp3(
    request: Request,
    mood: str = Form(...),
    genre: str = Form(...),
    tempo: int = Form(...),
    style: str = Form(...)
):



    if (
        mood == "Happy" and
        genre == "Pop" and
        tempo == 120 and
        style == "Simple"
    ):
        song = "/static/songs/Kesariya.mp3"

    elif (
        mood == "Energetic" and
        genre == "Jazz" and
        tempo == 90 and
        style == "Simple"
    ):
        song = "/static/songs/love_me_like_u_do.mp3"

    elif (
        mood == "Energetic" and
        genre == "Rock" and
        tempo == 140 and
        style == "Complex"
    ):
        song = "/static/songs/dont_stop.mp3"

    elif (
        mood == "Sad" and
        genre == "Jazz" and
        tempo == 140 and
        style == "Complex"
    ):
        song = "/static/songs/Channa Mereya.mp3"

    elif (
        mood == "Happy" and
        genre == "Pop" and
        tempo == 140 and
        style == "Simple"
    ):
        song = "/static/songs/justin bieber.mp3"

    elif (
        mood == "Energetic" and
        genre == "Rock" and
        tempo == 120 and
        style == "Complex"
    ):
        song = "/static/songs/redsea.mp3"

    elif (
        mood == "Sad" and
        genre == "Pop" and
        tempo == 120 and
        style == "Simple"
    ):
        song = "/static/songs/ye_manishike.mp3"
    
    elif (
    mood == "Energetic" and
    genre == "Jazz" and
    tempo == 120 and
    style == "Simple"
):
        song = "/static/songs/The_Monster.mp3"

    elif (
    mood == "Happy" and
    genre == "Jazz" and
    tempo == 90 and
    style == "Simple"
):
     song = "/static/songs/Jatha_Kalise.mp3"

    elif (
    mood == "Sad" and
    genre == "Rock" and
    tempo == 90 and
    style == "Complex"
):
     song = "/static/songs/Sunn_raha_hai.mp3"

    elif (
    mood == "Happy" and
    genre == "Rock" and
    tempo == 120 and
    style == "Complex"
):
     song = "/static/songs/Yegire_Mabbulona.mp3"

    elif (
    mood == "Energetic" and
    genre == "Pop" and
    tempo == 140 and
    style == "Complex"
):
     song = "/static/songs/Daavudi.mp3"

    elif (
    mood == "Sad" and
    genre == "Pop" and
    tempo == 140 and
    style == "Simple"
):
     song = "/static/songs/Papa Meri Jaan.mp3"

    elif (
    mood == "Happy" and
    genre == "Jazz" and
    tempo == 140 and
    style == "Complex"
):
     song = "/static/songs/Sahibaa.mp3"

    elif (
    mood == "Energetic" and
    genre == "Pop" and
    tempo == 90 and
    style == "Simple"
):
     song = "/static/songs/Perfect.mp3"

    elif (
    mood == "Happy" and
    genre == "Rock" and
    tempo == 90 and
    style == "Complex"
):
     song = "/static/songs/O Maahi.mp3"

    elif (
    mood == "Sad" and
    genre == "Jazz" and
    tempo == 90 and
    style == "Simple"
):
     song = "/static/songs/Chivaraku Migiledi.mp3"


    return templates.TemplateResponse(
        request=request,
        name="mp3_result.html",
        context={
            "audio_file": song,
            "mood": mood,
            "genre": genre,
            "tempo": tempo,
            "style": style
        }
    )

@app.get("/generate-page")
async def generate_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )
# -----------------------------
# SoundFont
# -----------------------------

SOUNDFONT = os.path.join(BASE_DIR, "soundfont.sf2")

# -----------------------------
# Genre Instruments
# -----------------------------

GENRE_INSTRUMENTS = {
    "Pop": 0,
    "Rock": 29,
    "Jazz": 26,
    "Electronic": 81
}

# -----------------------------
# Mood Scales
# -----------------------------

MOOD_SCALES = {
    "Happy": [60, 62, 64, 65, 67, 69, 71],
    "Sad": [60, 62, 63, 65, 67, 68, 70],
    "Calm": [60, 62, 64, 67, 69],
    "Energetic": [60, 64, 67, 72]
}
def markov_melody(scale, length=32):

    melody = [random.choice(scale)]

    for _ in range(length - 1):

        current = melody[-1]
        idx = scale.index(current)

        choices = []

        if idx > 0:
            choices.append(scale[idx - 1])

        choices.append(scale[idx])

        if idx < len(scale) - 1:
            choices.append(scale[idx + 1])

        melody.append(random.choice(choices))

    return melody


def note_properties(style):

    if style == "Simple":
        return 1, 100

    duration = random.choice([0.5, 1, 1.5])
    velocity = random.randint(70, 120)

    return duration, velocity

def create_midi(notes, genre, tempo, style, midi_path):

    midi = MIDIFile(3)

    melody_track = 0
    bass_track = 1
    drum_track = 2

    instrument = GENRE_INSTRUMENTS.get(genre, 0)

    midi.addTempo(melody_track, 0, tempo)
    midi.addTempo(bass_track, 0, tempo)
    midi.addTempo(drum_track, 0, tempo)

    midi.addProgramChange(melody_track, 0, 0, instrument)
    midi.addProgramChange(bass_track, 1, 0, 33)

    time = 0

    for note in notes:

        duration, velocity = note_properties(style)

        # Melody
        midi.addNote(
            melody_track,
            0,
            note,
            time,
            duration,
            velocity
        )

        # Bass
        midi.addNote(
            bass_track,
            1,
            note - 12,
            time,
            duration,
            80
        )

        # Drums
        midi.addNote(
            drum_track,
            9,
            36,
            time,
            0.5,
            100
        )

        time += duration

    with open(midi_path, "wb") as output_file:
        midi.writeFile(output_file)

def convert_to_wav(midi_path, wav_path):

    try:
        command = [
            r"C:\FluidSynth\bin\fluidsynth.exe",
            "-ni",
            "-F",
            wav_path,
            "-r",
            "44100",
            SOUNDFONT,
            midi_path
        ]

        subprocess.run(command, check=True)

        return os.path.isfile(wav_path)

    except Exception as e:
        print("WAV conversion error:", e)
        return False
    

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="home.html"
    )


@app.post("/generate")
async def generate(
    request: Request,
    mood: str = Form(...),
    genre: str = Form(...),
    tempo: int = Form(...),
    style: str = Form(...)
):

    scale = MOOD_SCALES[mood]

    notes = markov_melody(scale)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    midi_file = os.path.join(
        OUTPUT_DIR,
        f"{timestamp}.mid"
    )

    wav_file = os.path.join(
        OUTPUT_DIR,
        f"{timestamp}.wav"
    )

    create_midi(
        notes,
        genre,
        tempo,
        style,
        midi_file
    )

    success = convert_to_wav(
        midi_file,
        wav_file
    )

    print("WAV CREATED:", success)
    print("WAV PATH:", wav_file)
    RECENT_SONGS.append(
        {
            "name": os.path.basename(wav_file),
            "file": f"/static/output/{os.path.basename(wav_file)}"
        }
    )
    if success:
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "audio_file": f"/static/output/{os.path.basename(wav_file)}",
                "mood": mood,
                "genre": genre,
                "tempo": tempo,
                "style": style,
                "file_name": os.path.basename(wav_file)
            }
        )

    return HTMLResponse("WAV generation failed")


