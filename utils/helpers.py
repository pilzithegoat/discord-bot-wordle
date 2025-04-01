import os
import bcrypt

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

def get_scope_label(scope: str) -> str:
    return "Server" if scope == "server" else "Global"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(stored_hash: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash.encode())

# Words initialization
WORDS_FILE = os.getenv("WORDS_FILE", "words.txt")
if not os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "w") as f:
        f.write("\n".join(["apfel", "birne", "banane", "mango", "beere"]))

with open(WORDS_FILE) as f:
    WORDS = [w.strip().lower() for w in f.readlines() if len(w.strip()) == 5]