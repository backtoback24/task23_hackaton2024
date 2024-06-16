from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String

db = SQLAlchemy()


class VideoFile(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    video_file_path = Column(String(200), nullable=False)


class ImageFile(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    image_file_path = Column(String(200), nullable=False)

