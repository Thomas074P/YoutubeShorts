# YoutubeShorts

- sudo apt install python3-full
- python3 -m venv venv
- source venv/bin/activate
- pip install google-auth-oauthlib google-api-python-client
- # 1. Dependencies installieren
pip install -r requirements.txt

# 2. FFmpeg installieren (falls nicht vorhanden)
sudo apt install ffmpeg

# 3. Video generieren!
python3 generate_video.py
