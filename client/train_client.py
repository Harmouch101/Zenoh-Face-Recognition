import sys
import time
from zenoh import Zenoh,Encoding, Value
import cv2
import numpy as np
import argparse as arg
class Zenoh_Object():
	def __init__(self,train_selector,locator):
		self._train_selector = train_selector
		self._locator = locator
		self._zenoh = None
		self._wk = None
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._Count = 0
	def create_zenoh(self):
		print('\n[*] Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('\n[*] Use Workspace on "{}" to send training samples'.format(self._train_selector))
		self._wk = self._zenoh.workspace(self._train_selector)

	def send(self,video):
		if self._zenoh == None:
			self.create_zenoh()
		face_id = input ('\n[*] Please enter the user name and press <return> ==> ')
		sc_fact = input ('\n[*] please enter the image scale factor (0 < nb < 100) ==> ')
		print ("\n[*] Initializing the camera, please look at the camera lens and wait ...")
		while (True):
			ret, img = video.read()
			if img is None:
				break
			self._Count += 1
			scaled_Image = self.Manipulate(img,sc_fact)
			encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
			is_success, im_buf_arr = cv2.imencode(".jpeg", scaled_Image, encode_param)
			im_buf_bytes = im_buf_arr.tobytes()
			cv2.imshow('sending images',  scaled_Image)
			k = cv2.waitKey (1) & 0xff
			if k == 27:
				break
			if self._Count == 51:
				break
			print("\n[*] Publishing image on ",self._train_selector + face_id)
			self._wk.put(self._train_selector + face_id, Value(im_buf_bytes, Encoding.RAW))
			time.sleep(0.1)
		self._zenoh.logout()
		video.release()
		cv2.destroyAllWindows()
		sys.exit("\n[*] Exiting The Program...")

	def Manipulate(self,img,scale_percent):
		scale_percent = int(scale_percent)
		width = int(img.shape[1] * scale_percent / 100)
		height = int(img.shape[0] * scale_percent / 100)
		dim = (width, height)
		return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)


def Arg_Parse():
	Arg_Par = arg.ArgumentParser(prog='Train_Client',
		description='A process that takes images from a webcam for sending it to the server')
	Arg_Par.add_argument('--train_selector', '-ts',
		default='/training/',
		type=str,
		help='The selector representing the URI of training images')
	Arg_Par.add_argument("-l", "--locator",
		default=None,
		type=str,
		help = "The locator to be used to create a zenoh session."
		"'tcp/ip-add:port' like 'tcp/192.168.0.1:9999'"
		"By default dynamic discovery is used")
	Arg_Par.add_argument("-v", "--video",
					help = "path of the video or if not then webcam")
	Arg_Par.add_argument("-c", "--camera",
					help = "Id of the camera")
	arg_list = vars(Arg_Par.parse_args())
	return [arg_list['train_selector'],arg_list['locator'],arg_list['video'],arg_list['camera']]	

if __name__ == "__main__":

	if len(sys.argv) == 1:
		print("\n[*] Please Provide an argument !!!")
		sys.exit(0)
	Arg_list = Arg_Parse()
	train_selector,locator,video,cam_id= Arg_Parse()
	Zenoh_Object = Zenoh_Object(train_selector,locator)
	if video != None :
		video = cv2.VideoCapture(video)
		Zenoh_Object.send(video)
	if cam_id != None :
		camera = cv2.VideoCapture(eval(cam_id))
		camera.set(3, 640)
		camera.set(4, 480)
		Zenoh_Object.send(camera)
