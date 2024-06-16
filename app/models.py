from . import db


class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    video_file_path = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<MediaFile {self.title}>'
