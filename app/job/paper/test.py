import judge
import cv2

img=cv2.imread("/home/zh/web/intelligent-school/app/job/paper/paper.png")
cv2.namedWindow("f",cv2.WINDOW_NORMAL)

ep =judge.open2(img,"/home/zh/web/intelligent-school/app/job/paper/test.jpg")
dst = judge.paper_ajust(img,ep)
split=judge.paper_split(dst,30,[65,80])
number=judge.number_pos(split[0])
print(number)
