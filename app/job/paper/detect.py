#检测图片中的A4纸并矫正，图片来源为扫描仪扫描或者手机拍摄若为手机拍摄，则需要将图片中的A4纸找出并矫正为A4纸的正常比例
import cv2
import numpy as np
import os
def order_points(pts):
    # 根据x坐标对点进行排序
    xSorted = pts[np.argsort(pts[:, 0]), :]
    # 获取最左边和最右边的点
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]
    # 现在，根据y坐标对最左边的点进行排序，以获取左上角和左下角的点
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost
    # 现在我们有了左上角和左下角的点，我们需要计算右上角和右下角的点
    # 我们可以利用欧氏距离来计算这两个点
    D = np.linalg.norm(rightMost - bl, axis=1)
    rightMost = rightMost[np.argsort(D)[::-1], :]
    (br, tr) = rightMost[0], rightMost[1]
    # 确保输出的点总是按照左上、右上、右下、左下的顺序排列
    if tl[1] > bl[1]: tl, bl = bl, tl
    if tr[1] > br[1]: tr, br = br, tr
    # 返回排序后的点
    return np.array([tl, tr, br, bl], dtype="float32")

def find_paper(img):    
    h, w = img.shape[:2] 
    # 检查图像的宽高比
    ratio = w / h
    if ratio > 1:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        h, w = img.shape[:2]
    chWidth=w//82
    #计算图像边缘一圈的像素平均值，若大于100则为A4纸   
    if (np.mean(img[:10, :w])+np.mean(img[h-10:h,:w])+np.mean(img[10:h-10,:10])+np.mean(img[w-10,w-10:w]))/4 > 150:
        print('扫描件')
        return 1,img
    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 对图像进行模糊处理
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    #腐蚀
    gray = cv2.erode(gray, None, iterations=3)    
    #膨胀
    gray = cv2.dilate(gray, None, iterations=3)  
    # 使用 Canny 边缘检测
    edges = cv2.Canny(gray, 50, 150)
    # 找到边缘的轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 找到最大的轮廓
    if len(contours) == 0:
        print('找不到答题卡.')
        return 2,None
    max_contour = max(contours, key=cv2.contourArea)
    #判断轮廓是否为矩形，且面积是否大于图片面积的1/3
    if len(max_contour) < 4 or cv2.contourArea(max_contour) < w * h *2/ 3:
        print('找不到答题卡.')
        return 2,None

    # 使用多边形逼近找到轮廓的四个角点
    epsilon = 0.02 * cv2.arcLength(max_contour, True)
    approx = cv2.approxPolyDP(max_contour, epsilon, True)
    # 使用透视变换进行矫正，保证长边和短边保持正常比例
    try:
        pts1 = order_points(approx.squeeze())
    except Exception as e:
        print(e)
        return 2,None
    pts2 = np.array([[0, 0], [2100, 0], [2100, 2970], [0, 2970]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(img, M, (2100, 2970))
    

    #判断是纸张，判断依据为纸张边缘一圈是否基本为白色
    if (np.mean(img[:10, :w])+np.mean(img[h-10:h,:w])+np.mean(img[10:h-10,:10])+np.mean(img[w-10,w-10:w]))/4>150:
        print('找到答题卡')
        return 1,dst
    else:
       
        return 2,None

#遍历文件夹下和子文件夹的所有图片
def get_file(file_path):
    n=0
    n1=0 
    for root, dirs, files in os.walk(file_path):
        for file in files:
            n1+=1
            if file.endswith('.jpg') or file.endswith('.png'):
               print(find_paper(os.path.join(root, file))[0])
               n+=1
    return n,n1


#print(get_file("C:/Users/Administrator/Desktop/detect"))
