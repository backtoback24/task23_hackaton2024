from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from .models import MediaFile, db
import os

main = Blueprint('main', __name__)


@main.route('/')
def index():
    media_files = MediaFile.query.all()
    return render_template('index.html', media_files=media_files)


@main.route('/upload', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files:
        return redirect(request.url)

    file = request.files['video_file']
    title = request.form['title']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Путь сохранения файла в папке статики
        file_path = os.path.join('uploads', filename)
        file.save(os.path.join(current_app.static_folder, file_path))

        new_video = MediaFile(title=title, video_file_path=file_path)
        db.session.add(new_video)
        db.session.commit()

        return redirect(url_for('main.index'))

    return 'Invalid file format', 400


@main.route('/video/<int:video_id>')
def play_video(video_id):
    video = MediaFile.query.get_or_404(video_id)
    return render_template('play_video.html', video=video)


@main.route('/video/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    video = MediaFile.query.get_or_404(video_id)
    # Путь к файлу видео
    file_path = os.path.join(current_app.static_folder, video.video_file_path)
    # Удаляем файл, если он существует
    if os.path.exists(file_path):
        os.remove(file_path)
    # Удаляем запись из базы данных
    db.session.delete(video)
    db.session.commit()
    return redirect(url_for('main.index'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}
