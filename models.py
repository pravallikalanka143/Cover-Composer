from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class Playlist(Base):

    __tablename__ = "playlists"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(String)

    user_email = Column(String)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer)

    mood = Column(String)
    genre = Column(String)
    tempo = Column(Integer)
    style = Column(String)

    file_path = Column(String)



class LikedSong(Base):
    __tablename__ = "liked_songs"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)

    song_name = Column(String)
    song_file = Column(String)
    song_type = Column(String)

    
class UserSettings(Base):

    __tablename__ = "settings"

    id = Column(
        Integer,
        primary_key=True
    )

    email = Column(String)

    default_mood = Column(String)

    default_genre = Column(String)

    default_tempo = Column(Integer)