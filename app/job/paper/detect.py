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
    #判断图像宽高比是否接近A4，以及边缘一圈是否基本为白色 ，若满足条件则视为扫描件   
    if 0.700 <= ratio <= 0.717 and np.mean(img[:10, :10]) > 200:
        print('The image is already A4 paper size.')
        return 0,img
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
    max_contour = max(contours, key=cv2.contourArea)
    # 使用多边形逼近找到轮廓的四个角点
    epsilon = 0.02 * cv2.arcLength(max_contour, True)
    approx = cv2.approxPolyDP(max_contour, epsilon, True)
    # 使用透视变换进行矫正，保证长边和短边保持正常比例
    pts1 = order_points(approx.squeeze())
    pts2 = np.array([[0, 0], [2100, 0], [2100, 2970], [0, 2970]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(img, M, (2100, 2970))
    return 1,dst

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
