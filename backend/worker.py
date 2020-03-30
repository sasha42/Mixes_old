import redis
import pickle
import time
import os
from mixes import process_mix


if __name__ == "__main__":
    # connect to the redis queue
    r = redis.from_url(os.environ.get("REDIS_URL"))

    # subscribe to the queue
    p = r.pubsub()
    p.psubscribe('job_*')

    # loop over the queue
    while True:
        message = p.get_message()

        # process message if it actually contains data
        if message and type(message['data']) == bytes:
            # get the job id out
            data = pickle.loads(message['data'])
            print('[worker] triggered on message')

            # download mix
            process_mix(data)

        time.sleep(1)  # be nice to the system :)
