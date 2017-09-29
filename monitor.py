import os, sys, json, webbrowser
from os import environ

import requests
import sounddevice as sd
import soundfile as sf
from acrcloud.recognizer import ACRCloudRecognizer
from apscheduler.schedulers.blocking import BlockingScheduler

'''
every n seconds, record a new n second audio clip
toss that audio clip at acrcloud and get album id
if album id is different than current album id, get cover image url from spotify
'''

ACRC_HOST = environ['ACRC_HOST']
ACRC_ACCESS_KEY = environ['ACRC_ACCESS_KEY']
ACRC_ACCESS_SECRET = environ['ACRC_ACCESS_SECRET']

SPOTIFY_CLIENT_ID = environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = environ['SPOTIFY_CLIENT_SECRET']
RECORDING_FILENAME = '/tmp/o.wav'


def record_sample():

    print "recording sample"
    samplerate = 44100  # Hertz
    duration = 8  # seconds

    mydata = sd.rec(int(samplerate * duration), samplerate=samplerate,
                    channels=2, blocking=True)
    sf.write(RECORDING_FILENAME, mydata, samplerate)
    identify_sample()

def identify_sample():

    print "identifying sample"
    config = {
        'host': ACRC_HOST,
        'access_key':ACRC_ACCESS_KEY,
        'access_secret': ACRC_ACCESS_SECRET,
        'timeout':8 # seconds
    }

    re = ACRCloudRecognizer(config)
    buf = open(RECORDING_FILENAME, 'rb').read()
    sample_details = json.loads(re.recognize_by_filebuffer(buf, 0))
    album_id = sample_details['metadata']['music'][0]['external_metadata']['spotify']['album']['id']
    find_art(album_id)

def find_art(album_id):
    print "finding artwork"
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    grant_type = 'client_credentials'

    #Request based on Client Credentials Flow from https://developer.spotify.com/web-api/authorization-guide/

    #Request body parameter: grant_type Value: Required. Set it to client_credentials
    body_params = {'grant_type' : grant_type}

    url='https://accounts.spotify.com/api/token'

    response=requests.post(url, data=body_params, auth = (client_id, client_secret))
    access_token = response.json()['access_token']

    album_details_url = "https://api.spotify.com/v1/albums/%s?market=us" % album_id

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer %s' % access_token
    }

    response = requests.get(album_details_url, headers = headers)
    webbrowser.open(response.json()['images'][0]['url'])


sched = BlockingScheduler()

sched.add_job(record_sample, 'interval', seconds=10)

sched.start()
