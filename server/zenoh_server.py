import sys
from zenoh import Zenoh,Encoding, Value
import cv2
import numpy as np
import argparse as arg
import warnings
import os
import time
class Recognizer():
	def __init__(self,file_path,cascade_path):
		self._Rec = cv2.face.LBPHFaceRecognizer_create()
		self._Rec.read(file_path) 
		self._Face_Cascade = cv2.CascadeClassifier(cascade_path)
		self.Names = self.FileRead()
	def FileRead(self):
		try:
			NAME = []
			with open("users_name.txt", "r") as f :
				for line in f:
					NAME.append(line.split(",")[1].rstrip())
			return NAME
		except:
			print("file users_name.txt does not exist, please train your model !")
			sys.exit(0)

	def Recognize(self,img):
		if img is None: 
			return -1
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		faces = self._Face_Cascade.detectMultiScale(gray,scaleFactor=1.3,minNeighbors=5,minSize=(20, 20),)
		for _,face in enumerate(faces):
			x,y,w,h = face
			self.Draw_Rect(img, face)
			id, conf = self._Rec.predict(gray[y:y + h, x:x + w])
			if (conf < 130):
				self.DispID(face, self.Get_UserName(id, 130 - conf), img)
			else:
				self.DispID(face, self.Get_UserName(0, conf), img)
		return img

	def Draw_Rect(self,Image, face):
		Green = [0,255,0] #[BGR]
		x,y,w,h = face
		cv2.line(Image, (x, y), (int(x + (w/5)),y), Green, 2)
		cv2.line(Image, (int(x+((w/5)*4)), y), (x+w, y), Green, 2)
		cv2.line(Image, (x, y), (x,int(y+(h/5))), Green, 2)
		cv2.line(Image, (x+w, y), (x+w, int(y+(h/5))), Green, 2)
		cv2.line(Image, (x, int(y+(h/5*4))), (x, y+h), Green, 2)
		cv2.line(Image, (x, int(y+h)), (x + int(w/5) ,y+h), Green, 2)
		cv2.line(Image, (x+int((w/5)*4), y+h), (x + w, y + h), Green, 2)
		cv2.line(Image, (x+w, int(y+(h/5*4))), (x+w, y+h), Green, 2)

	def Get_UserName(self,ID, conf):
		if not ID > 0:
			return " Face Not Recognised "
		return "Name: " + self.FileRead()[ID -1] +"; confidence: " + (str(round(conf)) )          

	def DispID(self,face, NAME, Image):
		x, y, w, h = face
		pt1 = (int(x), int(y+h+10))
		pt2 = (int(x + (len(NAME) * 5)),int(y+h+25))
		pt3 = (int(x + 1), int(y+h +(-int(y+h) + int(y+h+25))/2+6))
		cv2.rectangle(Image,pt1, pt2, (255,255,255), -2)          
		cv2.rectangle(Image, pt1, pt2, (0,0,255), 1) 
		cv2.putText(Image, NAME,pt3 , cv2.FONT_HERSHEY_PLAIN, .5, (0,0,0))  

class Trainer():
	def __init__(self,cascade_path):
		self._Face_Cascade = cv2.CascadeClassifier(cascade_path)
		self.path_exists("dataset/")
		self.recognizer = cv2.face.LBPHFaceRecognizer_create()
	def path_exists(self,path):
		dir = os.path.dirname(path)
		if not os.path.exists(dir):
			os.makedirs(dir)
	def detect(self,img):
		if img is None: 
			return -1
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		saved_face = None
		faces = self._Face_Cascade.detectMultiScale(gray,scaleFactor=1.3,minNeighbors=5,minSize=(20, 20),)
		for _,face in enumerate(faces):
			x,y,w,h = face
			saved_face = gray[y:y + h, x:x + w]
		return saved_face
	def getImagesAndLabels(self,path):
		imagePaths = [os.path.join(path,f) for f in os.listdir (path)]
		faceSamples = []
		ids = []
		for imagePath in imagePaths:
			img = cv2.imread(imagePath,0)
			img_numpy = np.array (img, 'uint8' )
			id = int (os.path.split (imagePath) [- 1] .split ( "." ) [1])
			faceSamples.append (img_numpy)
			ids.append (id)
		return faceSamples, ids
	def train(self):
		path = 'dataset/'
		faces, ids = self.getImagesAndLabels (path)
		self.recognizer.train (faces, np.array (ids))
		# Saving the model
		print("\n[*] Creating a training model")
		self.recognizer.write ( 'trainer.yaml' )
		print("\n[*] {0} Persons has been trained successfully.".format (len (np.unique (ids))))
		print("\n[*] Exiting the Training Phase")

	def Get_UserName(self,ID, conf):
		if not ID > 0:
			return " Face Not Recognised "
		return "Name: " + self.FileRead()[ID -1] +"; confidence: " + (str(round(conf)) )          

class Zenoh_Object():
	def __init__(self,train_selector,recognize_selector,locator):
		self._train_selector = train_selector
		self._recognize_selector = recognize_selector
		self._locator = locator
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._trainer = Trainer('haarcascade_frontalface_default.xml')
		try:
			self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml')
		except:
			pass
		#self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml') 
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._face_id = 0
		self._name = ''
		self._count = 0
		self._bool = False
	def start(self):
		print("\n[*] Creating a Zenoh object(locator={})".format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('\n[*] Use Workspace on "{}" to train the model'.format(self._train_selector[:-1]))
		print('\n[*] Use Workspace on "{}" to recognize images'.format(self._recognize_selector[:-1]))
		self._wk1= self._zenoh.workspace(self._train_selector[:-1])
		self._wk2 = self._zenoh.workspace(self._recognize_selector[:-1])
		print("\n[*] Declaring Subscriber on '{}'...".format(self._train_selector))
		print("\n[*] Declaring Subscriber on '{}'...".format(self._recognize_selector))
		subid1 = self._wk1.subscribe(self._train_selector, self.train_listener)
		subid2 = self._wk2.subscribe(self._recognize_selector, self.recognize_listener)
		print("\n[*] Waiting for a new client to connect...")
		while True:
			pass
	def recognize_listener(self,changes):
		print("\n[*] Receiving a new image for recognition !")
		for change in changes:
			path = change.get_path()
			image = change.get_value()
			if image is None:
				return
			image_array = np.fromstring(bytes(image.get_value()),dtype=np.uint8)
			decoded_image = cv2.imdecode(image_array,1)
			Rec_Img = self._recognizer.Recognize(decoded_image)
			s_success, im_buf_arr = cv2.imencode(".jpg", Rec_Img, self._enc_param)
			im_buf_str = im_buf_arr.tobytes()
			self._wk2.put(path + "/result", Value(im_buf_str, Encoding.RAW))
			print("\n[*] Sending Recognized Image!")
	def train_listener(self,changes):
		for change in changes:
			image = change.get_value()
			if image is None:
				return
			image_array = np.fromstring(bytes(image.get_value()),dtype=np.uint8)
			decoded_image = cv2.imdecode(image_array,1)
			gray_face = self._trainer.detect(decoded_image)
			if gray_face is None:
				return
			self._count += 1
			if self._count == 1:
				self._name  = change.get_path()[change.get_path().rfind('/') + 1 : ]
				self.add_user(self._name)
			cv2.imwrite("dataset/User." + str(self._face_id) + '.' + str(self._count) + ".jpg " ,gray_face)
			print("\n[*] Receiving image number ",self._count)
			if self._count == 50:
				print("\n[*] Training phase for {} has been started, , please wait a moment...".format(self._name))
				self._trainer.train()
				self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml')
				self._count = 0
				print("\n[*] Waiting for a client to connect...")

	def add_user(self,name):
		info = open("users_name.txt", "a+")
		ID = len(open("users_name.txt").readlines(  )) + 1
		info.write(str(ID) + "," + name + "\n")
		print ("\n[*] Name '{}' is a stored with ID = '{}' in the users_name.txt file".format(name,ID))
		self._face_id = ID
		info.close()
		return ID


def Arg_Parse():
	Arg_Par = arg.ArgumentParser(prog='server',
		description='A process that takes images from clients to train and recognize purposes')
	Arg_Par.add_argument('--train_selector', '-ts',
		default='/training/*',
		type=str,
		help='The selector specifying the subscription for training images')
	Arg_Par.add_argument('--recognize_selector', '-rs',
		default='/recognition/*',
		type=str,
		help='The selector specifying the subscription for recognize images')
	Arg_Par.add_argument("-l", "--locator",
		default=None,
		type=str,
		help = "The locator to be used to create a zenoh session."
		"'tcp/ip-add:port' like 'tcp/192.168.0.1:9999'"
		"By default dynamic discovery is used")
	arg_list = vars(Arg_Par.parse_args())
	return [arg_list['train_selector'],arg_list['recognize_selector'],arg_list['locator']]	


if __name__ == "__main__":
	'''
	if len(sys.argv) == 1:
		print("Please Provide an argument !!!")
		sys.exit(0)
	'''
	#warnings.simplefilter("ignore", DeprecationWarning)
	train_selector,recognize_selector,locator = Arg_Parse()
	Zenoh_Object = Zenoh_Object(train_selector,recognize_selector,locator)
	Zenoh_Object.start()




