import json
from flask import Flask, request, redirect, g, render_template
import requests
import base64
import urllib
import urllib.parse
from datetime import date

app = Flask(__name__)

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
SCOPE1 = 'streaming user-read-birthdate user-read-private user-modify-playback-state'
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# Weather App Id
WEATHER_APP_ID = "decca2633db37406aa20f5fba1267d59"

# OpenWeatherMap URLS
WEATHER_API_BASE_URL = "http://api.openweathermap.org/data"
WEATHER_API_VERSION = "2.5"
WEATHER_API_URL = "{}/{}/weather".format(WEATHER_API_BASE_URL, WEATHER_API_VERSION)

# Weather Data
global_weather = 000
weather_id = 0
weather_word = "clear sky"

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.route("/")
def weather():
    return render_template('weather.html')

@app.route('/', methods=['POST'])
def weather_post():
    global weather_id
    global weather_word

    text = request.form['text']

    raw_weather_data_from_zipcode = getWeatherFromZip(text);
    loose_weather_data = raw_weather_data_from_zipcode.get("weather")[0]
    global_weather = loose_weather_data.get("id")
    weather_word = loose_weather_data.get("main")


    # print("Current Weather:", loose_weather_data.get("main"), global_weather)
        # Sunny Day : 800
        # Windy, Cloudy Days: 8xx NOT 800
        # Rainy Days: 2xx Thunderstorm 3xx Drizzle 5xx Rain
        # Snowy Days: 6xx Snow
    global_weather_parse = global_weather // 100
    if global_weather == 800:
        weather_id = 0
    elif global_weather_parse == 8:
        weather_id = 1
    elif global_weather_parse == 2 or global_weather_parse == 3 or  global_weather_parse == 5:
        weather_id = 2
    elif global_weather_parse == 6:
        weather_id = 3

    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key,val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    global weather_id
    global weather_word

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

    response_data = json.loads(post_request.text)
    access_token = response_data.get('access_token')
    refresh_token = response_data.get('refresh_token')
    token_type = response_data.get('token_type')
    expires_in = response_data.get('expires_in')

    authorization_header = {"Authorization":"Bearer {}".format(access_token)}
    profile_data = getProfileData(authorization_header)
    playlist_data_list = getPlaylistData(authorization_header, profile_data).get("items") # Already sorted playlist

    # top_track_playlist_list = list()
    # for playlist in playlist_data_list:
    #     tracks_in_playlist = getTrackFromPlaylistData(authorization_header, playlist).get("items")
    #     track_id_populer_flat_tuplelist = [(item.get("track").get("id"), item.get("track").get("popularity")) for item
    #                                        in tracks_in_playlist]
    #     sorted_by_popularity_tuplelist = sorted(track_id_populer_flat_tuplelist, key=lambda id_popular: id_popular[1],
    #                                             reverse=True)[:5]
    #     top_track_playlist_list.extend(sorted_by_popularity_tuplelist)

    top_track_playlist_list = [track.get('id') for track in getTopTrack(authorization_header).get('items')]

    audio_feature_list = [(x, getAudioFeatureFromTrack(authorization_header, x)) for x in top_track_playlist_list]
    sort_variable_list = [(x[0], x[1].get('valence'), x[1].get('instrumentalness'), x[1].get('energy'),
                           x[1].get('danceability'), x[1].get('acousticness'))
                          for x in audio_feature_list]

    vw = 0 # vw = valence weight
    iw = 0 # iw = instrumentalness weight
    ew = 0 # ew = energy weight
    dw = 0 # dw = danceability weight
    aw = 0 # aw = acousticness weight

    if weather_id == 0:
        # Sunny
        vw = 1.6
        iw = -1.05
        ew = 1.7
        dw = 1.3
        aw = -1.3
    elif weather_id == 1:
        # Cloudy
        vw = -1.3
        iw = 1.5
        ew = -1.6
        dw = -1.2
        aw = 1.1
    elif weather_id == 2:
        # Rain
        vw = -1.5
        iw = 1.2
        ew = -1.7
        dw = -1.3
        aw = 1.8
    elif weather_id == 3:
        # snow
        vw = -1.15
        iw = 1.5
        ew = -1.5
        dw = -1.03
        aw = 1.2

    print("weather",weather_id)
    # print("vw",vw,"iw",iw,"ew",ew,"dw",dw,"aw",aw,)

    calculated_sort_variable_list = sorted([(track_data[0],
                                             ((track_data[1] * vw) + (track_data[2] * iw) + (track_data[3] * ew) + (
                                                     track_data[4] * dw) + (track_data[5] * aw))
                                             )
                                            for track_data in sort_variable_list], key=lambda sort_key: sort_key[1],
                                           reverse=True)

    recommendation_tracks = getRecommendationThroughTracks(authorization_header, [x[0] for x in calculated_sort_variable_list[:5]], []).get("tracks")

    create_playlist = postBlankPlaylist(authorization_header, weather_word, profile_data.get('id'))
    print("create_playlist",create_playlist)
    post_tracks_playlist = postTrackToPlaylist(authorization_header,[x.get('id') for x in recommendation_tracks],create_playlist[1])
    print("post_tracks_playlist",post_tracks_playlist)

    return render_template("index.html",sorted_array=getIframePlaylist(create_playlist[1]) ,weather_word=weather_word)

def getIframePlaylist(playlist_id):
    open_base_url = 'https://open.spotify.com/embed?uri=spotify'
    iframe_playlist_url = '{}:playlist:{}'.format(open_base_url,playlist_id)

    return iframe_playlist_url

def getIframeSourceList(raw_track_list):
    # https://open.spotify.com/embed?uri=spotify:track:24HKv1Y7SIO3YfGCQzjDz4
    open_base_url = 'https://open.spotify.com/embed?uri=spotify'
    track_id = [x.get('id') for x in raw_track_list]

    iframe_url = ['{}:track:{}'.format(open_base_url,track) for track in track_id]

    return iframe_url

def getRecommendationThroughTracks(authorization_header, listOfSeedTracks, listOfAudioFeature):
    # example; https://api.spotify.com/v1/recommendations?limit=10&market=ES&seed_tracks=1BDY39wDjT45KwlPADHap3%2C2wz8v9hjCcnp3m7kbZZMTG&target_acousticness=3
    limit = 20
    market = "ES"
    print("listOfSeedTracks",listOfSeedTracks)
    recommend_base_endpoint = "{}/recommendations?limit={}&market={}".format(SPOTIFY_API_URL,limit,market)
    appended_list_seed = ','.join(listOfSeedTracks)
    seed_api_endpoint = "{}&seed_tracks={}&".format(recommend_base_endpoint,appended_list_seed)
    raw_audio_feature = '&'.join("%s=%s" % (key, val) for (key, val) in listOfAudioFeature)
    audio_feature_api_endpoint = "{}{}".format(seed_api_endpoint,raw_audio_feature)

    recommend_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    recommend_data = json.loads(recommend_response.text)

    return recommend_data

def getWeatherFromZip(zipcode):
    state = 'us'
    weather_api_endpoint = "{}?zip={},{}&appid={}".format(WEATHER_API_URL,zipcode,state,WEATHER_APP_ID)
    weather_response = requests.get(weather_api_endpoint)
    weather_data = json.loads(weather_response.text)

    return weather_data

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

if __name__ == "__main__":
    app.run(debug=True,port=PORT)
