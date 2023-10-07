import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import json
import time
import random
import threading

scopes = "user-read-playback-state, user-modify-playback-state, user-read-currently-playing, playlist-read-private, playlist-read-collaborative, user-read-playback-position, user-top-read, user-read-recently-played, user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="", client_secret="", redirect_uri="http://localhost:8080", scope = scopes))

global already_played_ads
global volume_support

volume_support = True
already_played_ads = []

# sp.add_to_queue("6NDoBIaqTHdcudaR8RDJNw", device_id=devices["devices"][int(d)]['id'])
# playlists = sp.current_user_playlists(limit=50, offset=0) # GET PLAYLISTS
# playlists = sp.category_playlists(category_id=, country='AR', limit=20, offset=0) # https://spotipy.readthedocs.io/en/2.22.1/?highlight=get%20playlists#spotipy.client.Spotify.category_playlists
#playlists = sp.featured_playlists(locale='es_AR', country='AR', timestamp='2023-10-07T10:40:00', limit=20, offset=0)
#print(json.dumps(playlists))
# a = sp.current_user_playing_track()
# print(a)

def thCrossfadeOut(steps=5, min_vol=33, interval=1):
    threading.Thread(target=crossfadeOut, args=[steps, min_vol, interval]).start()

def crossfadeOut(steps, min_vol, interval):
    global volume_support
    if not volume_support:
        return
    
    step = (100 - min_vol) / steps
    for i in range(1, steps+1):
        vol = int(100 - step*i)
        sp.volume(vol)
        time.sleep(interval)

def thCrossfadeIn(steps=5, min_vol=33, interval=1):
    threading.Thread(target=crossfadeIn, args=[steps, min_vol, interval]).start()

def crossfadeIn(steps, min_vol, interval):
    global volume_support
    if not volume_support:
        return
    
    step = (100 - min_vol) / steps
    for i in range(1, steps+1):
        vol = int(min_vol + step*i)
        vol = min(vol, 100)
        sp.volume(vol)
        time.sleep(interval)

def set_volume(volume):
    global volume_support
    if not volume_support:
        return
    sp.volume(volume)

def select_device():
    devices = sp.devices()    
    if len(devices) == 0:
        print("[-] No devices found")
        return
    d_id = 0
    for device in devices["devices"]:
        print(f"[{d_id}]: {device['name']}")
        d_id += 1
    d_index = int(input("Select device: "))
    volume_support = devices["devices"][d_index]["supports_volume"]
    device = devices["devices"][d_index]["id"]
    return device

def select_playlist():
    playlists = sp.current_user_playlists()
    p_id = 0
    for playlist in playlists["items"]:
        print(f"[{p_id}]: {playlist['name']}")
        p_id += 1
    p = int(input("Select playlist: "))
    return playlists["items"][p]["id"]

def get_recent_played_songs():
    recent = []
    songs = sp.current_user_recently_played(limit=15)
    for song in songs["items"]:
        recent.append(song["id"])
    return recent

def load_songs():

    pl_selected = select_playlist()                             # SELECT PLAYLIST
    songs = get_playlist_random_songs(pl_selected, 15)          # GET SONGS FROM PLAYLIST

    choice = input("Load recently played songs? (y/n): ")
    
    if choice.lower == "y":
        recent = get_recent_played_songs()
        songs.append(recent)
        random.shuffle(songs)

    return songs

def get_playlist_random_songs(playlist_id, limit = None):

    songs_id = []
    pl_data = sp.playlist(playlist_id=playlist_id, fields="name, id, tracks(total), tracks(items(track(id, name, duration_ms)))")
    
    for song in pl_data["tracks"]["items"]:
        songs_id.append(song["track"])   

    random.shuffle(songs_id)

    if ( (limit >= len(songs_id)) or (limit == None) ):
        return songs_id
    
    else:
        return songs_id[:limit]


def load_ads(playlist_id):
    ads = []
    songs = sp.playlist(playlist_id=playlist_id, fields="tracks(total), tracks(items(track(id, name, duration_ms)))")
    _id = 0
    for song in songs["tracks"]["items"]:
        ads.append({"id":_id, "duration_ms": song["track"]["duration_ms"], "name": song["track"]["name"]})
        _id += 1
    return ads

def get_next_ad(fake_ads):
    global already_played_ads
    total = len(fake_ads)
    if len(already_played_ads) >= total:
        already_played_ads.clear()
    index = random.randint(0, total-1)
    while index in already_played_ads:
        index = random.randint(0, total-1)
    already_played_ads.append(index)
    return index

if __name__ == '__main__':

    MAX_PLAY_TIME = 120 # 120 seconds -> 2 mins
    MAX_PLAY_TIME_PERC = 0.60 # 60% of the song
    SONGS_PER_AD = 2
    MIN_VOL = 33

    pl_fake_ads = "spotify:playlist:45XIyADnYlW5xnB5s1NzZw"

    # DEVICE SELECTION
    device = select_device()
    
    # INSTANCE VARIABLES
    song_counter = 0
    fake_ads = load_ads(pl_fake_ads)  # LOAD FAKE ADS
    songs = load_songs()

    print("\n#################################################")
    print("#                                               #")
    print("#   Spotify radio simulator v1.0 - by santikz   #")
    print("#                                               #")
    print("#################################################\n")
    print(f"[+] {len(fake_ads)} ads loded")
    print(f"[+] {len(songs)} songs loaded\n")

    set_volume(MIN_VOL)
    for song in songs:

        if song_counter >= SONGS_PER_AD:
            
            # Play ad & reset counter
            _ad_index = get_next_ad(fake_ads)

            print(f"[+] Playing ad \"{fake_ads[_ad_index]['name']}\" ({round(fake_ads[_ad_index]['duration_ms']/1000,2)} s) - [{len(already_played_ads)} of {len(fake_ads)} ads played]")
            sp.start_playback(device_id=device, context_uri=pl_fake_ads, offset={"position": _ad_index })
            thCrossfadeIn(3, MIN_VOL, 0.5)
            
            song_counter = 0
            time.sleep(fake_ads[_ad_index]['duration_ms']/1000 - 6)
            crossfadeOut(3, MIN_VOL, 0.5)

        else:
            
            # Play song/skip to next
            thCrossfadeIn(5, MIN_VOL, 0.5)
            sp.start_playback(device_id=device, uris=[f"spotify:track:{song['id']}"] )
            
            duration = song["duration_ms"] / 1000
            # if the song duration exceeds the minium duration
            if duration > MAX_PLAY_TIME:
                
                # if the % duration of the song is less than the minium duration, wait the minium
                if duration*MAX_PLAY_TIME_PERC < MAX_PLAY_TIME:
                    sleep_time = MAX_PLAY_TIME
                else:
                    sleep_time = duration*MAX_PLAY_TIME_PERC

                # sleep_time = MAX_PLAY_TIME

                print(f"[+] Playing \"{song['name']}\" - (>{round(duration/60,2)} min) skiping on {round(sleep_time,2)}s ...")
                time.sleep(sleep_time - 1)

            # play the whole song
            else:
                print(f"[+] Playing \"{song['name']}\" - ({round(duration/60,2)} min)")
                time.sleep(duration - 1)
            
            print(f"[+] {SONGS_PER_AD - song_counter - 1} songs left to ad ({song_counter+1}/{SONGS_PER_AD})")
            song_counter +=1
            crossfadeOut(6, MIN_VOL, 0.5)
