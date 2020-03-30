import youtube_dl
import time
import pickle
from secrets import token_urlsafe
import redis
import os
import requests


# configure redis path
r = redis.from_url(os.environ.get("REDIS_URL"))

# temporary hack for hook
mix_hook = None


def redis_sync(data: dict):
    """Checks if data is in redis, then syncs it"""

    # try go get the data out
    try:
        p_data = r.get(str(data['id']))
        redis_data = pickle.loads(p_data)

        # check if data changed and set it if that's the case
        if str(data) != str(redis_data):
            p_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
            r.set(str(data['id']), p_data)

    except:
        print('[redis] created new item')
        p_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        r.set(str(data['id']), p_data)
        r.publish(f'job_{data["id"]}', p_data)


def mix_hook(d: dict):
    # compute percentage
    percentage = int((d['downloaded_bytes']/d['total_bytes'])*100)

    # update job with in progress status
    hook_data = mix_hook.data

    hook_data['percentage'] = abs(percentage-2)
    hook_data['status'] = d['status']

    if d['status'] == 'finished':
        print('[youtube] Done downloading, now converting ...')
        hook_data['status'] = 'converting'
        hook_data['percentage'] = 99

    mix_hook.data = hook_data


# youtube dl configuration
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'progress_hooks': [mix_hook],
}


class Mix(object):
    """Class that defines a mix and provides methods to handle the various
    stages of its lifecycle, like downloading metadata, thumbnails and the mix
    itself"""

    def __init__(self, data: dict):
        # generate job metadata
        print('[class] class initialized')
        if 'id' not in data:
            data.update({'id': token_urlsafe(11)})

        if 'timestamp_loaded' not in data:
            data.update({'timestamp_loaded': int(time.time()*1000)})

        self._data = data

    @property
    def data(self):
        # get data
        redis_sync(self._data)
        return self._data

    @data.setter
    def data(self, val: dict):
        # set data
        redis_sync(self._data)
        self._data = val

    def get_info(self):
        print('[class] getting info')
        with youtube_dl.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(self._data['mix_url'], download=False)

        # add info about mix to redis
        self._data['title'] = info_dict['title']
        self._data['thumbnail_url'] = info_dict['thumbnail']

        return self._data

    def get_thumbnail(self):
        print('[class] getting thumbnail')

        thumbnail_url = self._data['thumbnail_url']

        r = requests.get(thumbnail_url)

        with open(f'{self._data["id"]}-thumbnail.jpg', 'wb') as f:
            f.write(r.content)

    def get_mix(self):
        print('[class] downloading mix')

        # oh dear
        global mix_hook
        mix_hook = self

        # download the mix
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self._data['mix_url']])

    def complete(self):
        print('[class] complete')
        self._data['status'] = 'complete'
        self._data['percentage'] = 100
        self._data['timestamp_completed'] = int(time.time()*1000)

        # i am not sure why i need to do this here but not
        # in other places
        redis_sync(self._data)

        return self._data


def process_mix(data: dict):
    """Processes an incoming request in the queue. First get the info about
    the mix we're about to download, and then actually download it.

    Args:
        job_id (str): string representing the id of the download job"""

    # create a new mix object
    mix = Mix(data)

    # get info about mix
    mix.get_info()

    # download thumbnail
    mix.get_thumbnail()

    # download mix
    mix.get_mix()

    # complete the download of the mix
    mix.complete()
