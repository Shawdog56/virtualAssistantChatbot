import os
from pathlib import Path

class AudioFileLister:
    def __init__(self, extensions=["wav","mp3"]):
        self.extensions = extensions
        self.init()

    def init(self):     
        if not os.path.exists("utils/"):
            os.makedirs("utils/")       
        if not os.path.exists("utils/audio_files.txt"):
            print("Generating audio file list...")
            self.create_audio_file(output_file="utils/audio_files.txt")

    def create_audio_file(self, output_file="utils/audio_files.txt"):
        try:
            audio_files = self.list_audio_files()
            with open(output_file,"w") as file:
                for audio_file in audio_files:
                    if audio_file.find("command") == -1 and audio_file.find("test-") == -1 and audio_file.find("/Trash/") == -1:
                        file.write(f"{audio_file}\n")
        except Exception as e:
            print(f"Error while trying to list audio files: {e}")


    def list_audio_files(self):
        try:
            # Convert extensions to a set for much faster "if x in y" checks
            # Also ensure they start with a dot (e.g., '.mp3') to match Path.suffix
            valid_extensions = {f".{ext.lstrip('.')}" for ext in self.extensions}
            
            home = Path.home()
            # rglob('*') performs a SINGLE recursive walk of the directory tree
            audio_files = [
                str(f) for f in home.rglob('*') 
                if f.is_file() and f.suffix.lower() in valid_extensions
            ]
            
            return audio_files
        except Exception as e:
            raise Exception(f"An error occurred while listing files: {e}")
            