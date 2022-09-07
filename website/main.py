from flask import session, render_template, redirect, request, send_from_directory, url_for, flash, jsonify
from flask_socketio import SocketIO
from application import create_app
from application.database import DataBase
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm
from werkzeug.exceptions import RequestEntityTooLarge
import os, logging, config, time

app = create_app()
socketio = SocketIO(app)

NAME_KEY = 'name'
MSG_LIMIT = 200

@socketio.on('event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    data = dict(json)
    if "name" in data:
        db = DataBase()
        db.save_message(data["name"], data["message"])

    socketio.emit('message response', json)




UPLOAD_FOLDER = 'static/uploads/'
 
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
     
 
@app.route('/share')
def share():
    return render_template('fileshare.html')
 
@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #print('upload_image filename: ' + filename)
        flash('Image successfully uploaded')
        return render_template('fileshare.html', filename=filename)
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)
 
@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)





@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form["inputName"]
        if len(name) >= 2:
            session[NAME_KEY] = name
            flash(f'You were successfully logged in as {name}.')
            return redirect(url_for("home"))
        else:
            flash("Name must be longer than 1 character.")

    return render_template("login.html", **{"session": session})

@app.route("/logout")
def logout():
    session.pop(NAME_KEY, None)
    flash("1You were logged out.")
    return redirect(url_for("login"))

@app.route("/")
@app.route("/home")
def home():
    if NAME_KEY not in session:
        return redirect(url_for("login"))

    return render_template("index.html", **{"session": session})

@app.route("/history")
def history():
    if NAME_KEY not in session:
        flash("1Please login before viewing your message history.")
        return redirect(url_for("login"))

    json_messages = get_history(session[NAME_KEY])
    print(json_messages)
    return render_template("history.html", **{"history": json_messages})

@app.route("/snooze")
def snooze():
    flash("Chat is now Snoozed...")
    json_messages = get_history(session[NAME_KEY])
    print(json_messages)
    return render_template("snooze.html", **{"history": json_messages})

@app.route("/get_name")
def get_name():
    data = {"name": ""}
    if NAME_KEY in session:
        data = {"name": session[NAME_KEY]}
    return jsonify(data)

@app.route("/get_messages")
def get_messages():
    db = DataBase()
    msgs = db.get_all_messages(MSG_LIMIT)
    messages = remove_seconds_from_messages(msgs)

    return jsonify(messages)

@app.route("/get_history")
def get_history(name):
    db = DataBase()
    msgs = db.get_messages_by_name(name)
    messages = remove_seconds_from_messages(msgs)

    return messages

def remove_seconds_from_messages(msgs):
    messages = []
    for msg in msgs:
        message = msg
        message["time"] = remove_seconds(message["time"])
        messages.append(message)

    return messages

def remove_seconds(msg):
    return msg.split(".")[0][:-3]


if __name__ == "__main__": 
    socketio.run(app, debug=True)