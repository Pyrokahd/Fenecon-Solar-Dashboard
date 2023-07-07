# Fenecon-Solar-Dashboard
A web app for logging and displaying solar voltage values for a fenecon solar collector system. \
It primarly displays the average (average over all battery cells) voltage for every battery module. Every module has 14 cells. These values are collected from the battery tower using the fenecon API and then stored in a csv file.

[Installation Linux/RaspberryPi](#on-linux--raspberry-pi)  <br>
[Installation Windows](#on-windows) <br>
[Data Location](#file-storage---where-is-my-data) <br>
[Some docker commands](#Some-docker-commands "basic docker commands")  <br>
[Troubleshooting](#Troubleshooting)  <br>


There are two applications each is run as its own process or docker container:
- The data logging script at data_logging_Scripts/collectDataVoltageV5.py
- the dashboard app (the files outside data_logging_scripts)

The IP and the number of modules in the config.json may need to be changed depending on your battery module and it's ip address.

![biggif_example](/screenshots/dashboard1.png)

![biggif_example](/screenshots/dashboard2.png)

# deploying using docker
I recommend using a raspberry pi, as both the data collection script and the dashboard server are supposed to run permanent.

On the host machine:
## On Linux / raspberry pi

**1. install docker** (here with convenience script)  <br>
```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
Other options on [docker docs](https://docs.docker.com/engine/install/ubuntu/). <br>
Full raspberry docker installation guide [here](https://www.simplilearn.com/tutorials/docker-tutorial/raspberry-pi-docker).

**2. Check installation** by running hello-world  <br>
```
sudo docker run hello-world
```

**3. Clone this repository** (git should be preinstalled in most linux systems)  <br>
navigate to a target directory then:
```
git clone https://github.com/Pyrokahd/Fenecon-Solar-Dashboard.git
```

### Setting a static IP for your raspberry pi
If the server is a raspberry pi (i am using a raspberry pi 4) then you might want to set a static ip adress for it:

1. Get Router IP and DNS IP   <br>
Enter in a terminal
```
ip r
grep "namesever" /etc/resolv.conf
```
The **ROUTER IP** is the first ip after "default via".
The **DNS IP** is the IP from the second command.

2. Edit dhcpcd.conf  <br>
```
nano /etc/dhcpcd.conf
```

3. Add the following lines at the end
```
interface [INTERFACE]
static_routers=[ROUTER IP]
static domain_name_servers=[DNS IP]
static ip_address=[STATIC IP ADDRESS YOU WANT]/24
```

4. save and close the file, restart the raspberry

Interface is either wlan0 or eth0 depending on wifi or ethernet connection. <br>
Example:
```
interface eth0
static_routers=192.168.1.1
static domain_name_servers=192.168.1.1
static ip_address=192.168.1.200/24
```


### Start data collections script
**1. Open a terminal**  <br>

**2. Navigate to data_logging_scripts directory** in this repo (...\Fenecon-Solar-Dashboard\data_logging_scripts)  <br>

**3. Change API URL and amount of modules to your battery tower**  <br>
Open the config.json file and adjust the IP address (batteryIP) to your local adress from your battery tower, including the port.  <br>
Also adjust the number of modules (module_count) to the correct amount.

**4. Create docker image**   <br>
(this may take some time)
```
docker build -t datacollection-docker .
```

**5. Create a docker Volume** (to persistently save the data outside a docker container)  <br>
```
docker volume create fenDataVolume
```

**6. Run image in a docker container** (with mounted volume)  <br>
```
docker run --mount source=fenDataVolume,destination=/app/data datacollection-docker
```

### Start Dashboard server
**1. Open a new terminal** <br>

**2. Navigate to this repo** (...\Fenecon-Solar-Dashboard)  <br>

**3. Create docker image**   <br>
(this may take even more time like 1300+ seconds)
```
docker build -t fdashboard-docker .
```

**4. Create a docker Volume** (should already be there from step 4 in the previous section, but calling it twice doesn't hurt)  <br>
```
docker volume create fenDataVolume
```

**5. Run image in a docker container** (with access to port 80 and with mounted volume)  <br>
```
docker run --publish 80:80 --mount source=fenDataVolume,destination=/app/data fdashboard-docker
```

**6. Wait 4 minutes** (The data collection first needs to create the csv file by making API requests)  <br>

**7. check your local ip adress**  <br>
In a new Terminal enter:
```
ifconfig
```
The Ip adress is something like 192.168.1...

**8. Enter that IP adress into a browser** on a machine connected to the same network  <br>

### Note: Installation via SSH
When using SSH to connect to the host machine (in example a raspberry pi) make sure to run the **docker run ...** commands in a virtual terminal like [Linux screen](https://linux.die.net/man/1/screen). 
So you open a terminal on your computer, connect to the raspberry or linux machine via SSH, then you run the commands and before the docker run command enter a screen. This way you can close the terminal on your computer without interrupting the running programs (docker container).
To install linux screen on the host machine use `sudo apt-get install screen`.

#### Linux Screen commands
**create screen**
```
screen -S NAME
```
**enter screen**
```
screen -r NAME
```
**leave screen**
press: ctrl+a+d

**list screens**
```
screen -ls
```

## On Windows
**1. Enable WSL**
See [Microsoft WSL installation Guide](https://learn.microsoft.com/en-us/windows/wsl/install)

**2. Install docker desktop**
[Docker installation guide](https://docs.docker.com/desktop/install/windows-install/)

**3. Restart your computer**

**4. Check installation** by running hello-world  <br>
In a terminal enter:
```
docker run hello-world
```

**5. Download this Repo as ZIP, unzip at target directory**

### Start data collections script
**1. Open a terminal**  <br>

**2. Navigate to data_logging_scripts directory** in this repo (...\Fenecon-Solar-Dashboard\data_logging_scripts)  <br>

**3. Change API URL and amount of modules to your battery tower**  <br>
Open the config.json file and adjust the IP address (batteryIP) to your local adress from your battery tower, including the port.  <br>
Also adjust the number of modules (module_count) to the correct amount.

**4. Create docker image**   <br>
```
docker build -t datacollection-docker .
```

**5. Create a docker Volume** (to persistently save the data outside a docker container)  <br>
```
docker volume create fenDataVolume
```

**6. Run image in a docker container** (with mounted volume)  <br>
```
docker run --mount source=fenDataVolume,destination=/app/data datacollection-docker
```

### Start Dashboard server
**1. Open a new terminal** <br>

**2. Navigate to this repo** (...\Fenecon-Solar-Dashboard)  <br>

**3. Create docker image**   <br>
```
docker build -t fdashboard-docker .
```

**4. Create a docker Volume** (should already be there from step 4 in the previous section, but calling it twice doesn't hurt)  <br>
```
docker volume create fenDataVolume
```

**5. Run image in a docker container** (with access to port 80 and with mounted volume)  <br>
```
docker run --publish 80:80 --mount source=fenDataVolume,destination=/app/data fdashboard-docker
```

**6. Wait 4 minutes** (The data collection first needs to create the csv file by making API requests)  <br>

**7. check your local ip adress**  <br>
In a new Terminal enter:
```
ipconfig
```
The Ip adress is something like 192.168.1...

**8. Enter that IP adress into a browser** on a machine connected to the same network  <br>

# file storage - Where is my data?
The created csv file is stored in the docker containers and shared on the volume. 

Docker volumes can be found in windows (with WSL enabled - linux for windows) via the filebrowser, \
enter: `\\wsl$\docker-desktop-data\data\docker\volumes`

In Linux the path is (you need admin/root rights):
`/var/lib/docker/volumes/`

# Some docker commands
Show Images installed:
```
docker image ls
```
Show created volumes:
```
docker volume ls
```
Show docker container:
```
docker container ls
```
Stop and remove docker container:
```
docker stop <Container_ID> docker rm <Container_ID>
```

# Troubleshooting
If the dashboard server is not running after 5 minutes, remove the docker container running it (see section **Some docker commands**). Then recreate and run the container with the docker run command in the installation guide. 

If this doesn't help you can check if the csv file has been generated or not (section **file storage**). If there is a csv file then the server should run unless the connection is somehow prevented.
