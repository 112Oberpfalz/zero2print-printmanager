# Zero2Print PrintManager - Update-Befehle für den Pi

## Schnell-Update (empfohlen)

```bash
cd ~/zero2print-printmanager
bash update_pi.sh
```

Das Skript führt automatisch aus:
- Code aktualisieren (`git pull`)
- Python-Dependencies installieren (`pip install -r requirements.txt`)
- Datenbank-Migrationen ausführen
- Service neu starten

---

## Manuell Schritt für Schritt

Falls das Skript nicht funktioniert, kannst du diese Befehle einzeln ausführen:

### 1. Projektverzeichnis
```bash
cd ~/zero2print-printmanager
```

### 2. Code aktualisieren
```bash
git pull
```

### 3. Virtual Environment aktivieren
```bash
source .venv/bin/activate
```

### 4. Python-Dependencies installieren
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Datenbank-Migrationen ausführen
```bash
python -c "from app.migrations import run_migrations; run_migrations()"
```

### 6. Service neu starten
```bash
sudo systemctl restart zero2print
```

### 7. Status prüfen
```bash
sudo systemctl status zero2print
```

---

## Logs anschauen

Falls etwas nicht funktioniert:

```bash
# Letzte 50 Log-Zeilen
sudo journalctl -u zero2print -n 50

# Fortlaufende Logs (mit Strg+C beenden)
sudo journalctl -u zero2print -f
```

---

## Datenbank-Backup vor Updates

Um sicherzustellen, dass du deine Daten nicht verlierst:

```bash
cp data/database.sqlite ~/database-backup-$(date +%Y%m%d-%H%M%S).sqlite
```

---

## Wenn etwas schiefgeht

Datenbank wiederherstellen:

```bash
cp ~/database-backup-YYYYMMDD-HHMMSS.sqlite data/database.sqlite
sudo systemctl restart zero2print
```

Oder den letzten bekannten Stand zurückrollen:

```bash
git log --oneline -10        # Letzte 10 Commits anschauen
git reset --hard <commit-id> # Zu einem älteren Commit zurückkehren
```
