import sys
import time
from zenoh import Zenoh,Encoding, Value
import cv2
import numpy as np
import argparse as arg
class Zenoh_Object():
	def __init__(self,recognize_selector,locator):
		self._recognize_selector = recognize_selector
		self._locator = locator
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._decoded_image = None
		self._camera_id = ''
		self._zenoh = None
		self._frame = None
		self._wk = None
		self._Count = 0
	def create_zenoh(self):
		print('\n[*] Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		self._camera_id = 'camera-' + input ('\n[*] Please enter the camera id and press <return> ==> ')
		print('\n[*] Use Workspace on "{}" to send images for recognition purposes'.format(self._recognize_selector + self._camera_id + '/'))
		self._wk = self._zenoh.workspace(self._recognize_selector + self._camera_id + '/')
		print("\n[*] Declaring Subscriber on '{}'...".format(self._recognize_selector + self._camera_id + '/result'))
		subid = self._wk.subscribe(self._recognize_selector + self._camera_id + '/result', self.result_listener)
	def result_listener(self,changes):
		print("\n[*] Receiving a recognized image !")
		for change in changes:
			path = change.get_path()
			image = change.get_value()
			if image is None:
				return
			image_array = np.fromstring(bytes(image.get_value()),dtype=np.uint8)
			self._decoded_image = cv2.imdecode(image_array,1)
			cv2.imshow('Received Images', self._decoded_image)
			if cv2.waitKey(1) & 0xFF == ord("q"):
				sys.exit(0)

	def send(self,video):
		if self._zenoh == None:
			self.create_zenoh()
		print('\n[*] Sending an image to ',self._recognize_selector + self._camera_id)
		encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
		is_success, im_buf_arr = cv2.imencode(".jpeg", frame, encode_param)
		im_buf_str = im_buf_arr.tobytes()
		self._wk.put(self._recognize_selector + self._camera_id, Value(im_buf_str, Encoding.RAW))
		#time.sleep(0.005)
def Manipulate(img):
	scale_percent = 30
	width = int(img.shape[1] * scale_percent / 100)
	height = int(img.shape[0] * scale_percent / 100)
	dim = (width, height)
	return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)


def Arg_Parse():
	Arg_Par = arg.ArgumentParser(prog='recognize_client',
		description='A process that takes images from a webcam for sending it to the server')
	Arg_Par.add_argument('--recognize_selector', '-rs',
		default='/recognition/',
		type=str,
		help='The selector representing the URI for recognizing images')
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
	return [arg_list['recognize_selector'],arg_list['locator'],arg_list['video'],arg_list['camera']]	

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print("Please Provide an argument !!!")
		sys.exit(0)
	recognize_selector,locator,video,cam_id= Arg_Parse()
	Zenoh_Object = Zenoh_Object(recognize_selector,locator)
	print(video)
	if video != None :
		video = cv2.VideoCapture(video)
		video.set(3, 640)
		video.set(4, 480)
		while True:
			#start = time.start()
			fps = video.get(cv2.CAP_PROP_FPS)
			ret, img = video.read()
			if img is None:
				break
			frame = Manipulate(img)
			Zenoh_Object.frame = frame
			Zenoh_Object.send(frame)
	if cam_id != None :
		camera = cv2.VideoCapture(eval(cam_id))
		camera.set(3, 640)
		camera.set(4, 480)
		while True:
			#start = time.start()
			#fps = video.get(cv2.CAP_PROP_FPS)
			ret, img = camera.read()
			if img is None:
				break
			frame = Manipulate(img)
			#cv2.imshow('frame', frame)
			#if cv2.waitKey(0) & 0xFF == ord("q"):
			#	sys.exit(0)
			Zenoh_Object.frame = frame
			Zenoh_Object.send(frame)
			#time.sleep(1/fps)
