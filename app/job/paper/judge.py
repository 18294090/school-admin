from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from pyzbar import pyzbar
line=[]
n=0
def open(url1):
    global n
    img=cv2.imread(url1)
    n=img.shape[1]//82   
    return(img)

def open2(url):
    global n
    img=cv2.imread(url)
    img=img[n*2:-n*2,n*2:-n*2]
    return(img)

def qr(img):#读取识别二维码
    global n
    if len(img.shape)!=2:
        pic = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    
    pic=pic[n*15:n*27,n*68:n*79]
    qr_code_blur = cv2.GaussianBlur(pic, (5, 5), 0)
    # 填充空洞
    qr_code_dilate = cv2.dilate(qr_code_blur, None, iterations=1)
    pic = cv2.erode(qr_code_dilate, None, iterations=1)
    barcodes =""
    barcodes = pyzbar.decode(pic)    
    barcodeData=[]
    for barcode in barcodes:
        barcodeData.append(barcode.data.decode('utf-8'))  # 二进制类型转成字符串
    return(barcodeData)

def pict(gray):  # 图像处理，二值化
    if len(gray.shape)!=2:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)      
    # 图像二值化处理，将灰度图转换为二值图
    # 二值化处理
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    binary_erosion =cv2.erode(thresh, kernel,iterations=2)#腐蚀
    binary_dilation =cv2.dilate(binary_erosion, kernel,iterations=4)    
    # 形态学操作，去除噪点和细节，填充小的白色区域
    opening = cv2.morphologyEx(binary_dilation, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    return(closing)

 
def paper_ajust(original_image, target_image):
    # 查找原图像和目标图像中的四个黑色方块的位置
    original_corners = find_corners(original_image)
    target_corners = find_corners(target_image)
    # 获取仿射变换矩阵
    M = cv2.getPerspectiveTransform(target_corners, original_corners)
    # 应用仿射变换矩阵对目标图像进行变换，实现矫正
    adjusted_image = cv2.warpPerspective(target_image, M, (original_image.shape[1], original_image.shape[0]))
    
    return adjusted_image

def find_corners(img):
    # 转换为灰度图像
    if len(img.shape)!=2:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    
    # 二值化处理
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # 形态学操作，去除噪点和细节，填充小的白色区域
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    binary_dilation =cv2.dilate(thresh, kernel)
    binary_erosion =cv2.erode(binary_dilation , kernel,iterations=1)     
    opening = cv2.morphologyEx(binary_erosion, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    # 查找轮廓
    contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)    
    # 计算轮廓的质心，即中心点
    centers = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area>1800:
            M = cv2.moments(cnt)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            centers.append((cx, cy))
    # 确定四个黑色方块的中心点
    top_left = min(centers, key=lambda x: x[0] + x[1])
    bottom_right = max(centers, key=lambda x: x[0] + x[1])
    top_right = max(centers, key=lambda x: x[0] - x[1])
    bottom_left = min(centers, key=lambda x: x[0] - x[1])
    return(np.array([top_left,bottom_right,top_right,bottom_left],dtype=np.float32))

def number_pos(pic): #识别号码
    img=pict(pic)
    
    cnts,h=cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)    
    pnt1=[]
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        
        if area>500:
            
            M = cv2.moments(cnt)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            pnt1.append((cx, cy))
    
    result=""
    
    pnt1.sort(key=lambda x:x[0])
    if len(pnt1)==10:        
        for i in pnt1:
            result+=str((i[1]//n)//2)
    else:
        print(len(pnt1))
        return("图像错误")
    return(result)

#矫正完成后，对画面进行切割，分别切割出考号填涂区，选择题区，和非选择题区
def paper_split(dst,s_n,line):
    num=dst[16*n:36*n,27*n:67*n]
    select=dst[43*n:43*n+(s_n+3)//4*2*n,6*n:77*n]
    c=[]
    for i in range(len(line)-1):
        c.append(dst[line[i]*n:line[i+1]*n,n*6:n*70])
    return(num,select,c)

def check_select(dst,m): #选择题阅卷，返回一个字典，{题目序号：选项} 
    pnt1=[]
    pnt={}
    #如果dst为空图像，返回一个空字典
    if dst.shape[0]==0:
        return(pnt)    
    s=pict(dst)
    cnts,h=cv2.findContours(s, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    """dst=cv2.drawContours(dst, cnts, -1, (0, 0, 255), 3)
    cv2.namedWindow("2",cv2.WINDOW_NORMAL)
    cv2.imshow("2",dst)
    cv2.waitKey(0)
    cv2.destroyAllWindows()"""
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area>1000:
            M = cv2.moments(cnt)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            pnt1.append((cx, cy))
    
    ans=["A","B","C","D"]
    for i in pnt1:
        row=int((i[1]//n+1)/2)
        col=(i[0]//n-1)
        order=(row)*4+col//15+1
        if order>m:
            continue
        s=(col%15-2)//3
        if s<=3:
            if order in pnt:
                pnt[order]+=ans[s]
            else:
                pnt[order]=ans[s]
        else:
            pass
    return(pnt)
