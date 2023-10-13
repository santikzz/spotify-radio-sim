seimport spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import os
import random
import time
import termux

class Radio:

    MAX_PLAYTIME = 130 # seconds
    ADS_PLAYLIST = "spotify:playlist:45XIyADnYlW5xnB5s1NzZw" # local files ads playlist

    def __init__(self) -> None:
          
        scopes = "user-read-playback-state, user-modify-playback-state, user-read-currently-playing, playlist-read-private, playlist-read-collaborative, user-read-playback-position, user-top-read, user-read-recently-played, user-library-read"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="19ba756cd5e9417b852cad85658ddd67", client_secret="846aa3d6ecc64085bfbd59ea52f109a0", redirect_uri="http://localhost:8080", scope = scopes))

        self.already_played_ads = []
        self.song_counter = 0
        self.songs_per_ad = 1 #random.randint(2,3)
        self.device = self.select_device()
        self.songs = self.load_songs()
        self.ads = self.load_ads(self.ADS_PLAYLIST)

    def crossfade(self, steps, interval, start, end):
        step_diff = (end - start) / steps
        volume = start
        for _ in range(1, steps+1):
            volume += step_diff
            self.set_volume(volume)
            time.sleep(interval)
        
    def async_crossfade(self, steps, interval, start, end):
        threading.Thread(target=self.crossfade, args=[steps, interval, start, end]).start()

    def set_volume(self, volume):
        if self.device["type"] == "Smartphone":  
            #os.system(f"termux-volume music {int(volume)}") 
            termux.volume("music", int(volume))
        elif self.device["type"] == "Computer" or self.device["supports_volume"]:
            self.sp.volume(int(volume), self.device["id"])
        else:
            return

    def select_device(self):
        devices = self.sp.devices()
        if len(devices) == 0:
            print("\n[-] No devices found")
            return None
        idx = 1
        for device in devices["devices"]:
            print(f"[{idx}]: {device['name']} ({device['type']})")
            idx += 1
        opt = int(input("\n> Select device: "))-1
        return devices["devices"][opt]

    def select_playlist(self):
        playlists = self.sp.current_user_playlists()
        idx = 1
        print("### Select a playlist ###")
        for playlist in playlists["items"]:
            print(f"[{idx}]: {playlist['name']}")
            idx += 1
        opt = int(input("\n> Select playlist: "))-1
        return playlists["items"][opt]["id"]

    def get_playlist_random_songs(self, playlist_id, limit = None):
        result = []
        songs = self.sp.playlist(playlist_id=playlist_id, fields="name, id, tracks(total), tracks(items(track(id, name, duration_ms)))")
        for song in songs["tracks"]["items"]:
            result.append(song["track"])   
        random.shuffle(result)
        if ((limit >= len(result)) or (limit == None)):
            return result
        else:
            return result[:limit]

    def get_recent_played_songs(self):
        recent = []
        songs = self.sp.current_user_recently_played(limit=20)
        for song in songs["items"]:
            recent.append(song["id"])
        return recent
    
    def load_songs(self):
        playlist = self.select_playlist()
        songs = self.get_playlist_random_songs(playlist, 20)
        choice = input("> Load recently played songs? (y/n): ")
        if choice.lower == "y":
            recent = self.get_recent_played_songs()
            songs = songs + recent
            random.shuffle(songs)
        return songs

    def load_ads(self, playlist_id):
        ads = []
        songs = self.sp.playlist(playlist_id=playlist_id, fields="tracks(total), tracks(items(track(id, name, duration_ms)))")
        idx = 0
        for song in songs["tracks"]["items"]:
            ads.append({"id":idx, "duration_ms": song["track"]["duration_ms"], "name": song["track"]["name"]})
            idx += 1
        return ads

    def get_next_ad_index(self):
        total = len(self.ads)
        if len(self.already_played_ads) >= total:
            self.already_played_ads.clear()
        index = random.randint(0, total-1)
        while index in self.already_played_ads:
            index = random.randint(0, total-1)
        self.already_played_ads.append(index)
        return index
    
    def play_ad(self):
        index = self.get_next_ad_index()
        self.set_volume(33)
        self.async_crossfade(5, 0.5, 33, 100)
        print(f"[+] Playing ad \"{self.ads[index]['name']}\"")
        self.sp.start_playback(device_id=self.device["id"], context_uri=self.ADS_PLAYLIST, offset={"position": index })
        self.song_counter = 0
        self.songs_per_ad = random.randint(2, 3)
        time.sleep( (self.ads[index]["duration_ms"]/1000) - 4)

    def play_song(self, song):

        self.set_volume(33)
        self.async_crossfade(5, 0.5, 33, 100)
        self.sp.start_playback(device_id=self.device["id"], uris=[f"spotify:track:{song['id']}"] )
        
        duration = song["duration_ms"] / 1000

        if duration > self.MAX_PLAYTIME:
            print(f"[+] Playing \"{song['name']}\" - ({round(duration/60,2)} min) skiping on {self.MAX_PLAYTIME}s ...")
            time.sleep(self.MAX_PLAYTIME)
        
        else:

            print(f"[+] Playing \"{song['name']}\" - ({round(duration/60,2)} min)")
            time.sleep(duration - 7)

        self.song_counter += 1
        self.crossfade(12, 0.5, 100, 33)

    def display_info(self):
        print(f"\n[+] Songs loaded: ({len(self.songs)}) / Ads loaded: ({len(self.ads)}) ")