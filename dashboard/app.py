import os
import json
import requests
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from models.database import init_db, Session, Guild
from models.server_config import ServerConfig

# Import configuration from config.py
try:
    from config import (
        TOKEN, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, ADMIN_IDS,
        FLASK_SECRET_KEY, FLASK_APP, FLASK_ENV, MAX_HINTS, MAX_ATTEMPTS,
        DISCORD_REDIRECT_URI
    )
except ImportError:
    print("Error: config.py not found. Please run install.sh first.")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour
app.config["SESSION_COOKIE_SECURE"] = False  # Set to False for local development
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_MAX_SIZE"] = 4093  # Maximum cookie size

# Initialize database
init_db()

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Discord OAuth2 settings
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

# Bot settings
BOT_TOKEN = TOKEN
MAX_HINTS = MAX_HINTS
MAX_ATTEMPTS = MAX_ATTEMPTS
ADMIN_IDS = ADMIN_IDS

def is_bot_admin(user_id):
    """Check if the user has admin permissions in any of the bot's guilds"""
    try:
        # Get all guilds where the bot is present
        bot_headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        bot_guilds_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=bot_headers)
        
        if bot_guilds_response.status_code != 200:
            print(f"Failed to get bot guilds: {bot_guilds_response.status_code}")
            return False
        
        bot_guilds = bot_guilds_response.json()
        
        # Check each guild where the bot is present
        for guild in bot_guilds:
            # Get guild member info to check permissions
            member_response = requests.get(
                f"{DISCORD_API_ENDPOINT}/guilds/{guild['id']}/members/{user_id}",
                headers=bot_headers
            )
            
            if member_response.status_code == 200:
                member_data = member_response.json()
                # Check if user has admin permissions or is owner
                if member_data.get("permissions", 0) & 0x8 or str(guild["owner_id"]) == str(user_id):  # 0x8 is ADMINISTRATOR permission
                    return True
        
        return False
        
    except Exception as e:
        print(f"Error checking admin permissions: {e}")
        return False

# Register the is_bot_admin function as a template filter
app.jinja_env.filters['is_bot_admin'] = is_bot_admin

class User(UserMixin):
    def __init__(self, user_id, username, avatar):
        self.id = user_id
        self.username = username
        self.avatar = avatar

@login_manager.user_loader
def load_user(user_id):
    if "user_data" in session:
        user_data = session["user_data"]
        return User(
            user_id=user_data["id"],
            username=user_data["username"],
            avatar=user_data["avatar"]
        )
    return None

def is_guild_owner(guild_id, user_id):
    """Check if the user is the owner of the guild"""
    try:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = requests.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}", headers=headers)
        if response.status_code == 200:
            guild_data = response.json()
            return str(guild_data["owner_id"]) == str(user_id)
    except Exception as e:
        print(f"Error checking guild ownership: {e}")
    return False

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        
        if not is_bot_admin(current_user.id):
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for("index"))
        
        return f(*args, **kwargs)
    return decorated_function

def guild_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        
        guild_id = kwargs.get("guild_id")
        if not guild_id:
            flash("Guild ID is required.", "danger")
            return redirect(url_for("index"))
        
        if not is_guild_owner(guild_id, current_user.id) and not is_bot_admin(current_user.id):
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for("index"))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
        
    # Ensure all required environment variables are set
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET or not DISCORD_REDIRECT_URI:
        flash("Discord OAuth2 configuration is incomplete. Please check your environment variables.", "danger")
        return redirect(url_for("index"))
    
    # Print debug information
    print(f"Discord Client ID: {DISCORD_CLIENT_ID}")
    print(f"Discord Redirect URI: {DISCORD_REDIRECT_URI}")
    
    # Construct the OAuth2 URL with proper parameters
    auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    
    print(f"Redirecting to Discord OAuth2 URL: {auth_url}")
    return redirect(auth_url)

@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        if not code:
            flash("No authorization code received from Discord.", "danger")
            return redirect(url_for("index"))
        
        print(f"Received authorization code: {code}")
        
        # Exchange code for access token
        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        print(f"Making token request to Discord API with redirect_uri: {DISCORD_REDIRECT_URI}")
        response = requests.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers)
        
        if response.status_code != 200:
            error_data = response.json()
            print(f"Discord token request failed with status {response.status_code}: {error_data}")
            flash(f"Failed to authenticate with Discord: {error_data.get('error_description', 'Unknown error')}", "danger")
            return redirect(url_for("index"))
        
        tokens = response.json()
        access_token = tokens.get("access_token")
        
        if not access_token:
            print("No access token received from Discord")
            flash("Failed to get access token from Discord.", "danger")
            return redirect(url_for("index"))
        
        print("Successfully received access token from Discord")
        
        # Store access token in session
        session["access_token"] = access_token
        
        # Get user information
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me", headers=headers)
        
        if user_response.status_code != 200:
            print(f"Failed to get user info with status {user_response.status_code}: {user_response.text}")
            flash("Failed to get user information from Discord.", "danger")
            return redirect(url_for("index"))
        
        user_data = user_response.json()
        print(f"Successfully retrieved user data: {user_data['username']}")
        
        # Create user object
        user = User(
            user_id=user_data["id"],
            username=user_data["username"],
            avatar=user_data.get("avatar")
        )
        
        # Login user
        login_user(user)
        print(f"User {user.username} logged in successfully")
        
        # Store minimal user data in session
        session["user_data"] = {
            "id": user_data["id"],
            "username": user_data["username"],
            "avatar": user_data.get("avatar")
        }
        
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        print(f"Error during Discord authentication: {str(e)}")
        flash("An unexpected error occurred during authentication.", "danger")
        return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))

@app.route("/guilds")
@login_required
def guilds():
    # Get user's guilds
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    guilds_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=headers)
    
    if guilds_response.status_code != 200:
        flash("Failed to get guild information.", "danger")
        return redirect(url_for("logout"))
    
    guilds_data = guilds_response.json()
    bot_guilds = []
    
    # Get all guilds where the bot is present
    bot_headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    bot_guilds_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=bot_headers)
    if bot_guilds_response.status_code == 200:
        bot_guilds = [guild["id"] for guild in bot_guilds_response.json()]
    
    # Filter guilds where user has admin permissions and bot is present
    admin_guilds = []
    for guild in guilds_data:
        if guild["id"] in bot_guilds:
            # Check if user has admin permissions
            member_response = requests.get(
                f"{DISCORD_API_ENDPOINT}/guilds/{guild['id']}/members/{current_user.id}",
                headers=bot_headers
            )
            
            if member_response.status_code == 200:
                member_data = member_response.json()
                if member_data.get("permissions", 0) & 0x8:  # 0x8 is ADMINISTRATOR permission
                    admin_guilds.append(guild)
    
    return render_template("guilds.html", 
                         user=current_user,
                         guilds=admin_guilds,
                         max_hints=MAX_HINTS,
                         max_attempts=MAX_ATTEMPTS)

@app.route("/guild/<guild_id>")
@login_required
@guild_owner_required
def guild_settings(guild_id):
    # Get guild information
    headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    response = requests.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}", headers=headers)
    
    if response.status_code != 200:
        flash("Failed to get guild information.", "danger")
        return redirect(url_for("guilds"))
    
    guild_data = response.json()
    
    # Get current settings
    config = ServerConfig()
    guild_config = {
        "wordle_channel": config.get_wordle_channel(guild_id),
        "max_hints": config.get_max_hints(guild_id),
        "max_attempts": config.get_max_attempts(guild_id),
        "words": config.get_words(guild_id),
        "game_history": config.get_game_history(guild_id)
    }
    
    # Get channels
    channels_response = requests.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}/channels", headers=headers)
    channels = []
    if channels_response.status_code == 200:
        channels = [channel for channel in channels_response.json() if channel["type"] == 0]  # Only text channels
    
    return render_template(
        "guild_settings.html", 
        user=current_user, 
        guild=guild_data, 
        config=guild_config,
        channels=channels,
        max_hints=MAX_HINTS,
        max_attempts=MAX_ATTEMPTS
    )

@app.route("/guild/<guild_id>/settings", methods=["POST"])
@login_required
@guild_owner_required
def update_guild_settings(guild_id):
    try:
        # Get form data
        wordle_channel = request.form.get("wordle_channel")
        max_hints = request.form.get("max_hints", type=int)
        max_attempts = request.form.get("max_attempts", type=int)
        
        # Validate data
        if not wordle_channel:
            flash("Wordle channel is required.", "danger")
            return redirect(url_for("guild_settings", guild_id=guild_id))
        
        if max_hints is None or max_hints < 0 or max_hints > 10:
            flash("Max hints must be between 0 and 10.", "danger")
            return redirect(url_for("guild_settings", guild_id=guild_id))
        
        if max_attempts is None or max_attempts < 1 or max_attempts > 10:
            flash("Max attempts must be between 1 and 10.", "danger")
            return redirect(url_for("guild_settings", guild_id=guild_id))
        
        # Get guild name
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        guild_response = requests.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}", headers=headers)
        if guild_response.status_code != 200:
            flash("Failed to get guild information.", "danger")
            return redirect(url_for("guild_settings", guild_id=guild_id))
        
        guild_data = guild_response.json()
        guild_name = guild_data["name"]
        
        # Update settings
        config = ServerConfig()
        config.set_wordle_channel(guild_id, int(wordle_channel), guild_name)
        config.set_max_hints(guild_id, max_hints)
        config.set_max_attempts(guild_id, max_attempts)
        
        # Create embed message
        embed = {
            "title": "Wordle Settings Updated",
            "description": f"Settings for {guild_name} have been updated.",
            "color": 0x00ff00,  # Green
            "fields": [
                {
                    "name": "Wordle Channel",
                    "value": f"<#{wordle_channel}>",
                    "inline": True
                },
                {
                    "name": "Max Hints",
                    "value": str(max_hints),
                    "inline": True
                },
                {
                    "name": "Max Attempts",
                    "value": str(max_attempts),
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Updated by {current_user.username}"
            }
        }
        
        # Send embed to the wordle channel using the bot
        channel_response = requests.post(
            f"{DISCORD_API_ENDPOINT}/channels/{wordle_channel}/messages",
            headers=headers,
            json={"embeds": [embed]}
        )
        
        if channel_response.status_code != 200:
            print(f"Failed to send message: {channel_response.status_code}")
        
        flash("Settings updated successfully.", "success")
        return redirect(url_for("guild_settings", guild_id=guild_id))
        
    except Exception as e:
        print(f"Error updating guild settings: {str(e)}")
        flash("An error occurred while updating settings.", "danger")
        return redirect(url_for("guild_settings", guild_id=guild_id))

@app.route("/guild/<guild_id>/words", methods=["POST"])
@login_required
@guild_owner_required
def update_guild_words(guild_id):
    # Get form data
    words_text = request.form.get("words")
    
    if not words_text:
        flash("Words are required.", "danger")
        return redirect(url_for("guild_settings", guild_id=guild_id))
    
    # Process words
    words = [w.strip().lower() for w in words_text.split("\n") if len(w.strip()) == 5]
    
    if not words:
        flash("No valid words found. Words must be 5 letters long.", "danger")
        return redirect(url_for("guild_settings", guild_id=guild_id))
    
    # Add words
    config = ServerConfig()
    for word in words:
        config.add_word(guild_id, word, guild_name=request.form.get("guild_name"))
    
    flash("Words added successfully.", "success")
    return redirect(url_for("guild_settings", guild_id=guild_id))

@app.route("/admin")
@login_required
@admin_required
def admin():
    return render_template("admin.html", user=current_user)

@app.route("/dashboard")
@login_required
def dashboard():
    # Get user's guilds
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    guilds_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=headers)
    
    if guilds_response.status_code != 200:
        flash("Failed to get guild information.", "danger")
        return redirect(url_for("logout"))
    
    guilds_data = guilds_response.json()
    bot_guilds = []
    
    # Get all guilds where the bot is present
    bot_headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    bot_guilds_response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=bot_headers)
    if bot_guilds_response.status_code == 200:
        bot_guilds = [guild["id"] for guild in bot_guilds_response.json()]
    
    # Filter guilds where user has admin permissions and bot is present
    admin_guilds = []
    for guild in guilds_data:
        if guild["id"] in bot_guilds:
            # Check if user has admin permissions
            member_response = requests.get(
                f"{DISCORD_API_ENDPOINT}/guilds/{guild['id']}/members/{current_user.id}",
                headers=bot_headers
            )
            
            if member_response.status_code == 200:
                member_data = member_response.json()
                # Check if user has admin permissions
                if member_data.get("permissions", 0) & 0x8:  # 0x8 is ADMINISTRATOR permission
                    admin_guilds.append(guild)
                else:
                    # Check if user is owner
                    guild_info_response = requests.get(
                        f"{DISCORD_API_ENDPOINT}/guilds/{guild['id']}",
                        headers=bot_headers
                    )
                    if guild_info_response.status_code == 200:
                        guild_info = guild_info_response.json()
                        if str(guild_info["owner_id"]) == str(current_user.id):
                            admin_guilds.append(guild)
    
    return render_template("dashboard.html", 
                         user=current_user,
                         guilds=admin_guilds)

if __name__ == "__main__":
    app.run(debug=True) 