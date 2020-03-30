import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function useInterval(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback.
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval.
  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      let id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

function App() {
  let [mixUrl, setMixUrl] = useState({mixUrl: ''});
  let [response, setResponse] = useState({response: ''});
  let [count, setCount] = useState(0);
  let [status, setStatus] = useState('');
  let [title, setTitle] = useState('');
  let [isDownloading, setIsDownloading] = useState(false);
  let [downloadState, setDownloadState] = useState('');

  async function mixUrlSubmit() {
    // start checking state of download
    setIsDownloading(true);

    // post the inputted text as a json
    fetch('http://localhost:5000/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'mix_url': mixUrl
      })})

      // then depending on the answer of the server, parse json
      .then((response) => {
        if(response.status >= 200 && response.status < 300) {
          return response.json()
        } else {
          throw new Error("Server can't be reached!")
        }
       })

       // set the json inoto state
       .then((responseJson) => {
         console.log('we got far enough')
         setResponse({
           response: responseJson.jobId,
         }, function(){
           // you can do magic here
         });

       })
       // create an alert with a potential error
       //.catch((error) =>{
      //   Alert.alert(JSON.stringify(error.message))
      //   this.setState({ responseText: error.message })
      // });
   }

  async function checkStatus() {
        // set up url, add jobId as a parameter to it
        var url = new URL('http://localhost:5000/status'),
        params = {jobId: response.response}
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

        // fetch status from server with url generated above
        const res = await fetch(url);
        const data = await res.json();

        console.log(data)

        // extract key variables from received json
        const { status, error, percentage, title, timestamp_completed } = data;

        if (status === 'complete') {
          setIsDownloading(false);
        }

        setStatus(percentage);
        setDownloadState(status);
        setTitle(title);
  }

  useInterval(() => {
    checkStatus()
    setCount(count + 1);
  }, isDownloading ? 2000 : null);

  const handleSubmit = (evt) => {
    evt.preventDefault();
    mixUrlSubmit()
  }

  return (
    <div className="App">
      <header className="App-header">
        <form onSubmit={handleSubmit}>
          <label htmlFor="mixUrl">Download mix</label>
          <input
              type="text"
              name="mix_url"
              id="mixUrl"
              value={mixUrl.mixUrl}
              onChange={e => setMixUrl(e.target.value)}
          />
          <input type="submit" value="Submit" />
        </form>
        <p>
          Job ID: {response.response}
        </p>
        <p>
          Title: {title}
        </p>
        <p>
          Percent complete: {status}% completed
        </p>
        <p>
          Download state: {downloadState}
        </p>
      </header>
    </div>
  );
}

export default App;
