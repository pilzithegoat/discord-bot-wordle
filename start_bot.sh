#!/bin/bash

# Farben für die Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Überprüfe, ob die virtuelle Umgebung aktiviert ist
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Aktiviere virtuelle Umgebung...${NC}"
    source venv/bin/activate
fi

# Überprüfe, ob config.py existiert
if [ ! -f "config.py" ]; then
    echo -e "${RED}Fehler: config.py nicht gefunden. Bitte führen Sie zuerst install.sh aus.${NC}"
    exit 1
fi

# Starte den Bot
echo -e "${GREEN}Starte Discord Wordle Bot...${NC}"
python main.py 