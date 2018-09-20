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