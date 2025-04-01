from flask import Flask, render_template, redirect, session, request
from .auth import init_auth_routes, requires_auth, get_guilds
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "skdnci2938djh"

init_auth_routes(app)

# Datenbank initialisieren
# In server.py
def init_db():
    try:
        conn = sqlite3.connect('wordle.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS server_config
                     (guild_id TEXT PRIMARY KEY, 
                      channel_id TEXT, 
                      words TEXT)''')
        conn.commit()
    except Exception as e:
        print("Datenbankfehler:", str(e))
    finally:
        conn.close()

init_db()

@app.route("/")
@requires_auth
def dashboard():
    try:
        # Debug-Logs
        print("Session Data:", dict(session))
        user_data = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {session["access_token"]}'}
        ).json()
        print("User Data:", user_data)
        
        guilds = get_guilds(session['access_token'])
        print("Guilds:", guilds)
        
        return render_template("dashboard.html", 
            guilds=guilds,
            user=user_data
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Server Error: {str(e)}", 500

@app.route("/configure/<string:guild_id>", endpoint="configure_guild")
@requires_auth
def configure(guild_id):
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute("SELECT * FROM server_config WHERE guild_id = ?", (guild_id,))
    config = c.fetchone()
    return render_template('configure.html', 
        guild_id=guild_id,
        current_channel=config[1] if config else None,
        words=config[2].split(',') if config else []
    )

@app.route("/update", methods=["POST"], endpoint="update_config")
@requires_auth
def update_config():
    guild_id = request.form['guild_id']
    channel_id = request.form['channel_id']
    words = request.form['words']
    
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute('''REPLACE INTO server_config 
               (guild_id, channel_id, words) VALUES (?, ?, ?)''',
               (guild_id, channel_id, words))
    conn.commit()
    conn.close()
    
    return redirect(f"/configure/{guild_id}")