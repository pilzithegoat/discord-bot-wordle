# 🎮 Discord Wordle Bot

Ein vollständig anpassbarer Wordle-Bot für Discord-Server mit Mehrsprachigkeit, Statistiken und Admin-Webinterface.

![Bot Demo](https://via.placeholder.com/1280x720.png?text=Wordle+Bot+Demo+Preview)

## 🌟 Hauptfunktionen
- **🎮 Mehrsprachiges Wordle-Spiel** (DE/EN)
- **🌞 Tägliche Challenges** mit globaler Bestenliste
- **📊 Detaillierte Statistiken** pro Spieler/Server
- **🎭 Anonymer Spielmodus** mit Passwortschutz
- **⚙️ Web-Dashboard** für Serverkonfiguration
- **🔧 Eigenes Wortlisten** einfach anpassbar

## 🚀 Installation
### Voraussetzungen
- Python 3.10+
- Discord Server mit Admin-Rechten
- [Bot-Token](https://discord.com/developers/applications)

### Schritt-für-Schritt
```
# 1. Repository klonen
git clone https://github.com/pilzithegoat/discord-bot-wordle.git
cd discord-bot-wordle

# 2. Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Konfigurationsdatei erstellen
cp .env.example .env
nano .env  # Bearbeite mit deinen Daten
```

### 📋 .env-Beispieldatei
```
TOKEN=dein_bot_token_hier
DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=dein_client_secret_hier
FLASK_SECRET=ein_sicherer_geheimer_schluessel
```

## 🕹️ Verwendung
### Grundlegende Befehle
| Befehl          | Beschreibung                  | Beispiel               |
|-----------------|-------------------------------|------------------------|
| `/wordle`       | Startet neues Spiel           | `/wordle`              |
| `/daily`        | Tägliche Challenge            | `/daily`               |
| `/stats @user`  | Zeigt Spielstatistiken        | `/stats @WordleFan23`  |
| `/setup`        | Serverkonfiguration starten   | `/setup`               |
| `/language`     | Sprache ändern (DE/EN)        | `/language en`         |

![Befehlsbeispiel](https://via.placeholder.com/600x300.png?text=Command+Examples)

## 🔧 Anpassungen
### Eigene Wörter hinzufügen
1. Öffne die Wortdateien:
   ```
   nano data/words_de.txt  # Deutsche Wörter
   nano data/words_en.txt  # Englische Wörter
   ```
2. Füge Wörter hinzu (pro Zeile ein 5-Buchstaben-Wort):
   ```
   KLIMA
   WOCHE
   ZEBRA
   ```

### Web-Dashboard
1. Starte den Bot
2. Öffne im Browser:
   ```
   http://localhost:5000
   ```
3. **Admin-Funktionen:**
   - Wordle-Kanal festlegen
   - Server-spezifische Wortlisten
   - Sprachkonfiguration
   - Statistiken einsehen

![Dashboard Demo](https://via.placeholder.com/800x400.png?text=Admin+Dashboard+Preview)

## 🤖 Bot einladen
1. Generiere Einladungslink:
   ```
   https://discord.com/api/oauth2/authorize?
   client_id=DEINE_CLIENT_ID&
   permissions=277025770560&
   scope=bot%20applications.commands
   ```
2. Wähle Server aus und bestätige

## 🛠️ Entwicklung
### Beitragsrichtlinien
1. Fork das Repository
2. Erstelle Feature-Branch:
   ```
   git checkout -b feature/meine-neue-funktion
   ```
3. Committe Änderungen:
   ```
   git commit -m "füge awesome feature hinzu"
   ```
4. Push zum Branch:
   ```
   git push origin feature/meine-neue-funktion
   ```
5. Öffne Pull Request

## 📜 Lizenz
MIT License - Siehe [LICENSE](LICENSE) für Details

---

> **Hinweis:** Dieser Bot steht in keiner Verbindung zum offiziellen Wordle-Spiel.  
> Probleme? [Issue erstellen](https://github.com/pilzithegoat/discord-bot-wordle/issues)
>> **Extra Hinweis** Dieser Bot ist ein Experiment von mir um zugucken was man alles 
>> mit KI machen kann, deswegen ist dieser Bot zu 100% mit der KI [DeepSeek](https://www.deepseek.com) erstellt worden.