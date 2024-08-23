# Music Converter

This program allows you to convert music between YouTube Music and Spotify.

## Installation

To install the required libraries, you can use the `requirements.txt` file. Run the following command:

```bash
pip install -r requirements.txt
```

## Setup

### Spotify
1. Create a new Spotify developer app at https://developer.spotify.com/dashboard

2. Set the redirect url to http://localhost:8888/callback

3. Once created navigate to settings and copy the Client ID and Client Secret. You will need to enter these into the program later.

4. You are ready to use Spotify features in the program.

### YouTube Music
1. Simply log-in to YouTube when prompted by the program.

## Troubleshooting

1. Sometimes YouTube Music will un-authenticate the user. The program should prompt you in log-in again. If it does not work after that, delete the ytmusic_config.json file and try again.