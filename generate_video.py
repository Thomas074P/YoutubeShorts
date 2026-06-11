#!/usr/bin/env python3
"""
Generiert 10-Sekunden-Videos für YouTube Shorts mit AI-generierten Bildern.
Vereinfachte Version mit minimalen Dependencies.
"""

import os
import sys
from pathlib import Path
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class AIVideoGenerator:
    """
    Generiert 10-Sekunden-Videos mit AI-generierten Bildern und Musik.
    Nutzt FFmpeg für Video-Verarbeitung (keine moviepy nötig).
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.output_dir = Path("generated_videos")
        self.output_dir.mkdir(exist_ok=True)
        self.fps = 24
        self.duration = 10
        self.width = 1080
        self.height = 1920
        
        # Überprüfe FFmpeg
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Überprüfe ob FFmpeg installiert ist"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FEHLER: FFmpeg ist nicht installiert!")
            print("\n📥 Installation:")
            print("   Ubuntu/Debian: sudo apt install ffmpeg")
            print("   macOS: brew install ffmpeg")
            print("   Windows: https://ffmpeg.org/download.html")
            sys.exit(1)
    
    def generate_image_with_dall_e(self, prompt: str, filename: str = "generated_image.png") -> str:
        """
        Generiert ein Bild mit OpenAI DALL-E API.
        """
        if not self.openai_api_key:
            print("⚠️  OPENAI_API_KEY nicht gesetzt. Verwende Fallback-Bild.")
            return self._create_fallback_image(filename)
        
        try:
            print(f"🎨 Generiere Bild mit DALL-E...")
            import requests
            
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
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code}")
            
            image_url = response.json()["data"][0]["url"]
            
            # Lade Bild herunter
            img_response = requests.get(image_url, timeout=30)
            img = Image.open(__import__('io').BytesIO(img_response.content))
            
            # Konvertiere zu 9:16 Format
            img = self._convert_to_vertical(img)
            
            filepath = self.output_dir / filename
            img.save(filepath, quality=95)
            
            print(f"✅ Bild gespeichert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Fehler bei DALL-E: {e}")
            return self._create_fallback_image(filename)
    
    def _convert_to_vertical(self, img: Image.Image) -> Image.Image:
        """Konvertiert Bild zu vertikalem 9:16 Format"""
        img = img.convert("RGB")
        
        aspect = img.width / img.height
        target_aspect = self.width / self.height
        
        if aspect > target_aspect:
            new_width = int(img.height * target_aspect)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            new_height = int(img.width / target_aspect)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        return img
    
    def _create_fallback_image(self, filename: str = "fallback_image.png") -> str:
        """Erstellt ein schönes Fallback-Bild"""
        print("📝 Erstelle Fallback-Bild...")
        
        # Erstelle Gradient-Hintergrund (Blau zu Gold)
        img = Image.new("RGB", (self.width, self.height), color=(25, 25, 112))
        pixels = img.load()
        
        # Erstelle Gradient-Effekt
        for y in range(self.height):
            r = int(25 + (255 - 25) * (y / self.height))
            g = int(25 + (215 - 25) * (y / self.height))
            b = int(112 + (0 - 112) * (y / self.height))
            for x in range(self.width):
                pixels[x, y] = (r, g, b)
        
        draw = ImageDraw.Draw(img)
        
        # Lade Schrift
        try:
            font_size = 120
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            font = ImageFont.load_default()
            font_small = font
        
        # Zeichne Text
        text_lines = ["👑", "JESUS", "KÖNIG DER", "KÖNIGE"]
        
        total_height = 0
        bbox_list = []
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font if line != text_lines[0] else font_small)
            bbox_list.append(bbox)
            total_height += bbox[3] - bbox[1] + 20
        
        y_pos = (self.height - total_height) // 2
        
        for i, line in enumerate(text_lines):
            current_font = font_small if i == 0 else font
            bbox = draw.textbbox((0, 0), line, font=current_font)
            text_width = bbox[2] - bbox[0]
            x_pos = (self.width - text_width) // 2
            
            # Zeichne Text mit Glow
            for offset in range(3, 0, -1):
                draw.text(
                    (x_pos, y_pos),
                    line,
                    font=current_font,
                    fill=(255, 200, 0, 100)
                )
            
            draw.text(
                (x_pos, y_pos),
                line,
                font=current_font,
                fill=(255, 215, 0)
            )
            
            y_pos += (bbox[3] - bbox[1]) + 20
        
        filepath = self.output_dir / filename
        img.save(filepath)
        print(f"✅ Fallback-Bild gespeichert: {filepath}")
        return str(filepath)
    
    def _create_silent_audio(self, filename: str = "silence.wav") -> str:
        """Erstellt eine stille Audio-Datei mit FFmpeg"""
        print("🔇 Erstelle stille Audio...")
        
        filepath = self.output_dir / filename
        
        try:
            subprocess.run([
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=mono",
                "-t", str(self.duration),
                "-q:a", "9",
                "-acodec", "libmp3lame",
                str(filepath),
                "-y"
            ], capture_output=True, check=True, timeout=30)
            
            print(f"✅ Audio erstellt: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"⚠️  Fehler beim Audio erstellen: {e}")
            return None
    
    def _download_music(self, music_url: str) -> str:
        """Lädt Musik herunter"""
        print(f"🎵 Lade Musik herunter...")
        
        try:
            import requests
            
            response = requests.get(music_url, timeout=60)
            response.raise_for_status()
            
            filepath = self.output_dir / "background_music.mp3"
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Musik gespeichert: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"❌ Download fehlgeschlagen: {e}")
            return None
    
    def create_video(
        self,
        image_path: str,
        music_path: str = None,
        title: str = "",
        output_filename: str = "output.mp4"
    ) -> str:
        """
        Erstellt ein 10-Sekunden-Video mit FFmpeg.
        """
        print("\n🎬 Erstelle Video mit FFmpeg...")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Bild nicht gefunden: {image_path}")
        
        output_path = self.output_dir / output_filename
        
        try:
            # Grundkommando für Video-Erstellung
            cmd = [
                "ffmpeg",
                "-loop", "1",
                "-i", image_path,
                "-t", str(self.duration),
                "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2",
                "-r", str(self.fps),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast"
            ]
            
            # Füge Audio hinzu
            if music_path and os.path.exists(music_path):
                cmd.extend([
                    "-i", music_path,
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest"
                ])
            else:
                # Stille Audio
                cmd.extend([
                    "-f", "lavfi",
                    "-i", f"anullsrc=r=44100:cl=mono",
                    "-c:a", "aac",
                    "-t", str(self.duration)
                ])
            
            cmd.extend([str(output_path), "-y"])
            
            print(f"💾 Speichere Video: {output_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"❌ FFmpeg Fehler: {result.stderr}")
                raise Exception(f"Video creation failed: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise Exception("Video file not created")
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"✅ Video erfolgreich erstellt!")
            print(f"   Größe: {file_size:.2f} MB")
            print(f"   Pfad: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Fehler beim Video erstellen: {e}")
            raise
    
    def generate_complete_short(
        self,
        theme: str = "Jesus als König mit goldenem Licht",
        music_url: str = None,
        title: str = "Jesus - König der Könige #shorts",
        output_filename: str = "jesus_king_short.mp4"
    ) -> str:
        """
        Kompletter Workflow: Bild -> Audio -> Video
        """
        print("="*60)
        print("🎬 STARTE AI VIDEO GENERIERUNG")
        print("="*60)
        
        # Schritt 1: Bild generieren
        image_path = self.generate_image_with_dall_e(theme)
        
        # Schritt 2: Audio laden/erstellen
        audio_path = None
        if music_url:
            audio_path = self._download_music(music_url)
        else:
            audio_path = self._create_silent_audio()
        
        # Schritt 3: Video erstellen
        video_path = self.create_video(image_path, audio_path, title, output_filename)
        
        print("="*60)
        print("✅ VIDEO GENERATION ABGESCHLOSSEN")
        print(f"📁 Speicherort: {video_path}")
        print("="*60)
        
        return video_path


def main():
    """Beispiel: Generiere ein Video von Jesus als König"""
    
    print("\n" + "🎬 "*30)
    print("\nYOUTUBESHORTS - AI VIDEO GENERATOR")
    print("\n" + "🎬 "*30 + "\n")
    
    generator = AIVideoGenerator()
    
    # Prompt für DALL-E (oder Fallback-Bild)
    prompt = (
        "Jesus Christ as King, sitting on a majestic golden throne, "
        "wearing royal purple robes with a golden crown, divine golden light radiating, "
        "heavenly atmosphere, 8k, ultra high quality, professional art, "
        "vertical portrait format 9:16"
    )
    
    # Generiere komplettes Video
    try:
        video_path = generator.generate_complete_short(
            theme=prompt,
            music_url=None,  # Verwende stille Audio
            title="👑 JESUS\nKÖNIG DER KÖNIGE",
            output_filename="jesus_king_10sec.mp4"
        )
        
        print(f"\n✅ Video erfolgreich generiert!")
        print(f"📹 Location: {video_path}")
        print(f"💾 Größe: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
        print(f"\n💡 Nächster Schritt: Upload mit upload_shorts.py")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
