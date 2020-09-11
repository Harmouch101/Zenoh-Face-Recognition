import sys
from zenoh import Zenoh,Encoding, Value
from threading import Thread
import cv2
import numpy as np
import argparse as arg
import warnings
import os
import time
class Recognizer():
	def __init__(self,file_path,cascade_path,names):
		self._Rec = cv2.face.LBPHFaceRecognizer_create()
		self._Rec.read(file_path) 
		self._Face_Cascade = cv2.CascadeClassifier(cascade_path)
		self._Names = names

	def Recognize(self,img):
		if img is None: 
			return -1
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		faces = self._Face_Cascade.detectMultiScale(gray,scaleFactor=1.3,minNeighbors=5,minSize=(20, 20),)
		for _,face in enumerate(faces):
			x,y,w,h = face
			self.Draw_Rect(img, face)
			id_, conf = self._Rec.predict(gray[y:y + h, x:x + w])
			if (conf < 100):
				self.DispID(face, self.Get_UserName(id_, 100 - conf), img)
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
		try :
			if not ID > 0:
				return " Face Not Recognised "
			return "Name: " + self._Names[ID - 1] +"; confidence: " + (str(round(conf)) )  
		except :
			return " Face Not Recognised "        

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
			id_ = int (os.path.split (imagePath) [- 1] .split ( "." ) [1])
			faceSamples.append (img_numpy)
			ids.append (id_)
		return faceSamples, ids
	def train(self,names):
		path = 'dataset/'
		faces, ids = self.getImagesAndLabels (path)
		self.recognizer.train (faces, np.array (ids))
		# Saving the model
		print("\n[*] Creating a training model")
		self.recognizer.write ( 'trainer.yaml' )
		print("\n[*] {0} Persons has been trained successfully.".format (len (np.unique (ids))))
		print("\n[*] Exiting the Training Phase")

class Zenoh_Object():
	def __init__(self,train_selector,recognize_selector,locator):
		self._train_selector = train_selector
		self._recognize_selector = recognize_selector
		self._locator = locator
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._storages = None
		self._trainer = Trainer('haarcascade_frontalface_default.xml')
		#self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml') 
		self._zenoh_admin = None
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._wk3 = None
		self._names = []
		self._counts = []
		try:
			z = Zenoh.login(None)
			w = z.workspace()
			for data in w.get('/known_face/*'):
				buff_ascii = np.frombuffer(data.value.get_value(),dtype=np.uint8)
				self._names = list(''.join(map(chr,buff_ascii)).split(","))
				print('\n[*] Getting Names : {} from storage : /known_face/* '.format(self._names))
			z.logout()
			if len(self._names) == 0:
				print('\n[*] Please train your model !!!')
			name_len = len(self._names)
			self._counts = [50 for i in range(name_len)]	
			self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml',self._names)
		except:
			pass
	def start(self):
		print("\n[*] Creating a Zenoh object(locator={})".format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		self._zenoh_admin = self._zenoh.admin()
		self._storages = self._zenoh_admin.get_storages(beid=None, zid=self._zenoh_admin.local)
		if len(self._storages) == 0 :
			print('\n[*] Add storage with id = {} and selector = {} '.format('names', '/known_face/ID'))
			self._zenoh_admin.add_storage('names', {'selector': '/known_face/ID'})
		print('\n[*] Use Workspace on "{}" to train the model'.format(self._train_selector[:-1]))
		print('\n[*] Use Workspace on "{}" to recognize images'.format(self._recognize_selector[:-1]))
		print('\n[*] Use Workspace on "/known_face/" to store users names')
		self._wk1= self._zenoh.workspace(self._train_selector[:-1])
		self._wk2 = self._zenoh.workspace(self._recognize_selector[:-1])
		self._wk3 = self._zenoh.workspace('/known_face/')
		print("\n[*] Declaring Subscriber on '{}'...".format(self._train_selector))
		print("\n[*] Declaring Subscriber on '{}'...".format(self._recognize_selector))
		subid1 = self._wk1.subscribe(self._train_selector, self.train_listener)
		subid2 = self._wk2.subscribe(self._recognize_selector, self.recognize_listener)
		print("\n[*] Waiting for a new client to connect...")
		while True:
			pass
	def recognize_listener(self,changes):
		if len(self._names) == 0:
			print('\n[*] Please train your model !!!')
			return
		print("\n[*] Receiving a new image for recognition !")
		for change in changes:
			path = change.get_path()
			image = change.get_value()
			if image is None:
				return
			image_array = np.frombuffer(image.get_value(),dtype=np.uint8)
			decoded_image = cv2.imdecode(image_array,1)
			Rec_Img = self._recognizer.Recognize(decoded_image)
			s_success, im_buf_arr = cv2.imencode(".jpg", Rec_Img, self._enc_param)
			im_buf_bytes = im_buf_arr.tobytes()
			self._wk2.put(path + "/result", Value(im_buf_bytes, Encoding.RAW))
			print("\n[*] Sending Recognized Image!")
	def train_listener(self,changes):
		for change in changes:
			image = change.get_value()
			if image is None:
				return
			image_array = np.frombuffer(image.get_value(),dtype=np.uint8)
			decoded_image = cv2.imdecode(image_array,1)
			gray_face = self._trainer.detect(decoded_image)
			if gray_face is None:
				return
			name  = change.get_path()[change.get_path().rfind('/') + 1 : ]
			if name not in self._names:
				self._names.append(name)
				self._counts.append(0)
			name_index = self._names.index(name)
			self._counts[name_index] += 1
			cv2.imwrite("dataset/User." + str(name_index + 1) + '.' + str(self._counts[name_index]) + ".jpg " ,gray_face)
			print("\n[*] Receiving image number ",self._counts[name_index])
			if self._counts[name_index] == 50:
				print("\n[*] Training phase for {} has been started, , please wait a moment...".format(name))
				self._trainer.train(self._names)
				self._recognizer = Recognizer('trainer.yaml','haarcascade_frontalface_default.xml',self._names)
				# split names array with ,
				separated_names = ",".join(self._names)
				self._wk3.put("/known_face/ID",Value(bytes(separated_names,'utf-8'), Encoding.RAW))
				print("\n[*] Waiting for a client to connect...")

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
	train_selector,recognize_selector,locator = Arg_Parse()
	Zenoh_Object = Zenoh_Object(train_selector,recognize_selector,locator)
	Zenoh_Object.start()




