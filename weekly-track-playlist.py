from datetime import date, datetime, timedelta
import time
import spotipy
import yaml
import json
import pprint
import spotipy.util as util

def load_config():
    global user_config
    stream = open('config.yaml')
    user_config = yaml.load(stream)

# Returns list of artist ids based on list of names given
def getArtistIds(names):
    artist_ids = []
    for artist_name in artist_names:
        artist = spotifyObject.search(q='artist:' + artist_name, type='artist')
        artistObject = artist['artists']['items'][0]
        if int(artistObject['popularity']) > 50:
            artist_id = artistObject['id']
            artist_ids.append(artist_id)
    return artist_ids

# Returns today's date minus 14 days
def getDateLimit():
    dateLimit = todaysDate - timedelta(days=14)
    return dateLimit.strftime('%Y/%m/%d')


# Remove duplicate albums/songs (explicit/clean versions)
def Remove(duplicate):
    final_list = []
    dup_list = []
    for item in duplicate:
        name = item['name']
        if name not in dup_list:
            dup_list.append(name)
            final_list.append(item)
    return final_list


# Returns list of recent albums from given list of artist ids
def getNewAlbumsForArtist(artist_id):
    returnContent = []
    albums = spotifyObject.artist_albums(artist_id)
    for item in albums['items']:
        uni_release_date = item['release_date']
        album = {'name': item['name'], 'id': item['id'], 'type': 'album'}
        try:
            release_date = datetime.strptime(uni_release_date,'%Y-%m-%d').strftime('%Y/%m/%d')
            dateLimit = getDateLimit()
            if release_date > dateLimit :
                album_group = item['album_group']
                if album_group != 'appears_on':
                    returnContent.append(album)
                else:
                    artist = spotifyObject.artist(artist_id)
                    artist_name = artist['name']
                    album.update({'artist_name': artist_name})
                    featureSongs = getFeaturedSongs(album)
                    for song in featureSongs:
                        returnContent.append(song)
        except:
            pass
    return returnContent

# Returns song(s) that artist that features in movie soundtracks (mixed ownership album)
def getFeaturedSongs(album):
    returnTracks = []
    query = 'album:' + album['name'] + ' artist:' + album['artist_name']
    tracks = spotifyObject.search(q=query, type='track')
    items = tracks['tracks']['items']
    if items:
        for item in items:
            track_uri = item['uri']
            track = {'name': item['name'], 'id': track_uri, 'type': 'track'}
            returnTracks.append(track)
    return returnTracks

# Returns list of tracks by album_id
def getTracksByAlbumId(album_id):
    returnTracks = []
    tracks = spotifyObject.album_tracks(album_id)
    return tracks

# Replaces the tracks on spotify and updates name/description of playlist
def replaceTracks(tracks):
    x = spotifyObject.user_playlist_replace_tracks(user_config['username'], user_config['weekly_playlist_uri_full'], tracks)
    y = spotifyObject.user_playlist_change_details(user_config['username'], user_config['weekly_playlist_uri_partial'], name=playlistName, description=description)


# -----------------------------------------------------------------------------
artist_names = ['Juice WRLD', 'A$AP Rocky', 'XXXTentacion', 'Tyler, The Creator', 'Frank Ocean', 'Khalid', 'Logic', 'Billie Eilish']
artist_names.extend(['Travis Scott', 'Kayne West', 'Kid Cudi', 'Lil Skies', 'Ski Mask The Slump God', 'Drake', 'Post Malone', 'Jaden Smith'])
todaysDate = datetime.today().date()
load_config()
tracksToAdd = []
scope = 'user-top-read user-read-private playlist-modify-private playlist-modify-public'
token = util.prompt_for_user_token(user_config['username'], scope=scope, client_id=user_config['client_id'], client_secret=user_config['client_secret'], redirect_uri=user_config['redirect_uri'])
if token:
    spotifyObject = spotipy.Spotify(auth=token)
    artist_ids = getArtistIds(artist_names)
    for artist_id in artist_ids:
        checkTracks = []
        checkedTracks = []
        checkAlbums = []
        items = getNewAlbumsForArtist(artist_id)
        for item in items:
            if item['type'] is 'album':
                checkAlbums.append(item)
            else:
                checkTracks.append(item)
        albums = Remove(checkAlbums)
        checkedTracks = Remove(checkTracks)
        for track in checkedTracks:
            tracksToAdd.append(track['id'])
        artistTracks = []
        for album in albums:
            album_id = album['id']
            newTracks = getTracksByAlbumId(album_id)
            newTracksList = newTracks['items']
            trackUris = []
            for track in newTracksList:
                track_uri = track['uri']
                trackUris.append(track_uri)
            artistTracks.extend(trackUris)
        tracksToAdd.extend(artistTracks)

    artistString = ', '.join(map(str, artist_names))
    detailsDate = datetime.strptime(todaysDate.strftime('%Y/%m/%d'),'%Y/%m/%d').strftime('%m/%d/%Y')
    playlistName = 'New Music for ' + detailsDate
    description = '***** Updated ' + detailsDate + ' ***** Artist\'s included in this week\'s search: ' + artistString
    print(datetime.today())
    print(description)
    replaceTracks(tracksToAdd)
    print('Success!')
    # print(json.dumps(tracksToAdd, indent=2, sort_keys=True))
else:
    print("No Token found.")
