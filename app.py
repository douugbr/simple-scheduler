from flask import Flask, render_template, g, redirect, url_for
from flask_oidc import OpenIDConnect
from okta import UsersClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from .config import Secrets

app = Flask(__name__)
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = Secrets.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = Secrets.SQLALCHEMY_DATABASE_URI
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


@app.route("/scheduler")
@oidc.require_login
def dashboard():
    context = {

    }
    return render_template("dashboard.html")


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".dashboard"))


@app.route("/logout")
def logout():
    oidc.logout()
    return redirect(url_for(".index"))