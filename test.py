import subprocess
import yt_dlp
from pathlib import Path
REPO_DIR = Path(__file__).parent
whisper = REPO_DIR / "build/bin/Release/whisper-cli.exe"

url = "https://www.youtube.com/watch?v=kKJHT6VlWro&t=125s"
output_dir = REPO_DIR / "downloads"
output_dir.mkdir(exist_ok= True)

#yt_dlp.YoutubeDL({}).download([url])
ydl_opts = {
    'format': 'bestaudio',
    'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3'
    }]
}
yt_dlp.YoutubeDL(ydl_opts).download([url])

audio_file = list(output_dir.glob("*.mp3"))[0]

proc = subprocess.Popen(
    [str(whisper), "-f", str(audio_file), "-osrt"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

for line in proc.stdout:
    print(">>", line.strip())