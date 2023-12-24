import random
import string
import urllib.parse
from fastapi import FastAPI
import requests
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv
import json

load_dotenv()
app = FastAPI()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = os.getenv('REDIRECT_URI')
base_url = os.getenv('BASE_URL')


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


@app.get('/')
async def login():
    scope = 'user-read-private user-read-email user-modify-playback-state user-read-playback-state app-remote-control streaming user-read-currently-playing'
    state = generate_random_string(16)

    payload = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    }

    spotify_auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(payload)
    return RedirectResponse(url=spotify_auth_url)


@app.get('/callback')
async def callback(code: str, state: str):
    access_token, refresh_token = authorize(code)
    get_devices(access_token)
    return RedirectResponse(url='/home')


@app.get('/home')
async def home():
    return f'Sistem basarili acildi'


def authorize(code):
    token_url = 'https://accounts.spotify.com/api/token'

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(token_url, data=payload)

    if response.status_code == 200:
        print('Başarılı! Token alındı.')
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        return access_token, refresh_token
    else:
        print('Hata oluştu. Hata kodu:', response.status_code)
        print('Hata mesajı:', response.text)
        return None, None


def get_devices(access_token):
    token_url = base_url + 'me/player/devices'

    header = {
        'Authorization': 'Bearer ' + access_token,
    }

    response = requests.get(token_url, headers=header)

    if response.status_code == 200:
        print('Başarılı! Token alındı.')
        response = response.json()
        for device in response['devices']:
            print(device['name'])
            print(device['id'])
            if 'Note' in device['name']:
                playback_transfer_to(access_token, device['id'])

    else:
        print('Hata oluştu. Hata kodu:', response.status_code)
        print('Hata mesajı:', response.text)


def playback_transfer_to(access_token, id):
    token_url = base_url + 'me/player'

    header = {
        'Authorization': 'Bearer ' + access_token,
    }

    payload = json.dumps({
        'device_ids': [id],
        'play': True
    })
    print(payload)

    response = requests.put(token_url, data=payload, headers=header)

    if response.status_code == 204 or response.status_code == 404:
        print('Başarılı! Aktarıldı.')

    else:
        print('Hata oluştu. Hata kodu:', response.status_code)
        print('Hata mesajı:', response.text)

