import streamlit as st
import plotly.express as px
import requests
import pandas as pd
from utils import map_keys, map_modes

# base URL of all Spotify API endpoints
BASE_URL = 'https://api.spotify.com/v1/'
@st.cache
def spotify_connection():
    CLIENT_ID = '3198847a0df0428498cd64c7cbb3bb72'
    CLIENT_SECRET = '115b947ecf3044448a6265782d644f4c'
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

    return headers

@st.cache
def get_artist_id(artist_name: str):
    headers = spotify_connection()

    query_result =requests.get(BASE_URL + 'search/', headers=headers, params={ 'q': artist_name, 'type': 'artist', 'limit':1}).json()
    artist_id = query_result['artists']['items'][0]['id']

    return artist_id

@st.cache
def get_artist_picture(artist_id: str):
    headers = spotify_connection()

    r_artist = requests.get(BASE_URL + 'artists/' + artist_id, headers=headers).json()
    image_url = r_artist['images'][0]['url']

    return image_url

@st.cache
def get_artist_name(artist_id: str):
    headers = spotify_connection()

    r_artist = requests.get(BASE_URL + 'artists/' + artist_id, headers=headers).json()
    artist_name = r_artist['name']

    return artist_name

@st.cache
def get_tracks_info(artist_id: str):

    headers = spotify_connection()

    df_songs = pd.DataFrame()

    r_albums = requests.get(BASE_URL + 'artists/' + artist_id + '/albums', headers=headers)
    r_albums = r_albums.json()
    for album in r_albums['items']:
        album_id = album['id']
        album_name = album['name']
        print(album_id)
        r_tracks = requests.get(BASE_URL + 'albums/' + album_id + '/tracks', headers=headers)
        r_tracks = r_tracks.json()
        for track in r_tracks['items']:
            track_id = track['id']
            track_name = track['name']

            r_track = requests.get(BASE_URL + 'audio-features/' + track_id, headers=headers)
            r_track = r_track.json()
            r_track['album_name'] = album_name

            s = pd.Series(r_track, name=track_name)
            s.index.name = track_name
            df_songs[track_name] = s

    df_songs_pivot = df_songs.T

    cols = df_songs_pivot.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df_songs_pivot = df_songs_pivot[cols]
    return df_songs_pivot

def transform_dataframe_to_histogram(df_tracks: pd.DataFrame, group_fields: str):
    df_aux = df_tracks.copy()
    df_aux['occurrences'] = 1
    if len(group_fields) == 1:
        group_field = group_fields[0]
        df_group_field = df_aux.groupby([group_field, 'album_name'], as_index=False).agg({'occurrences': 'sum'})
        if group_field == 'key':
            df_group_field[group_field] = df_group_field[group_field].map(map_keys)
        elif group_field == 'mode':
            df_group_field[group_field] = df_group_field[group_field].map(map_modes)
        df_group_field_final = df_group_field.sort_values(by=group_field)

    elif len(group_fields) == 2:
        group_new_field = '_'.join(group_fields)
        for group_field in group_fields:
            if group_field == 'key':
                df_aux[group_field] = df_aux[group_field].map(map_keys)
            elif group_field == 'mode':
                df_aux[group_field] = df_aux[group_field].map(map_modes)

        field1, field2 = group_fields
        df_aux[group_new_field] = df_aux[field1] + ' ' + df_aux[field2]
        df_group_field = df_aux.groupby([group_new_field, 'album_name'], as_index=False).agg({'occurrences': 'sum'})

        #df_group_field['occurrences'] = round(df_group_field['occurrences'] / len(df), 2) * 100
        df_group_field_final = df_group_field.sort_values(by=group_new_field)

    return df_group_field_final

try:
    st.title('Which keys and modes are the most used by artists?')
    search_term = st.radio(
        "Search by:",
        ('Artist name', 'Spotify artist ID'))

    url = 'https://artists.spotify.com/help/article/finding-your-artist-url'
    st.caption('Check [this]({}) to know how to get the ID'.format(url))

    if search_term == 'Artist name':
        artist_search_term = st.text_input('Introduce an artist name', 'Lord Malvo')
        mode = 'name'
    elif search_term == 'Spotify artist ID':
        artist_search_term = st.text_input('Introduce a Spotify artist ID', '0RpTnyHVl084J1I5V79gos')
        mode = 'id'

    if mode == 'name':
        artist_id = get_artist_id(artist_search_term)

    elif mode == 'id':
        artist_id = artist_search_term

    artist_name = get_artist_name(artist_id) # It will be retaken, because maybe the input artist_name is interpreted as other's
    picture_url = get_artist_picture(artist_id)

    col1, col2 = st.columns(2)

    with col1:
        # Artist picture
        st.markdown(
            "<img alt='ARTIST' src='{}' width='250px' height='250px' style='text-align: center; float: center'></img>".format(picture_url),
            unsafe_allow_html=True)

    with col2:
        st.write("**Artist name**: {}".format(artist_name))
        st.write("**Spotify artist ID**: {}".format(artist_id))
        st.write("**Link to Spotify**: {} \n".format('https://open.spotify.com/artist/'+artist_id))

    try:
        df = get_tracks_info(artist_id)
        #st.dataframe(df)

    except Exception as e:
        st.error(
            """**No data could be found for group/artist selected.** \n
            {}""".format(e)
        )

    tab1, tab2, tab3 = st.tabs(["By key", "By mode", "By key-mode"])

    n_total_tracks = len(df)

    with tab1:
        try:
            st.write('Total number of songs by artist: {}'.format(n_total_tracks))
            group_field = 'key'
            df_keys = transform_dataframe_to_histogram(df_tracks=df, group_fields=[group_field])

            # Create distplot with custom bin_size
            fig = px.histogram(df_keys, x=group_field, y='occurrences', color='album_name', color_discrete_sequence=['#1DB954'],
                               hover_data=['key', 'album_name'], labels={group_field: 'Key', 'album_name': 'Album name'})
            fig.update_layout(yaxis_title='Nº of occurrences')

            # Plot!
            st.plotly_chart(fig)

        except Exception as e:
            st.error(
                """**Histogram could not be built for group/artist selected** \n
                {}""".format(e))

    with tab2:
        try:
            st.write('Total number of songs by artist: {}'.format(n_total_tracks))
            group_field = 'mode'
            df_modes = transform_dataframe_to_histogram(df_tracks=df, group_fields=[group_field])

            # Create distplot with custom bin_size
            fig = px.histogram(df_modes, x=group_field, y='occurrences', color='album_name', color_discrete_sequence=['#1DB954'],
                               labels={group_field: 'Mode', 'album_name': 'Album name'})
            fig.update_layout(yaxis_title='Nº of occurrences')

            # Plot!
            st.plotly_chart(fig)

        except Exception as e:
            st.error(
                """**Histogram could not be built for group/artist selected** \n
                {}""".format(e))

    with tab3:
        try:
            st.write('Total number of songs by artist: {}'.format(n_total_tracks))
            df_keys = transform_dataframe_to_histogram(df_tracks=df, group_fields=['key', 'mode'])

            # Create distplot with custom bin_size
            fig = px.histogram(df_keys, x='key_mode', y='occurrences', color='album_name', color_discrete_sequence=['#1DB954'],
                               labels={group_field: 'Key-Mode', 'album_name': 'Album name'})
            fig.update_layout(yaxis_title='Nº of occurrences')

            # Plot!
            st.plotly_chart(fig)

        except Exception as e:
            st.error(
                """**Histogram could not be built for group/artist selected** \n
                {}""".format(e))

except Exception as e:
    st.error(
        """
        **{}** \n
        Error: %s
    """.format(e)
    )