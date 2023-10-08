from radio import Radio


if __name__ == '__main__':


    print("\n#################################################")
    print("#                                               #")
    print("#   Spotify radio simulator v1.0 - by santikz   #")
    print("#                                               #")
    print("#################################################\n")
    
    radio = Radio()
    radio.display_info()

    for song in radio.songs:

        if radio.song_counter >= radio.songs_per_ad:
            radio.play_ad()

        else:
            radio.play_song(song)
            
