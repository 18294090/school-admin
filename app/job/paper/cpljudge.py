import cv2
import pytesseract
import os
import judge
# 读取填空题图像
img=judge.open(os.path.join(os.getcwd(),"app",'job','paper','2.png'))
ep=judge.open2(os.path.join(os.getcwd(),"app",'job','paper','1.jpg'))
ep=judge.paper_ajust(img,ep)
split=judge.paper_split(ep,11,[54,65,78,91])
cpl=split[2][0]
cv2.namedWindow("cpl",cv2.WINDOW_NORMAL)
cv2.imshow("cpl",cpl)
cv2.waitKey(0)
cv2.destroyAllWindows()
# 分割出每个小题的图像区域
# 这里使用简单的方式，假设每个小题的图像区域大小相同，位置也已知
# 实际应用中可能需要使用更复杂的方式来分割图像区域
x1, y1, x2, y2 = (0, 0, 100, 100)  # 假设第一个小题的位置为左上角的100x100的矩形
sub_img = cpl

# 定位每个空的横线位置
gray_img = cv2.cvtColor(sub_img, cv2.COLOR_BGR2GRAY)
_, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
contours, hierarchy = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
lines = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > h:
        lines.append((y, y+h))

# 切割出每个空的图像区域，识别其中的文字
results = []
for i, (y1, y2) in enumerate(lines):
    sub_img = img[y1:y2, x1:x2]
    gray_img = cv2.cvtColor(sub_img, cv2.COLOR_BGR2GRAY)
    _, binary_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(binary_img, lang='chi_sim')
    results.append((i, text))

# 打印每个空的识别结果
for i, text in results:
    print(f"第{i+1}个空的识别结果为：{text}")