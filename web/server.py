from flask import Flask, render_template, redirect, session
from auth import requires_auth, get_guilds
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Datenbank initialisieren
def init_db():
    conn = sqlite3.connect('wordle.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS server_config
                 (guild_id TEXT PRIMARY KEY, channel_id TEXT, words TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
@requires_auth
def dashboard():
    guilds = get_guilds(session['access_token'])
    return render_template('dashboard.html', guilds=guilds)

@app.route("/configure/<guild_id>")
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

@app.route("/update_config", methods=["POST"])
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