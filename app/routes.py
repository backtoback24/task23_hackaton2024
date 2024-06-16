from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file
from .models import db, VideoFile, ImageFile
from werkzeug.utils import secure_filename
import os
import cv2
import zipfile
import io
from ultralytics import YOLO

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'jpg', 'jpeg', 'png', 'gif'}

# Инициализация модели YOLOv8
model = YOLO('very_best.pt')  # Замените 'yolov8n.pt' на путь к вашей модели


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_folder():
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


@main.route('/')
def index():
    video_files = VideoFile.query.all()
    image_files = ImageFile.query.all()
    return render_template('index.html', video_files=video_files, image_files=image_files)


@main.route('/upload_video', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'video_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['video_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = ensure_upload_folder()
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            normalized_file_path = os.path.normpath(os.path.join('uploads', filename)).replace("\\", "/")
            new_video = VideoFile(title=filename, video_file_path=normalized_file_path)
            db.session.add(new_video)
            db.session.commit()

            # Обработка видео
            process_video(file_path)

            flash('Video uploaded and processed successfully')
        else:
            flash('Allowed file types are mp4, mov, avi')

        return redirect(url_for('.index'))
    return render_template('upload_video.html')


@main.route('/upload_images', methods=['GET', 'POST'])
def upload_images():
    if request.method == 'POST':
        if 'image_files' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('image_files')
        if not files:
            flash('No selected files')
            return redirect(request.url)

        image_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = ensure_upload_folder()
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                normalized_file_path = os.path.normpath(os.path.join('uploads', filename)).replace("\\", "/")
                new_image = ImageFile(title=filename, image_file_path=normalized_file_path)
                db.session.add(new_image)
                db.session.commit()
                image_paths.append(file_path)
            else:
                flash('Allowed file types are jpg, jpeg, png, gif')

        if image_paths:
            read_images(image_paths)
            flash('Images uploaded and processed successfully')

        return redirect(url_for('.index'))
    return render_template('upload_images.html')


@main.route('/play_video/<int:video_id>', methods=['GET'])
def play_video(video_id):
    video = VideoFile.query.get_or_404(video_id)
    return render_template('play_video.html', video=video)


@main.route('/download_video/<int:video_id>', methods=['GET'])
def download_video(video_id):
    video = VideoFile.query.get_or_404(video_id)
    file_path = os.path.normpath(os.path.join(current_app.static_folder, video.video_file_path))
    return send_file(file_path, as_attachment=True)


@main.route('/download_image_txt/<int:image_id>', methods=['GET'])
def download_image_txt(image_id):
    image = ImageFile.query.get_or_404(image_id)
    txt_file_path = os.path.splitext(os.path.join(current_app.static_folder, image.image_file_path))[0] + '.txt'
    if os.path.exists(txt_file_path):
        return send_file(txt_file_path, as_attachment=True)
    else:
        flash('Text file not found')
        return redirect(url_for('.index'))


@main.route('/download_images', methods=['GET'])
def download_images():
    image_files = ImageFile.query.all()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for image in image_files:
            txt_file_path = os.path.splitext(os.path.join(current_app.static_folder, image.image_file_path))[0] + '.txt'
            if os.path.exists(txt_file_path):
                zip_file.write(txt_file_path, os.path.basename(txt_file_path))
    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name='annotations.zip', mimetype='application/zip')


@main.route('/delete_video/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    video = VideoFile.query.get_or_404(video_id)
    try:
        os.remove(os.path.normpath(os.path.join(current_app.static_folder, video.video_file_path)))
        txt_file_path = os.path.splitext(video.video_file_path)[0] + '.txt'
        if os.path.exists(txt_file_path):
            os.remove(os.path.normpath(os.path.join(current_app.static_folder, txt_file_path)))
    except OSError as e:
        flash(f'Error deleting file: {e}')
    db.session.delete(video)
    db.session.commit()
    flash('Video deleted successfully')
    return redirect(url_for('.index'))


@main.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    image = ImageFile.query.get_or_404(image_id)
    try:
        os.remove(os.path.normpath(os.path.join(current_app.static_folder, image.image_file_path)))
        txt_file_path = os.path.splitext(image.image_file_path)[0] + '.txt'
        if os.path.exists(txt_file_path):
            os.remove(os.path.normpath(os.path.join(current_app.static_folder, txt_file_path)))
    except OSError as e:
        flash(f'Error deleting file: {e}')
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully')
    return redirect(url_for('.index'))


def read_images(image_paths):
    for image_path in image_paths:
        img = cv2.imread(image_path)
        results = model(img)

        txt_file_path = os.path.splitext(image_path)[0] + '.txt'
        with open(txt_file_path, 'w') as f:
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].numpy()  # Используем атрибут xyxy для получения координат
                    class_id = int(box.cls[0])

                    # Применение преобразования id_class
                    if class_id == 0:
                        class_id = 3
                    elif class_id == 1:
                        class_id = 0
                    elif class_id == 2:
                        class_id = 2
                    elif class_id == 3:
                        class_id = 1
                    elif class_id == 4:
                        class_id = 4

                    x_center = (x1 + x2) / 2 / img.shape[1]
                    y_center = (y1 + y2) / 2 / img.shape[0]
                    width = (x2 - x1) / img.shape[1]
                    height = (y2 - y1) / img.shape[0]
                    f.write(f"{class_id};{x_center};{y_center};{width};{height}\n")


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        txt_file_path = os.path.splitext(video_path)[0] + f'_{frame_number}.txt'
        with open(txt_file_path, 'w') as f:
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].numpy()  # Используем атрибут xyxy для получения координат
                    class_id = int(box.cls[0])

                    # Применение преобразования id_class
                    if class_id == 0:
                        class_id = 3
                    elif class_id == 1:
                        class_id = 0
                    elif class_id == 2:
                        class_id = 2
                    elif class_id == 3:
                        class_id = 1
                    elif class_id == 4:
                        class_id = 4

                    x_center = (x1 + x2) / 2 / frame.shape[1]
                    y_center = (y1 + y2) / 2 / frame.shape[0]
                    width = (x2 - x1) / frame.shape[1]
                    height = (y2 - y1) / frame.shape[0]
                    f.write(f"{class_id};{x_center};{y_center};{width};{height}\n")

        frame_number += 1

    cap.release()
    cv2.destroyAllWindows()
