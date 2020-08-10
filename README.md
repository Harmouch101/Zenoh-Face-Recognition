<h1>Zenoh Face Recognition On Raspberry Pi</h1>
<p>This project implements a face recognition algorithm into Zenoh router(edge computing) using LBPH algorithm for the recognition part and Viola Jones for the detection part. For more information about these algorithms, please refer to <a href="https://github.com/Harmouch101/Face-Recogntion-Detection">this repo</a>.
</p>
<h2>Zenoh API on Raspberry Pi model b+</h2>	
<p>At the moment of building this project, the Zenoh API is only compatible with a specific versions of Raspian(Raspbian-9.4-armv7l) which can be downlaoded using <a href="https://downloads.raspberrypi.org/raspbian_full/images/raspbian_full-2019-09-30/">this link</a>
</p>
<h2>Writing The Raspian image to a microSD card</h2>	
<ol>
	<li> Connect the SD card to your PC.</li>
	<li> Format your memory card. For example, on windows, simply right click on the sd card icon and click format.</li>
	<img src="pics/Capture0.png" alt="format">
	<li> Unpack the downloaded ZIP archive, downloaded previously, to any location on your computer.</li>
	<li> Download and install <a href="https://github.com/pbatard/rufus">Rufus</a> utility to write images to microSD on your computer.</li>
	<li> Run the Rufus program and write raspian image on the sd card.</li>
	<img src="pics/Capture1.PNG" alt="rufus">
	<img src="pics/Capture2.PNG" alt="select the iso file">
	<img src="pics/Capture3.PNG" alt="write the image">
</ol>
<h2>Install Zenoh on Raspian OS</h2>	
<p> Once the Raspberry Pi is up and running, click the following <a href="https://download.eclipse.org/zenoh/zenoh/0.4.2-M1/eclipse-zenoh-0.4.2-M1-Raspbian-9.4-armv7l.tgz">link</a> to download the zenohd executable file.</p>
<ul> 
	<li> Unpack the archived file in a given directory.</li>
	<li> Open the folder(bin folder) thatcontains the executable file zenohd.exe.</li>
	<li> Open your terminal and enter the following command :</li>
</ul>

```bash
$ ./zenohd.exe -v -p tcp/192.168.1.8:7447	# 192.168.1.8 is the ip address of the other peer(pc).
```
<p> This will run zenoh daemon on your raspberry and connect to the "192.168.1.8" peer, which, by default, is listening on port 7447 for zenoh communication. The raspberry will play the role of a client, and on another pc, there is a zenoh server.</p>
<h2>Install Zenoh on a Linux distro(ubuntu in my case)</h2>
<p> For the sake of simplicity, zenoh is available in a docker image which we will use it in our project. So first make sure that <a href="https://docs.docker.com/engine/install/ubuntu/">docker</a> is available on your machine by executing the following command:</p>

```bash
$ docker --version
```
<p> If it is installed, your terminal should output the Docker version number. As described in this <a href="https://github.com/Harmouch101/zenoh">repo</a>, you can install the docker image of zenoh using the following command :</p>

```bash
$ docker pull eclipse/zenoh:latest
```
<p> This pulls the zenoh image/repo from the registry to your local machine. In order to verify that the image is locally stored with the docker engine, you need to run the following command:</p>

```bash
$ docker image ls      # or $ docker images
```
<p> which will output the following if the image is successfully stored on your local machine :</p>

` REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
eclipse/zenoh       latest              a2056fe06164        7 weeks ago         238MB
`
<p> in the beginning, there are no containers on the machine:</p>

```bash
$ docker ps 
```
`Output
 CONTAINER ID     IMAGE     COMMAND     CREATED     STATUS     PORTS     NAMES
`
<p> to create a container associated with the name <b>zenoh</b>, you need to run the following :</p>

```bash
$ sudo docker create -t -i eclipse/zenoh --name zenoh    
```

`Output
 CONTAINER ID           IMAGE               COMMAND           CREATED     STATUS          PORTS      NAMES
 ad40926fcae0     eclipse/zenoh:latest  "/entrypoint.sh -v"  3 hours ago  Exited (137) 3h  			 zenoh
`
<p> you could also rename the container using the following command :</p>

```bash
$ docker rename zenoh zenoh1  
```

`Output
 CONTAINER ID           IMAGE               COMMAND           CREATED     STATUS          PORTS      NAMES
 ad40926fcae0     eclipse/zenoh:latest  "/entrypoint.sh -v"  3 hours ago  Exited (137) 3h 			zenoh1
`
<p> to start the container, execute the following :</p>

```bash
$ docker start -i ad40926fcae0
```

`Output
 * Starting database influxd                                             [ OK ] 
 * Starting: /eclipse-zenoh/bin/zenohd.exe -v
[1597070149.524708][INFO] Running scouting on interface auto
[1597070149.524863][INFO] Joining MCast group
[1597070149.525432][INFO] Zenoh router starting ...
[1597070149.525679][INFO] pid     : c53f541f83c3402080061843287bee3f
[1597070149.525703][INFO] tcpport : 7447
[1597070149.525868][INFO] peers   : 
[1597070149.529727][INFO] Loading plugin 'storages' from '/eclipse-zenoh/bin/../lib/zenoh-plugin-storages.cmxs' with args: '/eclipse-zenoh/bin/../lib/zenoh-plugin-storages.cmxs'...
[1597070149.535750][INFO] [Zstorages] create storages admin space on /@/router/c53f541f83c3402080061843287bee3f/plugin/storages/**
[1597070149.536005][INFO] Loading plugin 'http' from '/eclipse-zenoh/bin/../lib/zenoh-plugin-http.cmxs' with args: '/eclipse-zenoh/bin/../lib/zenoh-plugin-http.cmxs'...
[1597070149.538216][INFO] [Zhttp] listening on port tcp/0.0.0.0:8000
[1597070149.538276][INFO] TcpService listening on port tcp/0.0.0.0:7447
`
<p> to stop the container, open a new terminal and execute the following :</p>

```bash
$ docker stop ad40926fcae0
```
<p> or you could run the docker image <b>eclipse/zenoh</b> using the following :</p>

```bash
$ docker run --init -p 7447:7447/tcp -p 7447:7447/udp -p 8000:8000/tcp eclipse/zenoh -v
```
<p> you could also specify the peer, which is in this case, the IP address of the raspberry :</p>

```bash
$ docker run --init -p 7447:7447/tcp -p 7447:7447/udp -p 8000:8000/tcp eclipse/zenoh -v -p tcp/192.168.1.4:7447
```
`Output
 * Starting database influxd
   ...done.
 * Starting: /eclipse-zenoh/bin/zenohd.exe -v -p tcp/192.168.1.4:7447
[1597070521.551351][INFO] Running scouting on interface auto
[1597070521.551439][INFO] Joining MCast group
[1597070521.551545][INFO] Zenoh router starting ...
[1597070521.551617][INFO] pid     : 46fdc400add84fbdb6ef2d657c92225b
[1597070521.551638][INFO] tcpport : 7447
[1597070521.551683][INFO] peers   : tcp/192.168.1.4:7447
[1597070521.555658][INFO] Loading plugin 'storages' from '/eclipse-zenoh/bin/../lib/zenoh-plugin-storages.cmxs' with args: '/eclipse-zenoh/bin/../lib/zenoh-plugin-storages.cmxs'...
[1597070521.562194][INFO] [Zstorages] create storages admin space on /@/router/46fdc400add84fbdb6ef2d657c92225b/plugin/storages/**
[1597070521.562450][INFO] Loading plugin 'http' from '/eclipse-zenoh/bin/../lib/zenoh-plugin-http.cmxs' with args: '/eclipse-zenoh/bin/../lib/zenoh-plugin-http.cmxs'...
[1597070521.564825][INFO] [Zhttp] listening on port tcp/0.0.0.0:8000
[1597070521.565046][INFO] TcpService listening on port tcp/0.0.0.0:7447
`

<p> to stop the running container, simply press <b>ctrl + c</b> , this is because of --init option which sets <b>ENTRYPOINT</b> to <b>tini</b> and passes the <b>CMD</b> to it.</p>