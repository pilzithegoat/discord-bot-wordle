from flask import redirect, session, request
import requests
import os
import sys

def init_auth_routes(app):
    CLIENT_ID = "1333829329175445514"
    CLIENT_SECRET = "Ik9YT8l-rMcQHNPLhanGk5EcT1LXJgnE"
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
        if 'code' not in request.args:
            return "Missing authorization code", 400
        code = request.args.get('code')
        data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
        }
        print("Access Token:", session['access_token'])
        user_data = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {session["access_token"]}'}
        ).json()
        print("User Data:", user_data)


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