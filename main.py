from bs4 import BeautifulSoup
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint

# date = input("What date would you like to travel to? (yyyy-mm-dd format): ")
date = "yyyy-mm-dd"  # if you want to have a set date
year = date.split("-")[0]

URL = f"https://www.billboard.com/charts/hot-100/{date}"  # can be changed to fit any other site with a list of songs

response = requests.get(URL)
webpage_html = response.text
soup = BeautifulSoup(webpage_html, "html.parser")

song_titles = soup.find_all(name="span", class_="chart-element__information__song text--truncate color--primary")
song_titles = [song.getText() for song in song_titles]
# song_titles = [(song.split("(")[0]).rstrip() for song in song_titles]
# the line above is in case you wanted to make the songs with parenthesis' easier to find
artist_titles = soup.find_all(name="span", class_="chart-element__information__artist text--truncate color--secondary")
artist_titles = [artist.getText() for artist in artist_titles]
songs_and_albums = dict(zip(song_titles, artist_titles))

# Spotify
CLIENT_ID = "YOUR CLIENT ID"
CLIENT_SECRET = "YOUR CLIENT SECRET CODE"
redirect_url = "http://example.com"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=f"{CLIENT_ID}",
        client_secret=f"{CLIENT_SECRET}",
        redirect_uri=f"{redirect_url}",
        scope="playlist-modify-private",
        show_dialog=True,
        cache_path="token.txt"
    )
)

user_id = sp.current_user()["id"]

song_and_uris = []
song_uris = []

for song, artist in songs_and_albums.items():
    result = sp.search(q=f"track:{song} artist:{artist} year:{year}", type="track")
    try:
        uri = result["tracks"]["items"][0]["uri"]
        song_and_uris.append({song: uri})
        song_uris.append(uri)
    except IndexError:
        try:  # in case the song was released the year before
            result = sp.search(q=f"track:{song} year:{str(int(year) - 1)}", type="track")
            uri = result["tracks"]["items"][0]["uri"]
            song_and_uris.append({song: uri})
            song_uris.append(uri)
        except IndexError:
            try:  # in case the song was released via album the following year
                result = sp.search(q=f"track:{song} year:{str(int(year) + 1)}", type="track")
                uri = result["tracks"]["items"][0]["uri"]
                song_and_uris.append({song: uri})
                song_uris.append(uri)
            except IndexError:
                pass
            pass
        # print(f"{song} doesn't exist in Spotify. Skipped.")
        pass

# pprint(song_and_uris)  # if you want to see the songs and their uri

playlist = sp.user_playlist_create(
    user=user_id,
    name=(date + " Billboard 100"),  # can be named whatever you want
    public=False,
    collaborative=False,
    description=f"A playlist of the Top 100 Billboard songs on the week of {date}"  # edit accordingly
)

add_tracks = sp.playlist_add_items(playlist_id=playlist["id"], items=song_uris, position=None)
