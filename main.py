from flask import Flask, request, redirect, g, render_template
import urllib
import urllib.parse

from datafoo import iframe
from datafoo import spotify
from datafoo import openWeather

app = Flask(__name__)

# Weather Data
weather_id = 0
weather_word = "clear sky"

# Port number
PORT = spotify.PORT

@app.route("/")
def weather():
    return render_template('weather.html')

@app.route('/', methods=['POST'])
def weather_post():
    global weather_id
    global weather_word

    zipcode = request.form['text']

    raw_weather_data_from_zipcode = openWeather.getWeatherFromZip(zipcode);
    loose_weather_data = raw_weather_data_from_zipcode.get("weather")[0]
    global_weather = loose_weather_data.get("id")
    weather_word = loose_weather_data.get("main")

    # print("Current Weather:", loose_weather_data.get("main"), global_weather)
        # Sunny Day : 800 - weather_id : 0
        # Windy, Cloudy Days: 8xx NOT 800 - weather_id : 1
        # Rainy Days: 2xx Thunderstorm 3xx Drizzle 5xx Rain - weather_id : 2
        # Snowy Days: 6xx Snow - weather_id : 3
    global_weather_parse = global_weather // 100
    if global_weather == 800:
        weather_id = 0
    elif global_weather_parse == 8:
        weather_id = 1
    elif global_weather_parse == 2 or global_weather_parse == 3 or  global_weather_parse == 5:
        weather_id = 2
    elif global_weather_parse == 6:
        weather_id = 3

    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key,val in spotify.auth_query_parameters.items()])
    auth_url = "{}/?{}".format(spotify.SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    global weather_id
    global weather_word

    authorization_header = spotify.getAuthorizationHeader()

    profile_data = spotify.getProfileData(authorization_header)

    # Old way of searching. Will get all the playlists in the user. In each of the playlists, it will get the top 5 popular tracks.
        # Utilized that to look for the tracks corresponding with the weather
    # playlist_data_list = spotify.getPlaylistData(authorization_header, profile_data).get("items") # Already sorted playlist
    # top_track_playlist_list = list()
    # for playlist in playlist_data_list:
    #     tracks_in_playlist = getTrackFromPlaylistData(authorization_header, playlist).get("items")
    #     track_id_populer_flat_tuplelist = [(item.get("track").get("id"), item.get("track").get("popularity")) for item
    #                                        in tracks_in_playlist]
    #     sorted_by_popularity_tuplelist = sorted(track_id_populer_flat_tuplelist, key=lambda id_popular: id_popular[1],
    #                                             reverse=True)[:5]
    #     top_track_playlist_list.extend(sorted_by_popularity_tuplelist)

    top_track_playlist_list = [track.get('id') for track in spotify.getTopTrack(authorization_header).get('items')]

    audio_feature_list = [(x, spotify.getAudioFeatureFromTrack(authorization_header, x)) for x in top_track_playlist_list]
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

    calculated_sort_variable_list = sorted([(track_data[0],
                                             ((track_data[1] * vw) + (track_data[2] * iw) + (track_data[3] * ew) + (
                                                     track_data[4] * dw) + (track_data[5] * aw))
                                             )
                                            for track_data in sort_variable_list], key=lambda sort_key: sort_key[1],
                                           reverse=True)

    recommendation_tracks = spotify.getRecommendationThroughTracks(authorization_header, [x[0] for x in calculated_sort_variable_list[:5]], []).get("tracks")

    create_playlist = spotify.postBlankPlaylist(authorization_header, weather_word, profile_data.get('id'))
    post_tracks_playlist = spotify.postTrackToPlaylist(authorization_header,[x.get('id') for x in recommendation_tracks],create_playlist[1])

    return render_template("index.html",sorted_array=iframe.getIframePlaylist(create_playlist[1]) ,weather_word=weather_word)

if __name__ == "__main__":
    app.run(debug=True,port=PORT)
