from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from pyzbar import pyzbar
line=[]

def open(url1):
    img=cv2.imread(url1)
    return(img)
def open2(img,url2):
    ep=cv2.imread(url2)
    ep=cv2.resize(ep,(img.shape[1],img.shape[0]))
    return(ep)

n=2000//82

def qr(img):#读取识别二维码
    pic=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pic=pic[n*15:n*27,n*67:n*79]
    barcodes = pyzbar.decode(pic)
    barcodeData=[]
    for barcode in barcodes:
        barcodeData.append(barcode.data.decode('utf-8'))  # 二进制类型转成字符串
    return(barcodeData)

def pict(t):  # 图像处理，二值化
    img = cv2.cvtColor(t, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((10, 10), np.float32)/50
    mohu = cv2.filter2D(img, -1, kernel)
    mohu = cv2.GaussianBlur(mohu, (5, 5), 0)
    dst = cv2.erode(mohu, kernel, iterations=1)
    dst = cv2.dilate(dst, kernel, iterations=1)
    ret, color2 = cv2.threshold(dst,200, 255, cv2.THRESH_BINARY_INV)
    color2 = cv2.dilate(color2, kernel, iterations=1)
    return(color2)

#根据两张图片的四个顶点pts1，pts2，进行图像矫正对齐,ep为扫描卷，img为试卷原图，pts1为扫描卷顶点，pts为原图顶点，返回值为cv2的image对象
def position_correction(ep,img,pts1,pts):  
    M = cv2.getPerspectiveTransform(pts1,pts)
    dst = cv2.warpPerspective(ep,M,(img.shape[1],img.shape[0]))
    return dst

#二值化试卷和扫描卷，对扫描卷进行位置矫正
def paper_ajust(img,ep):
    pic=pict(img)
    test=pict(ep)
    pic = cv2.Canny(pic,10,100)
    test = cv2.Canny(test,10,100)
    contours,h1=cv2.findContours(pic, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    epcontours,h2=cv2.findContours(test, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    p = [cv2.moments(contours[-1]),cv2.moments(contours[-2]),cv2.moments(contours[1]),cv2.moments(contours[0])] #获取四个角的轮廓的矩，用来获取轮廓中心点
    pts=[]  #查找四个角的轮廓的中心点
    for M in p:  
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        pts.append((cX,cY))
    p= [cv2.moments(epcontours[-1]),cv2.moments(epcontours[-2]),cv2.moments(epcontours[1]),cv2.moments(epcontours[0])]
    pts1=[]
    for M in p: 
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        pts1.append((cX,cY))

    def find_points(pts): #查找四个顶点，pts为存储有四个点坐标的列表,返回值为一个列表，分别存储左上角，右上角，左下角，右下角坐标
        pts.sort()
        if pts[0][1]<pts[1][1]:
            p1=pts[0]
            p3=pts[1]
        else:
            p1,p3=pts[1],pts[0]
        if pts[2][1]<pts[3][1]:
            p2,p4=pts[2],pts[3]
        else:
            p2,p4=pts[3],pts[2]
        return np.float32([p1,p2,p3,p4])

    pts=find_points(pts)
    pts1=find_points(pts1)
    dst=position_correction(ep,img,pts1,pts)
    return dst



def number_pos(pic): #查找号码定位点
    d=ImageDraw.Draw(pic)
    for i in range(10):
        for j in range(10):
            d.rectangle((28*n+i*n*4,16*n+j*2*n,30*n+n//2+i*n*4,17*n+j*2*n),outline="#00FF00",width=2)

#矫正完成后，对画面进行切割，分别切割出考号填涂区，选择题区，和非选择题区
def paper_split(dst,s_n,line):
    num=dst[9*n:36*n,27*n:67*n]
    select=dst[42*n:42*n+s_n//4*2*n,6*n:77*n]
    c=[]
    for i in range(len(line)-1):
        c.append(dst[line[i]*n:line[i+1]*n,n*6:n*77])
    return(num,select,c)

def check_select(dst): #选择题阅卷，返回一个字典，{题目序号：选项}
    
    s=pict(dst)
    cnts,h=cv2.findContours(s, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pic=cv2.drawContours(dst,cnts,-1,(255,0,0),3)
    pnt=[]
    for i in cnts:
        pnt.append(cv2.moments(i))

    pnt1=[]
    for M in pnt:  
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        pnt1.append((cX,cY))
    pnt={}
    ans=["A","B","C","D"]
    for i in pnt1:
        row=(i[1]//n+1)//2
        col=(i[0]//n-1)
        order=(row-1)*4+col//15+1
        s=(col%15-2)//3
        pnt[order]=ans[s]
    
    return(pnt)


