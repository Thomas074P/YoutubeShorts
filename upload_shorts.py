import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# API-Bereich für den YouTube-Upload
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv nicht installiert oder .env nicht vorhanden; weiter mit Umgebungsvariablen
    pass

def main():
    # Erlaubt HTTP für lokale Tests (wichtig für den OAuth-Login im Browser)
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"

    # =================================================================
    # HIER DEINE ZUGANGSDATEN EINTRAGEN (wird aus .env oder Umgebungsvariablen geladen)
    # Erwartete Variablen: CLIENT_ID / CLIENT_SECRET oder YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET
    # =================================================================
    CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("YOUTUBE_CLIENT_ID") or "HIER_DEINE_CLIENT_ID_AUS_DEM_FENSTER_EINFÜGEN"
    CLIENT_SECRET = os.getenv("CLIENT_SECRET") or os.getenv("YOUTUBE_CLIENT_SECRET") or "HIER_DEIN_CLIENT_SECRET_AUS_DEM_FENSTER_EINFÜGEN"

    if CLIENT_ID.startswith("HIER_") or CLIENT_SECRET.startswith("HIER_"):
        print("Warnung: CLIENT_ID und/oder CLIENT_SECRET sind nicht gesetzt. Lege eine .env mit CLIENT_ID/CLIENT_SECRET an oder exportiere Umgebungsvariablen.")
    
    # Pfad zu deinem Video (muss vertikal sein und < 60 Sekunden)
    VIDEO_DATEI_PFAD = "dein_video.mp4"
    # =================================================================

    # Manuelle Konfiguration statt client_secret.json
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    # Authentifizierung starten
    print("Starte Authentifizierung... Bitte öffne den Browser, falls er sich nicht automatisch öffnet.")
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
        client_config, SCOPES)
    credentials = flow.run_local_server(port=0)
    
    # API-Client aufbauen
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # Metadaten für das Short festlegen
    body = {
        "snippet": {
            "title": "Mein erstes API Short #shorts",  # #shorts sorgt für die Einsortierung
            "description": "Automatisch hochgeladen per API! #shorts",
            "categoryId": "22"  # 22 = Menschen & Blogs
        },
        "status": {
            "privacyStatus": "private"  # 'private', 'public' oder 'unlisted'
        }
    }

    # Video-Datei für den Upload vorbereiten
    if not os.path.exists(VIDEO_DATEI_PFAD):
        print(f"Fehler: Die Datei '{VIDEO_DATEI_PFAD}' wurde nicht gefunden. Bitte passe den Pfad im Code an.")
        return

    media = MediaFileUpload(VIDEO_DATEI_PFAD, chunksize=-1, resumable=True, mimetype="video/mp4")

    # Upload-Anfrage absenden
    print(f"Upload von '{VIDEO_DATEI_PFAD}' gestartet... Bitte warten.")
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()

        print("\n" + "="*40)
        print("ERFOLG!")
        print(f"Video erfolgreich hochgeladen.")
        print(f"Video-ID: {response['id']}")
        print(f"Link: https://www.youtube.com/shorts/{response['id']}")
        print("="*40)

    except googleapiclient.errors.HttpError as e:
        print(f"\nEin API-Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()