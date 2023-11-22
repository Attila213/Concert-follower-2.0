from flask import Flask, redirect, jsonify, session, request, copy_current_request_context
import urllib.parse
import requests
from datetime import datetime
import threading,json

lock = threading.Lock()
data = None
favorite_artists_data = None

with open('sensitive_datas.json') as file:
    data = json.load(file)



app = Flask(__name__)
app.secret_key = "passwordSOMETHING"
CLIENT_ID = data["CLIENT_ID"]
CLIENT_SECRET = data["CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:5000/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

@app.route("/")
def index():
    return "Welcome to my Spotify concert follower app <a href='/login'>Login with Spotify</a>"

@app.route("/login")
def login():
    scope = 'user-read-private user-read-email user-library-read'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route("/callback")
def callback():
    if "error" in request.args:
        error_message = request.args.get("error")
        print(f"Error received in callback: {error_message}")
        return jsonify({"error": error_message})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL, data=req_body)
        if response.status_code != 200:
            print(f"Error fetching access token: {response.text}")
            return jsonify({"error": "Failed to fetch access token"})
        
        token_info = response.json()
        session['access_token'] = token_info.get('access_token')
        session['refresh_token'] = token_info.get('refresh_token')
        session['expires_at'] = datetime.now().timestamp() + token_info.get('expires_in', 0)
        return redirect("/nav_page")

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect("/login")
    
    req_body = {
        "grant_type": "refresh_token",
        "refresh_token": session["refresh_token"],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=req_body)
    if response.status_code != 200:
        print(f"Error refreshing token: {response.text}")
        return jsonify({"error": "Failed to refresh token"})

    new_token_info = response.json()
    session['access_token'] = new_token_info.get('access_token')
    session['expires_at'] = datetime.now().timestamp() + new_token_info.get('expires_in', 0)

    return redirect("/nav_page")

def get_favorite_artists():
    global favorite_artists_data
    with lock:
        try:
            if 'access_token' not in session:
                return
            
            if datetime.now().timestamp() > session.get('expires_at', 0):
                return

            limit = 50
            offset = 0
            headers = {"Authorization": f"Bearer {session['access_token']}"}
            artist_names = set()

            while True:
                url = f"{API_BASE_URL}me/tracks?limit={limit}&offset={offset}"
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Error fetching favorite songs: {response.status_code}, {response.text}")
                    break

                data = response.json()
                tracks = data['items']

                for track in tracks:
                    artists = track['track']['artists']
                    for artist in artists:
                        artist_names.add(artist['name'])

                if len(tracks) < limit:
                    break

                offset += limit

            favorite_artists_data = list(artist_names)
        except Exception as e:
            print(f"Error in background thread: {e}")

@app.route('/nav_page')
def nav_page():
    @copy_current_request_context
    def thread_function():
        get_favorite_artists()

    threading.Thread(target=thread_function).start()
    return "Welcome to the navigation page! <a href='/favorite-artists'>See Favorite Artists</a>"

@app.route("/favorite-artists")
def get_favorite_artists_view():
    if favorite_artists_data is None:
        return "Data is still loading, please wait..."
   
    return jsonify(favorite_artists_data)
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

    