import judge
import cv2
import os
n=1
img=judge.open(os.path.join(os.getcwd(),"app",'job','paper','1.png'))
for  dirpath, dirnames, filenames in os.walk(os.path.join(os.getcwd(),"app","static",'answer','5')): #遍历答题卷文件夹阅卷
    for filepath in filenames:
        print(filepath)
        n+=1        
        ep=judge.open2(os.path.join(dirpath, filepath))
        ep=judge.paper_ajust(img,ep)
        split=judge.paper_split(ep,11,[70,80])
        s=judge.check_select(split[1],8)
        s = {k: s[k] for k in sorted(s)}
        number=judge.number_pos(split[0])        
        print(number,s)
        """if n==10:
            break"""  