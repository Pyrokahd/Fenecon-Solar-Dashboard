# Fenecon-Solar-Dashboard
A web app for logging and displaying solar voltage values for a fenecon solar collector system. \
It primarly displays the average (average over all battery cells) voltage for every battery module. Every module has 14 cells. These values are collected from the battery tower using the fenecon API and then stored in a csv file.

*Currently 10 modules are expected in the collection script. There is yet no config file to change it*

There are two applications each is ruin as its own process or docker container:
- The data logging script at data_logging_Scripts/collectDataVoltageV5.py
- the dashboard app (the files outside data_logging_scripts)

The URLs in the data_collection_script (data_logging_Scripts/collectDataVoltageV5.py) may need to be changed depending on your battery modules ip addres.

![biggif_example](/screenshots/dashboard1.png)

![biggif_example](/screenshots/dashboard2.png)

# deploying using docker
1. install docker on target computer
2. clone this repo
3. 
## data collection
1. Navigate to data_logging_scripts in this repo (...\Fenecon-Solar-Dashboard\data_logging_scripts)
3. create image
`docker build -t datacollection-docker .`
3. create volume (for persistent data)
`docker volume create fenDataVolume`
4. run as container
`docker run --mount source=fenDataVolume,destination=/app/data datacollection-docker`

It collects the current data every 5 minutes via the API.

## dashboard
1. Navigate to this repo (...\Fenecon-Solar-Dashboard)
2. create image
`docker build -t fdashboard-docker .`
3. create volume (for persistent data)
`docker volume create fenDataVolume`
4. run as container (on port 8050)
`docker run --publish 8050:8050 --mount source=fenDataVolume,destination=/app/data fdashboard-docker`
5. look up the local ip address of that computer
6. Enter that url on port 8050 into the browser (example: http://192.168.1.47:8050/)

## file storage
The created csv file is stored in the docker containers and shared on the volume. 

Docker volumes can be found in windows (with WSL enabled - linux for **windows**) via the filebrowser \
File browser enter: `\\wsl$\docker-desktop-data\data\docker\volumes`

In Linux the path is:
`/var/lib/docker/volumes/`

# Other info
You can add `-rm` to the run command for docker to close the container when the application is closed.
