from GUI import GUI
import tkinter as tk
from tkinter import simpledialog
import os
import json
import requests
from ytmusicapi import YTMusic
from ytmusicapi.exceptions import YTMusicServerError
from ytmusicapi.auth.oauth import OAuthCredentials, RefreshingToken
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import urllib.parse

SPOTIFY_CONFIG = 'spotify_config.json'
YTMUSIC_CONFIG = 'ytmusic_config.json'

def load_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return json.load(file)
    return {}
    
def save_config(config_file, config):
    with open(config_file, 'w') as file:
        json.dump(config, file)

def setup_ytmusic():
    config = load_config(YTMUSIC_CONFIG)
    headers = config.get('headers')

    if not headers:
        headers = authenticate_ytmusic()
        if headers:
            config['headers'] = headers
            save_config(YTMUSIC_CONFIG, config)
        else:
            print("YouTube Music authentication failed")
            return None

    ytmusic = YTMusic(headers)
    return ytmusic

def authenticate_ytmusic():
    headers_file = 'oauth.json'
    session = requests.Session()
    oauth = OAuthCredentials(session=session)

    code = oauth.get_code()

    # Create a Tkinter window for user interaction
    auth_window = tk.Tk()
    auth_window.title("YouTube Music Authentication")

    verification_url_with_code = f"{code['verification_url']}?user_code={code['user_code']}"

    # Display the verification URL and user code
    tk.Label(auth_window, text="Please visit the following URL to complete the authentication:").pack()

    def open_url(event):
        webbrowser.open_new(verification_url_with_code)

    url_label = tk.Label(auth_window, text=verification_url_with_code, fg="blue", cursor="hand2")
    url_label.pack()
    url_label.bind("<Button-1>", open_url)

    def on_confirm():
        # Wait for the user to complete the flow
        raw_token = oauth.token_from_code(code["device_code"])
        # Check for errors in the raw_token
        if 'error' in raw_token:
            raise Exception(f"Error during token retrieval: {raw_token['error']}")

        ref_token = RefreshingToken(credentials=oauth, **raw_token)
        # Construct the headers manually
        headers = {
            "Authorization": f"Bearer {ref_token.access_token}"
        }

        # Save the headers to a file
        with open(headers_file, 'w') as file:
            json.dump(headers, file)
        # Close the Tkinter window
        auth_window.destroy()
        auth_window.quit()

    # Button to confirm the completion of authentication
    tk.Button(auth_window, text="Click here once you have completed the authentication", command=on_confirm).pack()

    # Start the Tkinter main loop
    auth_window.mainloop()
    print("Authentication successful")
    with open(headers_file, 'r') as file:
        headers = json.load(file)
    return headers

def ensure_ytmusic_auth(ytmusic):
    try:
        # Example API call to check authentication
        ytmusic.get_library_playlists(limit=1)
    except YTMusicServerError as e:
        if 'invalid authentication credentials' in str(e):
            print("YouTube Music authentication expired. Reauthenticating...")
            headers = authenticate_ytmusic()
            if headers:
                config = load_config(YTMUSIC_CONFIG)
                config['headers'] = headers
                save_config(YTMUSIC_CONFIG, config)
                ytmusic = YTMusic(headers)
            else:
                print("Reauthentication failed")
                return None
    return ytmusic


def setup_spotify(scope):

    config = load_config(SPOTIFY_CONFIG)

    client_id = config.get('SPOTIPY_CLIENT_ID')
    client_secret = config.get('SPOTIPY_CLIENT_SECRET')
    redirect_url = config.get('SPOTIPY_REDIRECT_URI')
    os.environ['SPOTIPY_REDIRECT_URI'] = 'https://localhost:8888/callback'
    if not client_id or not client_secret:
        root = tk.Tk()
        root.withdraw()

        client_id = simpledialog.askstring("Spotify Authentication", "Enter your Spotify client ID:")
        client_secret = simpledialog.askstring("Spotify Authentication", "Enter your Spotify client secret:")


        if client_id and client_secret:
            print("Spotify authentication successful")
            config['SPOTIPY_CLIENT_ID'] = client_id
            config['SPOTIPY_CLIENT_SECRET'] = client_secret
            save_config(SPOTIFY_CONFIG, config)
            os.environ['SPOTIPY_CLIENT_ID'] = client_id
            os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
        else:
            print("Spotify authentication failed")
            return
    else:
        os.environ['SPOTIPY_CLIENT_ID'] = client_id
        os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
    auth_manager = SpotifyOAuth(scope=scope, cache_path=".cache-spotify")
    
    # Check for a cached token
    token_info = auth_manager.get_cached_token()
    
    if not token_info:
        # Open the auth URL in the default web browser
        auth_url = auth_manager.get_authorize_url()
        webbrowser.open(auth_url)
        
        # Create a popup to get the redirect URL from the user
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        redirect_url = simpledialog.askstring("Spotify Authentication", "Enter the URL you were redirected to:")
        root.destroy()
        
        # Parse the redirect URL to get the authorization code
        code = auth_manager.parse_response_code(redirect_url)
        token_info = auth_manager.get_access_token(code)
    
    return spotipy.Spotify(auth=token_info['access_token'])


def convert_songs(source, destination, id, songs):
    if id == "Youtube Music":
        ytmusic = source
        spotify = destination
        for song in songs:
            result = spotify.search("track:" + song['title'] + " artist:" + song['artists'][0]['name'] + " album:" + song['album']['name'], limit=1)
            for i in result["tracks"]["items"]:
                spotify.current_user_saved_tracks_add(tracks=[i["uri"]])
        return
    else:
        spotify = source
        ytmusic = destination
        for song in songs:
            result = ytmusic.search(
                query=song['track']['name'] + " " + song['track']['artists'][0]['name'] + " " + song['track']['album']['name'], 
                filter='songs', 
                limit=1)
            ytmusic.rate_song(result[0]['videoId'],'LIKE')
        return

def convert_playlists(source, destination, id, playlists):
    if id == "Youtube Music":
        ytmusic = source
        spotify = destination
        for youtube_playlist in playlists:
            tracks = ytmusic.get_playlist(youtube_playlist['playlistId'],limit=None)
            new_playlist = []
            spotify.user_playlist_create(spotify.me()['id'], name=youtube_playlist['title'])
             #get the id of the newly created playlist
            spotify_playlists = spotify.current_user_playlists()
            playlist_id = None
            for spotify_playlist in spotify_playlists['items']:
                if spotify_playlist['name'] == youtube_playlist['title']:
                    playlist_id = spotify_playlist['id']
                    break
            for track in tracks['tracks']:
                result = spotify.search("track:" + track['title'] + " artist:" + track['artists'][0]['name'] + " album:" + track['album']['name'], limit=1, type='track')
                for i in result["tracks"]["items"]:
                    new_playlist.append(i["uri"])
            spotify.playlist_add_items(playlist_id, new_playlist)
        return
    else:
        spotify = source
        ytmusic = destination
        for spotify_playlist in playlists:
            playlist_id = spotify_playlist['id']
            tracks = spotify.playlist_tracks(playlist_id)
            new_playlist = []
            for track in tracks['items']:
                track = track['track']
                title = track['name']
                artist = track['artists'][0]['name']
                album = track['album']['name']
                result = ytmusic.search(query=title + " " + artist + " " + album, filter='songs', limit= 1) #refine search query getting wrong results
                #add the song ids to the new playlist
                #print(result[0]['title'])
                new_playlist.append(result[0]['videoId'])
            ytmusic.create_playlist(title= spotify_playlist['name'], description= "",video_ids= new_playlist)
        return

def convert_albums(source, destination, id, albums):
    if id == "Youtube Music":
        ytmusic = source
        spotify = destination
        for album in albums:
            result = spotify.search("album:" + album['title'] + " artist:" + album['artists'][0]['name'], limit=1,type='album')
            for i in result["albums"]["items"]:
                spotify.current_user_saved_albums_add(albums=[i["uri"]])
        return
    else:           #Broken b/c audioPlaylistId returns none... might not work at all
        ytmusic = destination
        spotify = source
        for album in albums:
            print(album['album']['name'])
            result = ytmusic.search(
                query=album['album']['name'] + " " + ', '.join([artist['name'] for artist in album['album']['artists']]), 
                filter='albums', 
                limit=1)
            browseId = result[0]['browseId']
            album = ytmusic.get_album(browseId)
            print(album.get('audioPlaylistId'))
            #print(album['playlistId'])
            ytmusic.rate_playlist(result[0]['browseId'],'LIKE')
        return

def convert_artists(source, destination, id, artists):
    if id == "Youtube Music":
        ytmusic = source
        spotify = destination
        for artist in artists:
            result = spotify.search("artist:" + artist['artist'], limit=1,type='artist')
            #print(result['id'])
            for i in result["artists"]["items"]:
                spotify.user_follow_artists(ids=[i["id"]])     #check if works
        return
    else:
        ytmusic = destination
        spotify = source
        for artist in artists:
            result = ytmusic.search(query=artist['name'], filter='artists', limit=1)
            artist = ytmusic.get_artist(result[0]['browseId'])
            ytmusic.subscribe_artists(artist['channelId'])
        return

def construct_spotify_query(track_title, artist, album):
    base_url = "https://api.spotify.com/v1/search"
    #query = f"albumn:{album} artist:{artist} track:{track_title}"
    #query = f"track:{track_title} artist:{artist}"
    query = f"artist:{artist} track:{track_title}"
    encoded_query = urllib.parse.quote(query)
    full_url = f"{base_url}?q={encoded_query}&type=track"
    return full_url


#Get tracks in Ytmusic playlist: ytmusic.get_playlist(items[0]['playlistId'],limit=None)
def convert(ytmusic, spotify, source, destination, media_type, items):
    print("Converting...")
    #print(source, destination, media_type, items)

    #spotify query construction

    #assuming youtube source
    print(source, destination, media_type)
    if source == "Youtube Music" and destination == "Spotify":
        if media_type == "song":
            convert_songs(ytmusic, spotify, "Youtube Music", items)
        elif media_type == "playlist":
            convert_playlists(ytmusic, spotify, "Youtube Music", items)
        elif media_type == "album":
            convert_albums(ytmusic, spotify, "Youtube Music", items)
        elif media_type == "artist":
            convert_artists(ytmusic, spotify, "Youtube Music", items)
    else:
        if media_type == "song":
            convert_songs(spotify, ytmusic, "Spotify", items)
        elif media_type == "playlist":
            convert_playlists(spotify, ytmusic, "Spotify", items)
        elif media_type == "album":
            convert_albums(spotify, ytmusic, "Spotify", items)
        elif media_type == "artist":
            convert_artists(spotify, ytmusic, "Spotify", items)            #clean up! condense to one line each or something
    print("Conversion complete")

def main():

    root = tk.Tk()
    GUI(root, setup_ytmusic, setup_spotify, ensure_ytmusic_auth, convert)
    
    root.mainloop()

if __name__ == "__main__":
    main()