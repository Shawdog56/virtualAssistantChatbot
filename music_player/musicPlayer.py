import re
import os
import time
import pygame
import threading
import unicodedata

from searcher.kmpSearcher import KMPSearcher


class Player:
    def __init__(self, list_of_songs):
        self.play_event = threading.Event()
        self.stop_event = threading.Event()
        self.thread = None
        self.current_file = None
        self.list_of_songs = list_of_songs

    def normalize(self,text):
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def filter_song(self, command: str) -> str:
        print(command)
        kmp_search = KMPSearcher()
        command = self.normalize(command.lower())
        command = "".join(list(re.findall(r'[a-z]+',command)))

        for song in self.list_of_songs:
            if kmp_search.kmp_search(text="".join(list(re.findall(r'[a-z]+',song.lower().split("/")[-1]))),pattern=command):
                return song

        return "Canción no encontrada en la lista."
    
    def _player_loop(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.current_file)
        pygame.mixer.music.play()
        self.play_event.set()  # start in playing state

        while not self.stop_event.is_set():
            if not self.play_event.is_set():
                pygame.mixer.music.pause()
                self.play_event.wait()  # block until resumed
                pygame.mixer.music.unpause()

            if not pygame.mixer.music.get_busy():
                break

            time.sleep(0.1)

        pygame.mixer.music.stop()

    def play(self, song):
        assert self.list_of_songs != None, "No tienes una lista de canciones"
        filename = self.filter_song(song)
        assert os.path.exists(filename), "El archivo no existe"
        if self.thread and self.thread.is_alive():
            self.stop()

        self.current_file = filename
        self.stop_event.clear()
        self.play_event.set()

        self.thread = threading.Thread(target=self._player_loop, daemon=True)
        self.thread.start()

    def pause(self):
        self.play_event.clear()

    def resume(self):
        self.play_event.set()

    def stop(self):
        self.stop_event.set()
        self.play_event.set()
        if self.thread:
            self.thread.join()

    def setVolume(self, volume: bool):
        if volume:
            pygame.mixer.music.set_volume(min(pygame.mixer.music.get_volume()+0.1,1.0))
        else:
            pygame.mixer.music.set_volume(max(pygame.mixer.music.get_volume()-0.1,0.0))
