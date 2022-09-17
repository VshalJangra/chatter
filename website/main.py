import os
from flask import session, render_template, redirect, jsonify
from flask import request, url_for, flash
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from application import create_app
from application.database import DataBase

app = create_app()
socketio = SocketIO(app)

UPLOAD_FOLDER = 'application/static/uploads/'
 
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024
 
ALLOWED_EXTENSIONS = (['pdf', 'doc', 'ppt', 'docx','png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/share')
def share():
    """File share function used for sharing the file into the html page."""
    return render_template('fileshare.html')
 
@app.route('/', methods=['POST'])
def upload_image():
    """Upload Image function used for uploading the image into the database after checking
    if the file is present in the allowed extensions."""
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
        flash('Image successfully uploaded')
        return render_template('index.html', filename=filename)
    else:
        flash('Allowed file types are - pdf, doc, ppt, docx, png, jpg, jpeg, gif')
        return redirect(request.url)
 
@app.route('/display/<filename>')
def display_image(filename):
    """Display Image function used for displaying the image from directory
    to the html page."""
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
    """Snooze function will snooze the char for the 5 seconds
    and it will automatically redirect to unsnooze after 5 seconds."""
    flash("Chat is now Snoozed, Please wait for 5 seconds....")
    json_messages = get_history(session[NAME_KEY])
    print(json_messages)
    return render_template("snooze.html", **{"history": json_messages})

@app.route("/unsnooze")
def desnooze():
    if NAME_KEY not in session:
        return redirect(url_for("login"))
    return render_template("unsnooze.html", **{"session": session})

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

NAME_KEY = 'name'
MSG_LIMIT = 200

@socketio.on('event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    data = dict(json)
    if "name" in data:
        db = DataBase()
        db.save_message(data["name"], data["message"])

    socketio.emit('message response', json)

if __name__ == "__main__": 
    socketio.run(app, debug=True)