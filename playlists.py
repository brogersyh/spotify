import datetime
import json
import os
import spotipy
import spotipy.util as util
import sys

def set_environment(client_id, client_secret, redirect_uri):
    os.environ['SPOTIPY_CLIENT_ID'] = client_id
    os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
    os.environ['SPOTIPY_REDIRECT_URI'] = redirect_uri

def cache_playlist(playlist):
    if not os.path.exists('cache'):
        os.makedirs('cache')
    path = os.path.join('cache', playlist['id'] + '.json')
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(playlist, indent=4))

def save_playlist(playlist):
    path = os.path.join('playlists', playlist['name'] + '.md')
    with open(path, 'w', encoding='utf-8') as file:
        # Header
        file.write('# {}\n\n'.format(playlist['name']))
        # Details
        file.write('Created by [{}]({}) · {} songs, {} · [:arrow_forward: Play]({})\n\n'.format(
            playlist['owner']['id'],
            playlist['owner']['external_urls']['spotify'],
            str(playlist['tracks']['total']),
            playlist_duration(playlist),
            playlist['external_urls']['spotify']))
        # Tracks
        file.write('&#35;|Artist|Song\n')
        file.write('----:|:-----|:---\n')
        for i, item in enumerate(playlist['tracks']['items']):
            track = item['track']
            file.write('{}|{}|{}\n'.format(
                str(i + 1),
                track['artists'][0]['name'],
                track['name']))

def playlist_duration(playlist):
    duration = 0
    for item in playlist['tracks']['items']:
        duration += item['track']['duration_ms']
    duration = (duration - (duration % 1000)) / 1000
    return str(datetime.timedelta(seconds=duration))

def main():
    if len(sys.argv) > 4:
        set_environment(sys.argv[2], sys.argv[3], sys.argv[4])
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        print('Usage: python playlists.py [username] [client_id] [client_secret] [redirect_uri]')
        sys.exit()

    token = util.prompt_for_user_token(username, scope='playlist-read-private')

    if token:
        sp = spotipy.Spotify(auth=token)
        offset = 0
        LIMIT = 50
        while True:
            playlists = sp.user_playlists(username, limit=LIMIT, offset=offset)
            if len(playlists['items']) == 0:
                break

            for playlist in playlists['items']:
                if playlist['owner']['id'] != username:
                    print('diff username: ' + playlist['owner']['id'] + " for playlist " + playlist['name'])
                else:
                    print('Found playlist: {} | {} tracks'.format(
                        playlist['name'],
                        playlist['tracks']['total']))

                    result = sp.user_playlist(username, playlist['id'], fields='tracks,next')
                    tracks = result['tracks']
                    playlist['tracks']['items'] = tracks['items']
                    while tracks['next']:
                        tracks = sp.next(tracks)
                        playlist['tracks']['items'] += tracks['items']

                    cache_playlist(playlist)
                    save_playlist(playlist)
            offset += LIMIT
    else:
        print('Error: Cannot get token for', username)

if __name__ == '__main__':
    main()
