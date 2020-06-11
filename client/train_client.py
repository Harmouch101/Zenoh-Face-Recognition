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
class Zenoh_Obj():
	def __init__(self,path1,path2,locator):
		self._path1 = path1
		self._path2 = path2
		self._locator = locator
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._Count = 0
	def create_zen(self):
		print('Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('Use Workspace on "{}" to send training images'.format(self._path1[:-2]))
		print('Use Workspace on "{}" to send id'.format(self._path2[:-2]))
		self._wk1= self._zenoh.workspace(self._path1[:-2])
		self._wk2 = self._zenoh.workspace(self._path2[:-2])

	def listener(self,rname, data, info):
		self.Get_Count(data)
	def Get_Count(self,data):
		self._Count = eval(data.decode())

	def snd(self,video):
		if self._zenoh == None:
			self.create_zen()
		face_id = input ( '\n Enter the user name and press <return> ==> ' )
		self._wk2.rt.write_data(self._path2[:-2] + 'id_img', str(face_id).encode())
		print ( "\n [INFO] Initializing the camera, please look in the camera lens and wait ...")
		sub1 = self._wk2.rt.declare_subscriber(self._path2, SubscriberMode.push(), self.listener)
		while (True):
			ret, img = video.read()
			if img is None:
				break
			scaled_Image = self.Manipulate(img)
			encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
			is_success, im_buf_arr = cv2.imencode(".jpeg", scaled_Image, encode_param)
			im_buf_str = im_buf_arr.tostring()
			cv2.imshow('sending Images',  scaled_Image)
			k = cv2.waitKey (1) & 0xff
			if k == 27:
				break
			elif self._Count == 50:
				break
			self._wk1.rt.write_data(self._path1[:-2] + 'train_img', im_buf_str)

		self._zenoh.logout()
		video.release()
		cv2.destroyAllWindows()
		sys.exit(0)

	def Manipulate(self,img):
		scale_percent = 40
		width = int(img.shape[1] * scale_percent / 100)
		height = int(img.shape[0] * scale_percent / 100)
		dim = (width, height)
		return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)


def Arg_Parse():
	Arg_Par = arg.ArgumentParser()
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

	slt1 = '/Face/Recognition/train_image/**'
	slt2 = '/Face/Recognition/id_image/**'
	locator = 'tcp/127.0.0.1:7447'
	if arg_list["storage1"] != None:
		slt1 = arg_list["storage1"]
	if arg_list["storage2"] != None:
		slt2 = arg_list["storage2"]
	if arg_list["locator"] != None:
		locator = arg_list["locator"]
	return slt1,slt2,locator


if __name__ == "__main__":

	if len(sys.argv) == 1:
		print("Please Provide an argument !!!")
		sys.exit(0)
	Arg_list = Arg_Parse()
	slt1,slt2,loc = get_znh_strs(Arg_list)
	zen_obj = Zenoh_Obj(slt1,slt2,loc)
	if Arg_list["video"] != None :
		video = cv2.VideoCapture(Arg_list["video"])
		zen_obj.snd(video)
	if Arg_list["camera"] != None :
		camera = cv2.VideoCapture(eval(Arg_list["camera"]))
		camera.set(3, 640)
		camera.set(4, 480)
		zen_obj.snd(camera)
