<!DOCTYPE html> 
<html> 
	<head> 
	</head> 
	<body>
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
			<img src="pics/Capture0.png" alt="format" width="500" height="600">
			<li> Unpack the downloaded ZIP archive, downloaded previously, to any location on your computer.</li>
			<li> Download and install <a href="https://github.com/pbatard/rufus">Rufus</a> utility to write images to microSD on your computer.</li>
			<li> Run the Rufus program and write raspian image on the sd card.</li>
			<img src="pics/Capture1.PNG" alt="rufus" width="500" height="600">
			<img src="pics/Capture2.PNG" alt="select the iso file" width="500" height="600">
			<img src="pics/Capture3.PNG" alt="write the image" width="500" height="600">
		</ol>
		<h2>Install Zenoh on Raspian OS</h2>	
		<p> Once the Raspberry Pi is up and running, click the following <a href="https://download.eclipse.org/zenoh/zenoh/0.4.2-M1/eclipse-zenoh-0.4.2-M1-Raspbian-9.4-armv7l.tgz">link</a> to download the zenohd executable file</p>
		<p> Now unpack the archived file in a certain directory.</p>
	</body> 
</html>

