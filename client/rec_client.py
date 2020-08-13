import sys
import time
from zenoh import Zenoh
import cv2
import numpy as np
import argparse as arg
from zenoh.net import (
    Session, QueryDest,
    ZN_STORAGE_DATA, ZN_STORAGE_FINAL,
    ZN_EVAL_DATA, ZN_EVAL_FINAL, SubscriberMode
)
import warnings

class Zenoh_Obj():
	def __init__(self,path1,path2,locator):
		self._path1 = path1
		self._path2 = path2
		self._locator = locator
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self.vid = None
		self._start = 0
		self._stop = 0
		self._frame_length = 0
		self._count = 0
		self._delay_file = open("delay1.txt", "a+")
		self._rate = open("rate1.txt", "a+")
	def create_zen(self):
		print('Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('Use Workspace on "{}" to send an image'.format(self._path1[:-2]))
		print('Use Workspace on "{}" to get an image'.format(self._path2[:-2]))
		self._wk1= self._zenoh.workspace(self._path1[:-2])
		self._wk2 = self._zenoh.workspace(self._path2[:-2])
		print("Declaring Subscriber on '{}'...".format(self._path2))
		sub = self._wk2.rt.declare_subscriber(self._path2, SubscriberMode.push(), self.listener)

	def snd(self,frame):
		if self._zenoh == None:
			self.create_zen()
		if self.vid is None:
			print('Sending the image to',self._path1)
			encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
			is_success, im_buf_arr = cv2.imencode(".jpg", frame, encode_param)
			im_buf_str = im_buf_arr.tostring()
			self._wk1.rt.write_data(self._path1[:-2] + 'snd_img', im_buf_str)
			print("Declaring Subscriber on '{}'...".format(self._path2))
			sub = self._wk2.rt.declare_subscriber(self._path2, SubscriberMode.push(), self.listener)

		else:
			#print('Sending a frame of video to',self._path1)
			encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
			is_success, im_buf_arr = cv2.imencode(".jpeg", frame, encode_param)
			im_buf_str = im_buf_arr.tostring()
			self._frame_length = len(im_buf_str)
			self._start = time.time()
			self._wk1.rt.write_data(self._path1[:-2] + 'snd_img', im_buf_str)
			#print("Get the image from '{}'...".format(self._path2))
			#print("Sending query to'{}'...".format(self._path2))
			#time.sleep(0.01)

	def listener(self,rname, data, info):
	    self.Read_Image(data)
	    
	def Read_Image(self,data):
		if data is None:
			return
		im_str = np.fromstring(data,dtype=np.uint8)
		self._stop = time.time()
		delay = abs(self._stop - self._start)/2
		rate = (self._frame_length/abs(self._stop - self._start))/1024 #KB/Sec
		print("Transmission Rate = {:.2f} KB/sec".format(rate))
		print("delay :{:.2f} ms".format(delay*1000))
		if self._count < 200 :
			self._delay_file.write(str(delay*1000) + "\n")
			self._rate.write(str(rate) + "\n")
			self._count += 1
		if self._count == 200 :
			self._delay_file.close()
			self._rate.close()
		Image_Decoded=cv2.imdecode(im_str,1)
		if self.vid is not None:
			scale_percent = 200
			width = int(Image_Decoded.shape[1] * scale_percent / 100)
			height = int(Image_Decoded.shape[0] * scale_percent / 100)
			dim = (width, height)
			#print(dim)

			scale_up = cv2.resize(Image_Decoded, dim, interpolation = cv2.INTER_AREA)
			cv2.imshow("Video", scale_up)
			cv2.waitKey(1)
		else:
			cv2.imshow('Image', Image_Decoded)
			if cv2.waitKey(0) & 0xFF == ord("q"):
				sys.exit(0)


def Arg_Parse():
	Arg_Par = arg.ArgumentParser()
	Arg_Par.add_argument("-i", "--image",
					help = "path of the image")
	Arg_Par.add_argument("-v", "--video",
					help = "path of the video or if not then webcam")
	Arg_Par.add_argument("-c", "--camera",
					help = "Id of the camera")
	Arg_Par.add_argument("-s1", "--storage1",
					help = "selector(path) for storage1")
	Arg_Par.add_argument("-s2", "--storage2",
					help = "selector(path) for storage2")	
	Arg_Par.add_argument("-l", "--locator",
					help = "give a locator 'tcp/ip-add:port' like 'tcp/192.168.0.1:9999'")
	arg_list = vars(Arg_Par.parse_args())
	return arg_list

def get_znh_strs(arg_list):

	slt1 = '/Face/Recognition/send_image/**'
	slt2 = '/Face/Recognition/get_image/**'
	
	locator = 'tcp/127.0.0.1:7447'
	if arg_list["storage1"] != None:
		slt1 = arg_list["storage1"]
	if arg_list["storage2"] != None:
		slt2 = arg_list["storage2"]
	if arg_list["locator"] != None:
		locator = arg_list["locator"]
	return slt1,slt2,locator

def Manipulate(img):
	scale_percent = 20
	width = int(img.shape[1] * scale_percent / 100)
	height = int(img.shape[0] * scale_percent / 100)
	dim = (width, height)
	return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

if __name__ == "__main__":

	if len(sys.argv) == 1:
		print("Please Provide an argument !!!")
		sys.exit(0)
	warnings.simplefilter("ignore", DeprecationWarning)
	Arg_list = Arg_Parse()
	slt1,slt2,loc = get_znh_strs(Arg_list)
	zen_obj = Zenoh_Obj(slt1,slt2,loc)
	if Arg_list["camera"] != None :
		camera = cv2.VideoCapture(int(Arg_list["camera"]))
		camera.set(3, 640)
		camera.set(4, 480)
		while True:
			ret, img = camera.read()
			if img is None:
				cv2.destroyWindow('video') 
				video.release()
			frame = Manipulate(img)
			#cv2.imshow('frame', frame)
			if cv2.waitKey(0) & 0xFF == ord("q"):
				sys.exit(0)
			zen_obj.vid = frame
			zen_obj.snd(frame)
			if cv2.waitKey(1) & 0xFF == ord("q"):
				sys.exit(0)

	elif Arg_list["video"] != None and Arg_list["image"] == None:
		video = cv2.VideoCapture(Arg_list["video"])
		video.set(3, 640)
		video.set(4, 480)
		while True:
			#start = time.start()
			fps = video.get(cv2.CAP_PROP_FPS)
			ret, img = video.read()
			if img is None:
				break
			frame = Manipulate(img)
			#cv2.imshow('frame', frame)
			#if cv2.waitKey(0) & 0xFF == ord("q"):
			#	sys.exit(0)
			zen_obj.vid = frame
			zen_obj.snd(frame)
			time.sleep(1/fps)


	elif Arg_list["image"] != None and Arg_list["video"] == None:
		img = cv2.imread(Arg_list["image"])
		zen_obj.snd(img)
	zen_obj._zenoh.logout()
	#cv2.destroyWindow('video') 
	video.release()
	sys.exit("Exiting")


