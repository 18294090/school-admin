import judge
import cv2
import os
n=1
img=judge.open_answer_card(os.path.join(os.getcwd(),"app",'job','paper','1.png'))
for  dirpath, dirnames, filenames in os.walk(os.path.join(os.getcwd(),"app","static","job",'abnormal_paper','12')): #遍历答题卷文件夹阅卷
    for filepath in filenames:
        print(filepath)
        n+=1        
        ep=judge.open_student_card(os.path.join(dirpath, filepath))
        ep=judge.paper_ajust(img,ep)
        messeage=judge.qr_recognize(ep,(judge.n*15,judge.n*37,judge.n*68,judge.n*82))
        print(messeage)
        if n==10:
            break 