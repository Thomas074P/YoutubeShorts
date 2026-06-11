# YoutubeShorts

- sudo apt install python3-full
- python3 -m venv venv
- source venv/bin/activate
- pip install google-auth-oauthlib google-api-python-client
- pip install -r requirements.txt
- sudo apt install ffmpeg

# Generate and upload a video
- source venv/bin/activate
- python3 generate_video.py
- python3 upload_shorts.py
