# Launching The Program
## Prerequisites
Before you can run the program, you will need to download the necessary models for this program to function. Please navigate to `/models/README.md` for more information.

## Using the `Client`
 - First, connect to the client via `localhost:9253`
 - To just get the default experience up and running skip everything below and navigate to http://localhost:9253/video_feed?identify=true
 - As of right now, to access the video feed you navigate to http://localhost:9253/video_feed
    - There are a few URL parameters you can append to the `video_feed` end point:
        - `width=[?]`; used to define the desired width of the video. Accepts integer values. Actual resolution will depend on what your camera can output. The default value is `640`.
        - `height=[?]`; used to define the desired height of the video. Accepts integer values. Actual resolution will depend on what your camera can output. The default value is `480`.
        - `fps_target=[]`; used to define the desired frame_rate of the video. Accepts integer values. Actual framerate will depend on what your camera can output as well as processing speed. The default value is `60`.
        - `identify=[true/false]`; should facial recognition occur?Works only if the `FaceManager` is set up. The default value is `False`.
        - `detect=[true/false]`; should client detect faces? The default value is `False`.
    - An example of modified parameters: http://localhost:9253/video_feed?width=1280&height=720&fps_target=5&identify=true

## Connecting the `FaceManager`
 - Setup the `FaceManager` via http://localhost:9253/facemanager_setup
    - Launch locally by just going to the above URL
    - If you have the `FaceManger` running somewhere else, tell the `Client` the IP and port by passing URL parameters by appending `?ip=[enter the ip here]&port=[enter the port here]`
 - Once you get the confirmation that the `FaceManager` is setup, you will need to connect to it and connect the `DatabaseManager`
 - By default, if you launch locally navigate to `localhost:9254`, othewise use the IP and port you supplied during setup

 ## Connecting the `DatabaseManager`
 - Setup the `DatabaseManager` via `[ip]:[port]/database_setup`, or if you launched `FaceManager` locally navigate to http://localhost:9254/database_setup
    - Launch locally by just going to the above URL
    - If you have the `DatabaseManager` running somewhere else, tell the `FaceManager` the IP and port by passing URL parameters by appending `?ip=[enter the ip here]&port=[enter the port here]`