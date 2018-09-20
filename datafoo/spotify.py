import json
import requests
import base64
from datetime import date
from flask import request

#  Client Keys
CLIENT_ID = "e7c5c33ec8a0430c8c2fe1b40087774c"
CLIENT_SECRET = "d1aaa3b074ee4aef9abf3301d36281e6"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

def getRecommendationThroughTracks(authorization_header, listOfSeedTracks, listOfAudioFeature):
    # example; https://api.spotify.com/v1/recommendations?limit=10&market=ES&seed_tracks=1BDY39wDjT45KwlPADHap3%2C2wz8v9hjCcnp3m7kbZZMTG&target_acousticness=3
    limit = 20
    market = "ES"
    recommend_base_endpoint = "{}/recommendations?limit={}&market={}".format(SPOTIFY_API_URL,limit,market)
    appended_list_seed = ','.join(listOfSeedTracks)
    seed_api_endpoint = "{}&seed_tracks={}&".format(recommend_base_endpoint,appended_list_seed)
    raw_audio_feature = '&'.join("%s=%s" % (key, val) for (key, val) in listOfAudioFeature)
    audio_feature_api_endpoint = "{}{}".format(seed_api_endpoint,raw_audio_feature)

    recommend_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    recommend_data = json.loads(recommend_response.text)

    return recommend_data

def getProfileData(authorization_header):
    # Getting the information
    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    return profile_data

def getTopTrack(authorization_header):
    # GET https://api.spotify.com/v1/me/top/{type}
    # https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=50
    time_range = 'short_term'
    limit = 50
    type = 'tracks'

    top_api_endpoint = "{}/me/top/{}".format(SPOTIFY_API_URL,type)
    specific_top_api_endpoint = "{}?time_range={}&limit={}".format(top_api_endpoint,time_range,limit)

    top_track_response = requests.get(specific_top_api_endpoint, headers=authorization_header)
    top_track_data = json.loads(top_track_response.text)

    return top_track_data

def getPlaylistData(authorization_header, profile_data):
    # # Get user playlist data
    # Get user playlist data
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    return playlist_data

def getTrackFromPlaylistData(authorization_header, playlist_data):
    # Get user Track from data for Playlist
    tracks_api_endpoint = "{}/tracks".format(playlist_data["href"])
    tracks_response = requests.get(tracks_api_endpoint, headers=authorization_header)
    track_data = json.loads(tracks_response.text)

    return track_data

def postBlankPlaylist(authorization_header, weather, user_id):
    # create a blank playlist to store
    d = date.today()
    user_date = d.strftime("%m/%d/%y")
    title = '{} {}'.format(d,weather)

    playlist_post = {'name': title, 'public': 'true', 'collaborative': 'false', 'description': 'Created at {} for {} weather. Made via SpotifyWeather.'.format(user_date,weather)}
    post_playlist_api_endpoint = '{}/users/{}/playlists'.format(SPOTIFY_API_URL,user_id)
    print("post_playlist_api_endpoint",post_playlist_api_endpoint)

    post_playlist_api_response = requests.post(post_playlist_api_endpoint, headers=authorization_header, data=json.dumps(playlist_post))

    print("post_playlist_api_response",post_playlist_api_response)

    # ALSO GET THE PLAYLIST ID#
    post_playlist_api_json = post_playlist_api_response.json()
    playlist_id = post_playlist_api_json.get('id')

    return post_playlist_api_response, playlist_id

def postTrackToPlaylist(authorization_header, track_id_list, playlist_id):
    # https://api.spotify.com/v1/playlists/0R7m3oPH6gdaCeEdS6z0sq/tracks?uris=
    edited_track_list = ['spotify:track:{}'.format(track_id) for track_id in track_id_list]
    print("edited_track_list",edited_track_list)
    post_track_api_endpoint = '{}/playlists/{}/tracks?uris={}'.format(SPOTIFY_API_URL,playlist_id,','.join(edited_track_list))
    print("post_track_api_endpoint",post_track_api_endpoint)
    post_track_api_response = requests.post(post_track_api_endpoint, headers=authorization_header)

    return post_track_api_response

def getAudioFeatureFromTrack(authorization_header, id):
    # Get audio feature from track
    # https://api.spotify.com/v1/audio-features/{id}
    audio_feature_api_endpoint = "{}/{}/audio-features/{}".format(SPOTIFY_API_BASE_URL, API_VERSION, id)
    audio_feature_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    audio_feature_data = json.loads(audio_feature_response.text)

    return audio_feature_data

def getPostRequest():
    auth_token = str(request.args["code"])
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    val = "{}:{}".format(CLIENT_ID, CLIENT_SECRET)
    base64encodedUtf8 = base64.b64encode(bytes(val, encoding='utf-8'))
    base64encoded = base64encodedUtf8.decode("utf-8")
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    return post_request

def getAuthorizationHeader():
    post_request = getPostRequest()

    response_data = json.loads(post_request.text)
    access_token = response_data.get('access_token')
    refresh_token = response_data.get('refresh_token')
    token_type = response_data.get('token_type')
    expires_in = response_data.get('expires_in')

    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    return authorization_header