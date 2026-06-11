import os
import requests
from pathlib import Path
from moviepy.editor import (
    ImageClip, CompositeVideoClip, concatenate_videoclips,
    TextClip, AudioFileClip, ColorClip
)
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class AIVideoGenerator:
    """
    Generiert 10-Sekunden-Videos mit AI-generierten Bildern und Musik.
    Ideal für YouTube Shorts mit Themen wie "Jesus als König".
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.output_dir = Path("generated_videos")
        self.output_dir.mkdir(exist_ok=True)
        self.fps = 24
        self.duration = 10
        
    def generate_image_with_dall_e(self, prompt: str, filename: str = "generated_image.png") -> str:
        """
        Generiert ein Bild mit OpenAI DALL-E API.
        
        Args:
            prompt: Beschreibung des gewünschten Bildes
            filename: Name der zu speichernden Datei
            
        Returns:
            Pfad zur gespeicherten Bilddatei
        """
        if not self.openai_api_key:
            print("⚠️  OPENAI_API_KEY nicht gesetzt. Verwende Fallback-Bild.")
            return self._create_fallback_image(filename)
        
        try:
            print(f"🎨 Generiere Bild mit DALL-E: {prompt}")
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            image_url = response.json()["data"][0]["url"]
            
            # Lade Bild herunter
            img_response = requests.get(image_url, timeout=30)
            img = Image.open(io.BytesIO(img_response.content))
            
            # Konvertiere zu 9:16 Format (Vertical Video)
            img = self._convert_to_vertical(img)
            
            filepath = self.output_dir / filename
            img.save(filepath, quality=95)
            
            print(f"✅ Bild gespeichert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Fehler bei DALL-E: {e}")
            return self._create_fallback_image(filename)
    
    def _convert_to_vertical(self, img: Image.Image, width: int = 1080, height: int = 1920) -> Image.Image:
        """Konvertiert Bild zu vertikalem Format (9:16)"""
        img = img.convert("RGB")
        
        # Zuschneiden oder Padding
        aspect = img.width / img.height
        target_aspect = width / height
        
        if aspect > target_aspect:
            # Bild ist zu breit
            new_width = int(img.height * target_aspect)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Bild ist zu hoch
            new_height = int(img.width / target_aspect)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Skaliere auf gewünschte Größe
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        return img
    
    def _create_fallback_image(self, filename: str) -> str:
        """Erstellt ein Fallback-Bild, wenn API nicht verfügbar ist"""
        print("📝 Erstelle Fallback-Bild (No API)...")
        
        width, height = 1080, 1920
        img = Image.new("RGB", (width, height), color=(25, 25, 112))  # Midnight Blue
        draw = ImageDraw.Draw(img)
        
        # Füge Text hinzu
        try:
            # Versuche, eine große Schrift zu laden
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        except:
            font = ImageFont.load_default()
        
        text = "👑 JESUS\nKÖNIG\nDER\nKÖNIGE"
        
        # Zentriere Text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Zeichne Text mit Glow-Effekt
        draw.multiline_text((x, y), text, font=font, fill=(255, 215, 0), align="center")  # Gold
        
        filepath = self.output_dir / filename
        img.save(filepath)
        return str(filepath)
    
    def download_music(self, music_url: str = None, filename: str = "background_music.mp3") -> str:
        """
        Lädt Musik herunter oder erstellt stille Audio.
        
        Args:
            music_url: URL zur Musikdatei (optional)
            filename: Name der zu speichernden Datei
            
        Returns:
            Pfad zur Musikdatei
        """
        filepath = self.output_dir / filename
        
        if music_url:
            try:
                print(f"🎵 Lade Musik herunter: {music_url}")
                response = requests.get(music_url, timeout=30)
                response.raise_for_status()
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Musik gespeichert: {filepath}")
                return str(filepath)
            except Exception as e:
                print(f"❌ Fehler beim Download: {e}")
                return self._create_silent_audio(filename)
        else:
            return self._create_silent_audio(filename)
    
    def _create_silent_audio(self, filename: str) -> str:
        """Erstellt eine stille Audio-Datei"""
        from scipy.io import wavfile
        
        print("🔇 Erstelle stille Audio...")
        filepath = self.output_dir / filename.replace(".mp3", ".wav")
        
        # 10 Sekunden stille Audio (44100 Hz)
        sample_rate = 44100
        duration = self.duration
        silence = np.zeros(int(sample_rate * duration))
        
        wavfile.write(str(filepath), sample_rate, silence.astype(np.int16))
        print(f"✅ Audio gespeichert: {filepath}")
        return str(filepath)
    
    def create_video(
        self,
        image_path: str,
        music_path: str = None,
        title: str = "Jesus - König der Könige",
        output_filename: str = "jesus_king_short.mp4"
    ) -> str:
        """
        Erstellt ein 10-Sekunden-Video aus Bildern und Musik.
        
        Args:
            image_path: Pfad zum Bild
            music_path: Pfad zur Musik (optional)
            title: Titel für das Video
            output_filename: Name der Output-Videodatei
            
        Returns:
            Pfad zur erstellten Videodatei
        """
        print("\n🎬 Erstelle Video...")
        
        try:
            # Lade Bild
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Bild nicht gefunden: {image_path}")
            
            image_clip = ImageClip(image_path).set_duration(self.duration)
            
            # Erstelle Text-Overlay
            txt_clip = TextClip(
                txt=title,
                fontsize=80,
                color="gold",
                font="Arial-Bold",
                method="caption",
                size=(1000, 300),
                align="center"
            ).set_duration(self.duration).set_position(("center", "center"))
            
            # Kombiniere Video
            video = CompositeVideoClip([image_clip, txt_clip])
            
            # Füge Audio hinzu, falls vorhanden
            if music_path and os.path.exists(music_path):
                try:
                    audio = AudioFileClip(music_path)
                    
                    # Verkürze Audio auf 10 Sekunden, falls nötig
                    if audio.duration > self.duration:
                        audio = audio.subclipped(0, self.duration)
                    elif audio.duration < self.duration:
                        # Loop die Musik, falls zu kurz
                        repeats = int(self.duration / audio.duration) + 1
                        audio = concatenate_videoclips([audio] * repeats).subclipped(0, self.duration)
                    
                    video = video.set_audio(audio)
                except Exception as e:
                    print(f"⚠️  Fehler beim Audio-Einfügen: {e}")
            
            # Speichere Video
            output_path = self.output_dir / output_filename
            print(f"💾 Speichere Video unter: {output_path}")
            
            video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video.close()
            if music_path and os.path.exists(music_path):
                try:
                    audio.close()
                except:
                    pass
            
            print(f"✅ Video erfolgreich erstellt: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Videos: {e}")
            raise
    
    def generate_complete_short(
        self,
        theme: str = "Jesus als König mit goldenem Licht",
        music_url: str = None,
        title: str = "Jesus - König der Könige #shorts",
        output_filename: str = "jesus_king_short.mp4"
    ) -> str:
        """
        Kompletter Workflow: Bild generieren -> Audio laden -> Video erstellen
        
        Args:
            theme: Beschreibung für das Bild
            music_url: URL zur Musikdatei (optional)
            title: Titel für das Video
            output_filename: Name der Output-Datei
            
        Returns:
            Pfad zur erstellten Videodatei
        """
        print("="*50)
        print("🎬 STARTE AI VIDEO GENERIERUNG")
        print("="*50)
        
        # Schritt 1: Bild generieren
        image_path = self.generate_image_with_dall_e(theme)
        
        # Schritt 2: Musik laden
        music_path = self.download_music(music_url)
        
        # Schritt 3: Video erstellen
        video_path = self.create_video(image_path, music_path, title, output_filename)
        
        print("="*50)
        print("✅ VIDEO GENERATION ABGESCHLOSSEN")
        print(f"📁 Speicherort: {video_path}")
        print("="*50)
        
        return video_path


def main():
    """Beispiel: Generiere ein Video von Jesus als König"""
    
    generator = AIVideoGenerator()
    
    # Prompt für DALL-E
    prompt = (
        "Jesus Christ as King, sitting on a majestic golden throne, "
        "wearing royal purple robes with a golden crown, divine golden light radiating, "
        "heavenly atmosphere, 8k, ultra high quality, professional art, "
        "vertical portrait format 9:16"
    )
    
    # Generiere komplettes Video
    video_path = generator.generate_complete_short(
        theme=prompt,
        music_url=None,  # Verwende stille Audio
        title="👑 JESUS\nKÖNIG DER KÖNIGE",
        output_filename="jesus_king_10sec.mp4"
    )
    
    print(f"\n📹 Video bereit zum Upload: {video_path}")
    print("💡 Tipp: Nutze 'upload_shorts.py' um das Video automatisch hochzuladen!")


if __name__ == "__main__":
    main()
