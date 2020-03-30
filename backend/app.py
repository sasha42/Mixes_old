# sasha 2019
from flask import Flask, request, jsonify
from flask_cors import CORS
from mixes import Mix
import redis
import os
import pickle


#############
### SETUP ###
#############

# specify folder for react frontend
react_folder = '../frontend/build/'

# set up flask app with react frontend
app = Flask(__name__, template_folder=react_folder, static_folder=react_folder)

# make sure that CORS is set up correctly
CORS(app)

# connect to redis
r = redis.from_url(os.environ.get("REDIS_URL"))


##############
### ROUTES ###
##############

@app.route('/')
def index():
    """Returns react frontend"""
    return 'hello world'


@app.route('/download', methods=['POST'])
def download_mix():
    """API endpoint for downloading new mixes, you need to specify a URL
    and submit it as a POST request."""
    #mix_url = "https://www.youtube.com/watch?v=u6bCiuVb2Ps"

    # get mix url that was sent over rest api
    data = request.json

    # create a mix download job
    created_mix = Mix(data)

    # return job id
    job_id = created_mix.data['id']
    return jsonify({'jobId': job_id})


@app.route('/status', methods=['GET'])
def get_status():
    """API endpoint to get the status of a specific download"""
    # get job id from url
    job_id = request.args.get('jobId')

    # check that we were able to get a url param
    if job_id == None:
        return jsonify({'error': True,
            'error_description': 'Missing job id'})

    # pull data from redis
    try:
        p_data = r.get(str(job_id))
        data = pickle.loads(p_data)
        print(data)
        return jsonify(data)
    except:
        return jsonify({'error': True,
            'error_description': 'Unable to pull data from queue'})


@app.route('/list', methods=['GET'])
def mixes_list():
    """API endpoint for returning a list of mixes"""
    return 'yasssss'


##############
### SERVER ###
##############

if __name__ == "__main__":
    app.run(debug=True)
