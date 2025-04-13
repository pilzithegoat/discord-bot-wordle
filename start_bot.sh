#!/bin/bash

# Farben für die Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion zum Abfragen von Passwörtern
ask_password() {
    local prompt="$1"
    local var_name="$2"
    local password=""
    
    while true; do
        read -s -p "$prompt: " password
        echo
        if [ -z "$password" ]; then
            echo -e "${RED}Fehler: Eingabe darf nicht leer sein!${NC}"
        else
            break
        fi
    done
    
    eval "$var_name='$password'"
}

# Funktion zum Abfragen von Werten
ask_value() {
    local prompt="$1"
    local var_name="$2"
    local value=""
    
    while true; do
        read -p "$prompt: " value
        if [ -z "$value" ]; then
            echo -e "${RED}Fehler: Eingabe darf nicht leer sein!${NC}"
        else
            break
        fi
    done
    
    eval "$var_name='$value'"
}

clear
echo -e "${YELLOW}=== Discord Wordle Bot Setup ===${NC}\n"

# Bot Token
ask_password "Discord Bot Token" DISCORD_TOKEN

# Flask Konfiguration
ask_value "Flask Secret Key" FLASK_KEY
ask_value "Discord Client ID" CLIENT_ID
ask_password "Discord Client Secret" CLIENT_SECRET
ask_value "Redirect URI (z.B. http://localhost:5000/callback)" REDIRECT_URI

# Zusätzliche Umgebungsvariablen
read -p "Zusätzliche Umgebungsvariablen (optional, leer lassen wenn keine): " ENV_VARS

# Konfiguration speichern
echo "DISCORD_TOKEN=$DISCORD_TOKEN" > bot_config.txt
echo "FLASK_KEY=$FLASK_KEY" >> bot_config.txt
echo "CLIENT_ID=$CLIENT_ID" >> bot_config.txt
echo "CLIENT_SECRET=$CLIENT_SECRET" >> bot_config.txt
echo "REDIRECT_URI=$REDIRECT_URI" >> bot_config.txt
echo "ENV_VARS=$ENV_VARS" >> bot_config.txt

# Umgebungsvariablen setzen
export DISCORD_TOKEN
export FLASK_KEY
export CLIENT_ID
export CLIENT_SECRET
export REDIRECT_URI

# Zusätzliche Umgebungsvariablen setzen
if [ ! -z "$ENV_VARS" ]; then
    IFS=' ' read -ra VARS <<< "$ENV_VARS"
    for var in "${VARS[@]}"; do
        if [[ $var == *"="* ]]; then
            export "$var"
        fi
    done
fi

echo -e "\n${GREEN}Konfiguration gespeichert!${NC}"
echo -e "${YELLOW}Starte Bot...${NC}\n"

# Bot starten mit Logging
python3 -u main.py 2>&1 | tee bot.log 