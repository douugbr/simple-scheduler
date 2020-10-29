from time import strftime
from flask import Flask, render_template, g, redirect, url_for, request, Response, abort
from flask_oidc import OpenIDConnect
from okta import UsersClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from config import Secrets
from forms import AddEventForm, RemoveEventForm

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


@app.route("/scheduler",  methods=['GET', 'POST'])
@oidc.require_login
def dashboard():
    form = AddEventForm(request.form)
    r_form = RemoveEventForm(request.form)
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

@app.route("/removeevent",  methods=['POST'])
@oidc.require_login
def remove_event():
    r_form = RemoveEventForm(request.form)
    if request.method == 'POST' and r_form.validate():
        if not (engine.execute('SELECT userid FROM events WHERE id = %s', (r_form.eventid.data,)).fetchone()['userid'] == g.user.id):
            abort(403)
        engine.execute('DELETE FROM events WHERE id = %s;',
                        (r_form.eventid.data))
        return redirect(url_for('.dashboard'))
    
    return abort(404)

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

@app.route('/scheduler/<event_id>/notes')
@oidc.require_login
def notes(event_id):
    event = engine.execute('SELECT * FROM events WHERE id = %s', (int(event_id),)).fetchone()
    notes = engine.execute('SELECT * FROM notepad WHERE eventid = %s', (int(event_id),)).fetchall()
    if not (event['userid'] == g.user.id):
        abort(403)
    context = {
        'event': event,
        'notes': notes
    }
    return render_template('event.html', **context)


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".dashboard"))

# @app.route("/files")
# def files():
#     return render_template('drive.html')

@app.route("/logout")
def logout():
    oidc.logout()
    return redirect(url_for(".index"))

# ERRORS

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
def custom_401(error):
    return Response(
        '''
        <body style="background-color: black">
            <img style="display: block;margin-left: auto;margin-right: auto;width: 50%;" src="https://http.cat/404">
            <h2 style="text-align:center; font-family: Arial; color:white">Página não encontrada.</h3>
        </body>
        ''', 404)