import os
import bcrypt
from dotenv import load_dotenv

## Worde Variablen. When use one do a # behind the variable and write # - used
load_dotenv()
MAX_HINTS = int(os.getenv("MAX_HINTS", 0))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 0))
WORDS_FILE = os.getenv("WORDS_FILE") # - used
DATA_FILE = os.getenv("DATA_FILE")
CONFIG_FILE = os.getenv("CONFIG_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
DAILY_FILE = os.getenv("DAILY_FILE")

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