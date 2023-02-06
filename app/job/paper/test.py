import judge
import cv2

img=cv2.imread("/home/zh/web/intelligent-school/app/job/paper/paper.png")
cv2.namedWindow("f",cv2.WINDOW_NORMAL)
cv2.imshow("1",img)
cv2.waitKey(0)
ep =judge.open2(img,"/home/zh/web/intelligent-school/app/job/paper/test.jpg")
dst = judge.paper_ajust(img,ep)
split=judge.paper_split(dst,30,[56,70])
cv2.imshow("2",split[0])
cv2.waitKey(0)
cv2.imshow("3",split[1])
cv2.waitKey(0)
cv2.destroyAllWindows()