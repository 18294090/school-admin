#coding=utf-8
#基本宽度单位(n)为一个六号字符的高度（2.56mm），A4为宽度为210mm,82个字符，高度290mm，116个字符。

from PIL import Image, ImageDraw, ImageFont
import math
import qrcode
import time
import os
f_url=os.getcwd()+"/app/job/paper/font/simsun.ttc"
#产生二维码和答题卷模板，将二维码贴到答题卷上，二维码内容为作业的学科，名称，布置教师
# width 为试卷宽度，message为二维码信息,pic为image对象,pos为二维码在答题卷上的放置位置,元组结构（x，y）,n1为二维码宽度，单位为像素，返回一个pillow对象
#x,y为绘图点指针，默认初始绘图点为n*7,n*30
def qr_paste(message,pic,pos,n1):
    qr=qrcode.make(message)    
    qr=qr.resize((n1,n1))
    pic.paste(qr,pos)
    return(pos)

def genarate_papaer(width):  #生成试卷，width为宽度，高度为宽度的2的1/2次方
    height=int(width*math.sqrt(2))  
    paper = Image.new("RGB",(width,height),"white")
    draw=ImageDraw.Draw(paper)
    n=int(paper.width/82) 
    draw.rectangle((n*2,n*2,n*4,n*4),fill = 0  )    
    draw.rectangle([width-n*4,n*2,width-n*2,n*4],fill=0)
    draw.rectangle([n*2,height-n*4,n*4,height-n*2],fill=0)
    draw.rectangle([width-n*4,height-n*4,width-n*2,height-n*2],fill=0)    
    return paper


def genarate_select(n,n1,pic,x,y): #生成选择题，n1为题目数量，pic为试卷模板，pos为第一题位置
    font=ImageFont.truetype(f_url, int(n*1.5))   
    char=["[ A ]","[ B ]","[ C ]","[ D ]"]
    draw=ImageDraw.Draw(pic)    
    draw.text((x,y),"一、选择题",fill="#000000",font=font)
    y+=3*n
    font=ImageFont.truetype(f_url, n)
    end=y+(n1//4+1)*(n*2) 
    draw.rectangle([x-n,y-n,pic.width-n*5,end],width=2,outline="#000000")
    pos=[]
    for i in range(n1):
        draw.text((x,y),str(i+1)+".",fill="#000000",font=font)
        x+=2*n
        for j in range(4):
            draw.text((x,y),char[j],fill="#000000",font=font)
            x+=3*n                        
        x+=n
        if (i+1)%4==0:
            y+=2*n
            x=n*7
    return([end,n1]) 

def generate_completion(n,pic,list,x,y,n1): #生成填空题，list为二维列表，存储每个小题几个空[[1,2],[1,1,1]],x,y 为位置，n1为题号
    line=[]
    flag=True
    draw=ImageDraw.Draw(pic)
    font=ImageFont.truetype(f_url, int(n*1.5))
    draw.text((x,y),"二、填空题",fill="#000000",font=font)
    y+=3*n
    draw.rectangle([x,y,pic.width-n*5,pic.height-n*5],width=2,outline="#000000")
    line.append(y//n)
    y+=3*n
    font=ImageFont.truetype(f_url, int(n*1.3))
    x+=n
    for i in range(len(list)):
        if (pic.height-y)<(len(list[i])+1)*3*n :
            break
        draw.text((x,y),str(n1)+".",fill=0,font=font)        
        x+=2*n
        y+=2*n
        pos=[]
        for j in range(len(list[i].split())):
            draw.text((x,y),"("+str(j+1)+")",fill=0,font=font)            
            x+=2*n
            for k in range(int(list[i].split()[j])):
                if x>pic.width-n*20:
                    x=n*11
                    y+=3*n
                draw.text((x,y),"____________________",fill=0,font=font)                
                x+=16*n
            y+=3*n
            x=9*n
        x=n*7
        draw.line((x-n,y,pic.width-5*n,y),fill="#000000",width=2)
        if y//n>114:
            flag=False
        else:
            line.append(y//n)
            y+=2*n
            n1+=1
    return(line,flag)

def number_area(n,pic,x,y,n1): #产生学号填涂区，pic为image对象，x,y 为填涂区左上角顶点坐标，n1为号码个数
    draw=ImageDraw.Draw(pic)    
    font=ImageFont.truetype(f_url, n*2)
    draw.text((x+n*n1*4//2-3*n,y+n//2),"学  号",fill=0,font=font)
    for i in range(5):
        draw.rectangle((x,y+7*n+n*4*i-n//2,x+n*n1*4,y+7*n+n*4*i+n+n//2),fill="#f6f6f6")
        pass
    draw.line((x,y+3*n,x+n*n1*4,y+3*n),fill="#000000",width=2)
    draw.line((x,y+6*n+n//2,x+n*n1*4,y+6*n+n//2),fill="#000000",width=2)
    font=ImageFont.truetype(f_url, n)   
    for i in range(n1):
        draw.line((x+i*n*4,y+3*n,x+i*n*4,n*36),width=2,fill="#000000")
        for j in range(10):            
            draw.text((x+n+i*n*4,y+7*n+j*2*n),"[ "+str(j)+" ] ",fill="#000000",font=font)
    draw.rectangle([x,y,x+n*n1*4,n*36],width=2,outline="#000000")
    return

def paper(subject,teacher,width,title,s_n,complete):
    paper=genarate_papaer(width)
    n=paper.width//82
    d=ImageDraw.Draw(paper)    
    x=n*7
    y=n*40
    font=ImageFont.truetype(f_url, n*3)
    d.text(((paper.width-n*3*len(title))//2,n*5),title,fill=0,font=font)
    pos=genarate_select(n,s_n,paper,x,y)
    flag=True
    if len(complete):
        line,flag = generate_completion(n,paper,complete,n*6,pos[0]+n*2,pos[1]+1)
    else:
        line=[]
    img=Image.open(os.getcwd()+"/app/job/paper/pic/"+"name.png")
    img=img.convert('L')
    name_width=n*20
    img=img.resize((name_width,27*n))
    paper.paste(img,(n*6,n*9))
    number_area(n,paper,n*27,n*9,10)
    qr_paste(subject+"-"+title+"-"+teacher,paper,(paper.width-n*16,n*15),n*12)
    p_name=os.getcwd()+"/app/static/paper/excercise/"+teacher+"-"+str(time.time())+".png"
    return((line,paper,flag))
