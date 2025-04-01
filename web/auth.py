from flask import redirect, session, request
import requests
import os


def init_auth_routes(app):
    CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    REDIRECT_URI = "http://localhost:5000/callback"

    @app.route("/login")
    def login():
        return redirect(
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify%20guilds"
        )

    @app.route("/callback")
    def callback():
        code = request.args.get('code')
        data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
        session['access_token'] = r.json()['access_token']
        return redirect("/")

def requires_auth(f):
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def get_guilds(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://discord.com/api/users/@me/guilds',
        headers=headers
    )
    return response.json()