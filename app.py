from time import strftime
from flask import Flask, render_template, g, redirect, url_for, request, Response, abort
from flask_oidc import OpenIDConnect
from okta import UsersClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from wtforms import form
from config import Secrets
from forms import AddEventForm, AddNoteForm, UpdateNoteForm, AddTodolistForm
from forms import RemoveEventForm, RemoveNoteForm, RemoveTodolistForm

app = Flask(__name__)
secrets = Secrets()
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = secrets.SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = secrets.SQLALCHEMY_DATABASE_URI
app.url_map.strict_slashes = False
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']
engine = create_engine(DB_URI)
oidc = OpenIDConnect(app)
okta_client = UsersClient("https://dev-1566490.okta.com", '00yg_xIMWwM-VzV63Mh8fX03ZwZvkEaF14Q1HJ2LeW')

@app.before_request
def before_request():
    if oidc.user_loggedin:
        g.user = okta_client.get_user(oidc.user_getfield("sub"))
    else:
        g.user = None

@app.route("/")
def index():
    return render_template("index.html")

### SHOW ALL EVENTS

@app.route("/scheduler",  methods=['GET', 'POST'])
@oidc.require_login
def dashboard():
    form = AddEventForm(request.form)
    if request.method == 'POST' and form.validate():
        event_name = form.name.data
        event_date = str(form.date.data)
        engine.execute('INSERT INTO events (name, date, userid) VALUES (%s, %s, %s);',
                        (event_name, event_date, g.user.id))
        return redirect(url_for('.dashboard'))
    db_events = engine.execute('SELECT name, id, date FROM events WHERE userid = %s', (g.user.id,)).fetchall()
    context = {
        'events': db_events
    }
    return render_template("dashboard.html", form=form, **context)

### REMOVE ONE EVENT

@app.route("/removeevent",  methods=['POST'])
@oidc.require_login
def remove_event():
    r_form = RemoveEventForm(request.form)
    if request.method != 'POST':
        abort(405)
    if request.method == 'POST' and r_form.validate():
        if not (engine.execute('SELECT userid FROM events WHERE id = %s',
         (r_form.eventid.data,)).fetchone()['userid'] == g.user.id):
            abort(403)
        engine.execute('DELETE FROM events WHERE id = %s;',
                        (r_form.eventid.data))
        
        # I forgot to add cascade delete so.....
        engine.execute('DELETE FROM notepad WHERE eventid = %s;',
                        (r_form.eventid.data))
        
        engine.execute('DELETE FROM calendar WHERE eventid = %s;',
                        (r_form.eventid.data))
        
        engine.execute('DELETE FROM todolist WHERE eventid = %s;',
                        (r_form.eventid.data))

        return redirect(url_for('.dashboard'))
    
    return abort(404)

### SHOW ONE EVENT

@app.route('/scheduler/<event_id>')
@oidc.require_login
def event(event_id):
    event = engine.execute('SELECT * FROM events WHERE id = %s', (int(event_id),)).fetchone()
    todo_count = engine.execute('SELECT COUNT(*) FROM todolist WHERE eventid = %s;', (event_id,)).fetchone()
    notes_count = engine.execute('SELECT COUNT(*) FROM notepad WHERE eventid = %s;', (event_id,)).fetchone()
    dates_count = engine.execute('SELECT COUNT(*) FROM calendar WHERE eventid = %s;', (event_id,)).fetchone()
    if not (event['userid'] == g.user.id):
        abort(403)
    context = {
        'event': event,
        'todo_count': todo_count,
        'notes_count': notes_count,
        'dates_count': dates_count
    }
    return render_template('event.html', **context)


### SHOW ALL NOTES


@app.route('/scheduler/<event_id>/notes', methods=['GET', 'POST'])
@oidc.require_login
def notes(event_id):
    event = engine.execute('SELECT * FROM events WHERE id = %s', (int(event_id),)).fetchone()
    notes = engine.execute('SELECT * FROM notepad WHERE eventid = %s', (int(event_id),)).fetchall()
    if not (event['userid'] == g.user.id):
        abort(403)
    form = AddNoteForm(request.form)
    if request.method == 'POST' and form.validate():
        event_name = form.name.data
        engine.execute('INSERT INTO notepad (name, eventid) VALUES (%s, %s);',
                        (event_name, event_id))
        return redirect(url_for('.notes', event_id=event_id))
    context = {
        'event': event,
        'notes': notes
    }
    return render_template('notes.html', **context)


### REMOVE ONE NOTE


@app.route("/removenote",  methods=['POST'])
@oidc.require_login
def remove_note():
    r_form = RemoveNoteForm(request.form)
    if request.method != 'POST':
        abort(405)
    if request.method == 'POST' and r_form.validate():
        if not (engine.execute('SELECT userid FROM events WHERE id = %s',
         (r_form.eventid.data,)).fetchone()['userid'] == g.user.id):
            abort(403)
        engine.execute('DELETE FROM notepad WHERE id = %s;',
                        (r_form.notepadid.data))

        return redirect(url_for('.notes', event_id=r_form.eventid.data))
    
    return abort(404)


### SHOW ONE NOTE


@app.route('/scheduler/<event_id>/notes/<note_id>/edit', methods=['GET', 'POST'])
@oidc.require_login
def note(event_id, note_id):
    event = engine.execute('SELECT * FROM events WHERE id = %s', (int(event_id),)).fetchone()
    note = engine.execute('SELECT * FROM notepad WHERE id = %s', (int(note_id),)).fetchone()

    form = UpdateNoteForm(request.form)
    if not (event['userid'] == g.user.id):
        abort(403)
    if request.method == 'POST' and form.validate():
        event_name = form.name.data
        event_notes = form.notes.data
        engine.execute('UPDATE notepad SET eventid = %s, name = %s, notes = %s WHERE id=%s;',
                        (event_id, event_name, event_notes, note_id))
        return redirect(url_for('.notes', event_id=event_id))

    if not (event['userid'] == g.user.id):
        abort(403)
    context = {
        'event': event,
        'note': note
    }

    return render_template('note.html', **context)


### SHOW ALL TODOLIST


@app.route('/scheduler/<event_id>/todolist', methods=['GET', 'POST'])
@oidc.require_login
def todolist(event_id):
    event = engine.execute('SELECT * FROM events WHERE id = %s', (int(event_id),)).fetchone()
    todolist = engine.execute('SELECT * FROM todolist WHERE eventid = %s', (int(event_id),)).fetchall()

    if not (event['userid'] == g.user.id):
        abort(403)

    form = AddTodolistForm(request.form)
    if request.method == 'POST' and form.validate():
        event_name = form.name.data
        print(event_name)
        engine.execute('INSERT INTO todolist (item, eventid, completed) VALUES (%s, %s, %s);',
                        (event_name, event_id, False))

        return redirect(url_for('.todolist', event_id=event_id))

    context = {
        'event': event,
        'todolist': todolist
    }
    return render_template('todolist.html', **context)














### LOGIN AND LOGOUT


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".dashboard"))

@app.route("/logout")
def logout():
    oidc.logout()
    return redirect(url_for(".index"))


### ERRORS


@app.errorhandler(403)
def custom_403(error):
    return Response(
        '''
        <body style="background-color: black">
            <img style="display: block;margin-left: auto;margin-right: auto;width: 50%;" src="https://http.cat/403">
            <h2 style="text-align:center; font-family: Arial; color:white">Você está tentando acessar um evento de outra pessoa.</h3>
        </body>
        ''', 403)


@app.errorhandler(404)
def custom_404(error):
    return Response(
        '''
        <body style="background-color: black">
            <img style="display: block;margin-left: auto;margin-right: auto;width: 50%;" src="https://http.cat/404">
            <h2 style="text-align:center; font-family: Arial; color:white">Página não encontrada.</h3>
        </body>
        ''', 404)

@app.errorhandler(405)
def custom_405(error):
    return Response(
        '''
        <body style="background-color: black">
            <img style="display: block;margin-left: auto;margin-right: auto;width: 50%;" src="https://http.cat/405">
            <h2 style="text-align:center; font-family: Arial; color:white">Apenas requests POST são permitidos aqui.</h3>
        </body>
        ''', 405)