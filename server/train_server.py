import sys
from zenoh import Zenoh
from zenoh.net import SubscriberMode
import cv2
import numpy as np
import argparse as arg
import warnings
import os
import time
class Recongnizer():
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
		print ( "\n [INFO] Face training, wait ..." )
		faces, ids = self.getImagesAndLabels (path)
		self.recognizer.train (faces, np.array (ids))
		# Saving the model
		self.recognizer.write ( 'trainer.yml' )
		print ( "\n [INFO] {0} persons trained. Exiting the program ".format (len (np.unique (ids))))
		print("\n [INFO] Quitting the program")

	def Get_UserName(self,ID, conf):
		if not ID > 0:
			return " Face Not Recognised "
		return "Name: " + self.FileRead()[ID -1] +"; confidence: " + (str(round(conf)) )          

class Zenoh_Obj():
	def __init__(self,path1,path2,locator):
		self._path1 = path1
		self._path2 = path2
		self._locator = locator
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._Rec = Recongnizer('haarcascade_frontalface_default.xml')
		self.face_id = 0
		self.Name = ''
		self.count = 0
		self._bool = False
	def crt(self):
		print('Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('Use Workspace on "{}" to get an image'.format(self._path1[:-2]))
		print('Use Workspace on "{}" get a name'.format(self._path2[:-2]))
		self._wk1= self._zenoh.workspace(self._path1[:-2])
		self._wk2 = self._zenoh.workspace(self._path2[:-2])
		print("Declaring Subscriber on '{}'...".format(self._path1))
		print("Declaring Subscriber on '{}'...".format(self._path2))
		sub1 = self._wk1.rt.declare_subscriber(self._path1, SubscriberMode.push(), self.listener1)
		sub2 = self._wk2.rt.declare_subscriber(self._path2, SubscriberMode.push(), self.listener2)
		while True:
			pass

			

	def listener1(self,rname, data, info):
		self.Get_Img(data)
	def listener2(self,rname, data, info):
		self.Get_Id(data)

	def Get_Img(self,data):
		if data is None:
			return
		np_img = np.fromstring(data,dtype=np.uint8)
		Img_Dec=cv2.imdecode(np_img,1)
		gray_face = self._Rec.detect(Img_Dec)
		if gray_face is None:
			return
		cv2.imwrite("dataset/User." + str(self.face_id) + '.' + str(self.count) + ".jpg " ,gray_face)
		self.count += 1
		self._wk2.rt.write_data(self._path2[:-2] + 'id_img', str(self.count).encode())
		if self.count == 50:
			self._Rec.train()
			self._zenoh.logout()
			cv2.destroyAllWindows()
			sys.exit(0)

	def Get_Id(self,data):
		if self._bool == True:
			return
		self.Name = str(data.decode())
		self.face_id = self.Add_User(self.Name)
		self._bool = True

	def Add_User(self,Name):
		Info = open("users_name.txt", "a+")
		ID = len(open("users_name.txt").readlines(  )) + 1
		Info.write(str(ID) + "," + Name + "\n")
		print ("Name Stored in " + str(ID))
		Info.close()
		return ID


def Arg_Parse():
	Arg_Par = arg.ArgumentParser()
	Arg_Par.add_argument("-s1", "--storage1",
					help = "selector(path) for storage1")
	Arg_Par.add_argument("-s2", "--storage2",
					help = "selector(path) for storage2")
	Arg_Par.add_argument("-id1", "--str_id1",
					help = "id for storage1")
	Arg_Par.add_argument("-id2", "--str_id2",
					help = "id for storage2")	
	Arg_Par.add_argument("-l", "--locator",
					help = "give a locator 'tcp/ip-add:port' like 'tcp/192.168.0.1:9999'")
	arg_list = vars(Arg_Par.parse_args())
	return arg_list

def crt_znh_strs(arg_list):

	slt1 = '/Face/Recognition/train_image/**'
	slt2 = '/Face/Recognition/id_image/**'
	str_id1 = 'train_img'
	str_id2 = 'id_img'
	locator = 'tcp/127.0.0.1:7447'

	if arg_list["storage1"] != None:
		slt1 = arg_list["storage1"]
	if arg_list["storage2"] != None:
		slt2 = arg_list["storage2"]
	if arg_list["str_id1"] != None:
		str_id1 = arg_list["str_id1"]
	if arg_list["str_id2"] != None:
		str_id2 = arg_list["str_id2"]
	if arg_list["locator"] != None:
		locator = arg_list["locator"]

	print('Creating a Zenoh object(locator={})...'.format(locator))
	z = Zenoh.login(locator)
	a = z.admin()
	storages = a.get_storages(beid=None, zid=a.local)
	print(len(storages))
	if len(storages) == 0 :
		print('Adding storage with id {} and selector {} '.format(str_id1, slt1))
		print('Adding storage with id {} and selector {} '.format(str_id2, slt2))
		prop1 = {'selector': slt1}
		prop2 = {'selector': slt2}
		a.add_storage(str_id1, prop1)
		a.add_storage(str_id2, prop2)
	print("peer id =",a.local)
	z.logout()
	return slt1,slt2,locator



if __name__ == "__main__":
	'''
	if len(sys.argv) == 1:
		print("Please Provide an argument !!!")
		sys.exit(0)
	'''
	warnings.simplefilter("ignore", DeprecationWarning)
	Arg_list = Arg_Parse()
	slt1,slt2,loc = crt_znh_strs(Arg_list)
	zen_obj = Zenoh_Obj(slt1,slt2,loc)
	zen_obj.crt()




