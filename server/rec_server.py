import sys
from zenoh import Zenoh
from zenoh.net import SubscriberMode
import cv2
import numpy as np
import argparse as arg
import warnings
class Recongnizer():
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

	def Recon(self,img):
		if img is None: 
			return -1
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		faces = self._Face_Cascade.detectMultiScale(gray,scaleFactor=1.3,minNeighbors=5,minSize=(20, 20),)
		for _,face in enumerate(faces):
			x,y,w,h = face
			self.Draw_Rect(img, face)
			id, conf = self._Rec.predict(gray[y:y + h, x:x + w])
			if (conf < 100):
				self.DispID(face, self.Get_UserName(id, 100 - conf), img)
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

class Zenoh_Obj():
	def __init__(self,path1,path2,locator):
		self._path1 = path1
		self._path2 = path2
		self._locator = locator
		self._zenoh = None
		self._wk1 = None
		self._wk2 = None
		self._enc_param = [int(cv2.IMWRITE_JPEG_QUALITY),90]
		self._Rec = Recongnizer('trainer.yml','haarcascade_frontalface_default.xml')
	def crt(self):
		print('Creating a Zenoh object(locator={})...'.format(self._locator))
		self._zenoh = Zenoh.login(self._locator)
		print('Use Workspace on "{}" to get an image'.format(self._path1[:-2]))
		print('Use Workspace on "{}" to send an image'.format(self._path2[:-2]))
		self._wk1= self._zenoh.workspace(self._path1[:-2])
		self._wk2 = self._zenoh.workspace(self._path2[:-2])
		print("Declaring Subscriber on '{}'...".format(self._path1))
		sub = self._wk1.rt.declare_subscriber(self._path1, SubscriberMode.push(), self.listener)
		c = ''
		while c != 'q':
			c = sys.stdin.read(1)

	def listener(self,rname, data, info):
		self.Get_Snd_Img(data)

	def Get_Snd_Img(self,data):
		np_img = np.fromstring(data,dtype=np.uint8)
		Img_Dec=cv2.imdecode(np_img,1)
		Rec_Img = self._Rec.Recon(Img_Dec)
		is_success, im_buf_arr = cv2.imencode(".jpg", Rec_Img, self._enc_param)
		im_buf_str = im_buf_arr.tostring()
		self._wk2.rt.write_data(self._path2[:-2] + 'get_img', im_buf_str)


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

	slt1 = '/Face/Recognition/send_image/**'
	slt2 = '/Face/Recognition/get_image/**'
	str_id1 = 'snd_img'
	str_id2 = 'get_img'
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
	if len(storages) == 2 :
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




