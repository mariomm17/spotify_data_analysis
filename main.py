import streamlit as st
import requests
import pandas as pd



@st.cache
def generate_df():
    CLIENT_ID = '4cbdd593d6554f9eb9375741f1c23cd4'
    CLIENT_SECRET = '1183b6dd611e4bdbad58d16e5187ddc0'

    AUTH_URL = 'https://accounts.spotify.com/api/token'

    # POST
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    print(auth_response)

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data['access_token']

    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    # base URL of all Spotify API endpoints
    BASE_URL = 'https://api.spotify.com/v1/'

    df_songs = pd.DataFrame()

    nonak_id = '1Sghk5FdovRZVQutvGK2PD'
    lordmalvo_id = '0RpTnyHVl084J1I5V79gos'
    latrinidad_id = '15KUuOUuBqWGiInJr8dZah'


    artists = {nonak_id:'Nonak',
               lordmalvo_id:'Lord Malvo',
               latrinidad_id:'La Trinidad'}


    for artist_id in artists.keys():
        r_albums = requests.get(BASE_URL + 'artists/' + artist_id + '/albums', headers=headers)
        r_albums = r_albums.json()
        for album in r_albums['items']:
            album_id = album['id']
            r_tracks = requests.get(BASE_URL + 'albums/' + album_id + '/tracks', headers=headers)
            r_tracks = r_tracks.json()
            for track in r_tracks['items']:
                track_id = track['id']
                track_name = track['name']

                r_track = requests.get(BASE_URL + 'audio-features/' + track_id, headers=headers)
                r_track = r_track.json()
                r_track['artist'] = artists[artist_id]

                s = pd.Series(r_track, name=track_name)
                s.index.name = track_name
                df_songs[track_name] = s

    df_songs_pivot = df_songs.T

    cols = df_songs_pivot.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df_songs_pivot = df_songs_pivot[cols]
    return df_songs_pivot

try:
    df = generate_df()
    st.dataframe(df)

    print("Histograms")
    st.write("Histograms")
    st.bar_chart(df, x='key')

except:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
    )