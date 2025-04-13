#!/bin/bash

# Farben für die Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktion zum Überprüfen des Exit-Codes
check_error() {
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Warnung: Ein Fehler ist aufgetreten, aber wir fahren fort...${NC}"
    fi
}

echo -e "${YELLOW}=== Installation des Discord Wordle Bots ===${NC}\n"

# Überprüfe, ob das Skript als root ausgeführt wird
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Das Skript sollte nicht als root ausgeführt werden!${NC}"
    exit 1
fi

# Aktualisiere Paketliste (ignoriere Fehler)
echo -e "${YELLOW}Aktualisiere Paketliste...${NC}"
sudo apt-get update || true

# Installiere Python und pip
echo -e "${YELLOW}Installiere Python und pip...${NC}"
sudo apt-get install -y python3 python3-pip
check_error

# Installiere virtuelle Umgebung
echo -e "${YELLOW}Installiere virtuelle Umgebung...${NC}"
sudo apt-get install -y python3-venv
check_error

# Erstelle virtuelle Umgebung
echo -e "${YELLOW}Erstelle virtuelle Umgebung...${NC}"
python3 -m venv venv
check_error

# Aktiviere virtuelle Umgebung
echo -e "${YELLOW}Aktiviere virtuelle Umgebung...${NC}"
source venv/bin/activate
check_error

# Installiere Abhängigkeiten
echo -e "${YELLOW}Installiere Abhängigkeiten...${NC}"
pip install -r requirements.txt
check_error

# Abfrage der sensiblen Daten
echo -e "\n${YELLOW}=== Bot Konfiguration ===${NC}"
read -p "Discord Bot Token: " BOT_TOKEN
read -p "Discord Client Secret: " CLIENT_SECRET
read -p "Discord User ID (für Admin-Zugriff): " ADMIN_ID

# Erstelle Konfigurationsdatei
echo -e "${YELLOW}Erstelle Konfigurationsdatei...${NC}"
cat > config.py << EOL
# Bot Konfiguration
TOKEN = "$BOT_TOKEN"
DISCORD_CLIENT_SECRET = "$CLIENT_SECRET"
ADMIN_IDS = ["$ADMIN_ID"]

# Flask Konfiguration
FLASK_SECRET_KEY = "avb345"
FLASK_APP = "dashboard/app.py"
FLASK_ENV = "development"

# Bot Einstellungen
MAX_HINTS = 3
MAX_ATTEMPTS = 6
EOL

# Mache Skripte ausführbar
echo -e "${YELLOW}Mache Skripte ausführbar...${NC}"
chmod +x start_bot.sh
check_error

echo -e "\n${GREEN}Installation abgeschlossen!${NC}"
echo -e "Starte den Bot mit: ${YELLOW}./start_bot.sh${NC}"
echo -e "Die virtuelle Umgebung wurde aktiviert. Um sie zu deaktivieren, geben Sie 'deactivate' ein." 