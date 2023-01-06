#coding=utf-8
#基本宽度单位(n)为一个六号字符的高度（2.56mm），A4为高度为210mm,82个字符，高度290mm，116个字符。

from PIL import Image, ImageDraw, ImageFont
import math
import qrcode


#产生二维码和答题卷模板，将二维码贴到答题卷上，二维码内容为作业的学科，名称，布置教师
# width 为试卷宽度，message为二维码信息,pic为image对象,pos为二维码在答题卷上的放置位置,元组结构（x，y）,n为大小基本单位为10，返回一个pillow对象
#x,y为绘图点指针，默认初始绘图点为n*7,n*30
def qr_paste(message,pic,pos,n1):
    qr=qrcode.make(message)
    
    qr=qr.resize((qr.width*n1,qr.width*n1))
    pic.paste(qr,pos)
    return img

bigbox=(150,100)
smallbox=(100,50)

def genarate_papaer(width):  #生成试卷，width为宽度，高度为宽度的2的1/2次方
    height=int(width*math.sqrt(2))  
    paper = Image.new("RGB",(width,height),"white")
    draw=ImageDraw.Draw(paper)
    n=int(paper.width/82)   
    draw.rectangle([n*2,n*2,n*4,n*4],fill=0)
    draw.rectangle([width-n*4,n*2,width-n*2,n*4],fill=0)
    draw.rectangle([n*2,height-n*4,n*4,height-n*2],fill=0)
    draw.rectangle([width-n*4,height-n*4,width-n*2,height-n*2],fill=0)
    paper.save("papaer.png")
    return paper

def genarate_select(n1,pic,x,y): #生成选择题，n1为题目数量，pic为试卷模板，(x,y)为第一题位置
    font=ImageFont.truetype("simsun.ttc", int(n*1.5))   
    char=["[ A ]","[ B ]","[ C ]","[ D ]"]
    draw=ImageDraw.Draw(pic)    
    draw.text((x,y),"一、选择题",fill="#000000",font=font)
    y+=3*n
    font=ImageFont.truetype("simsun.ttc", n)
    end=y+(n1//4+1)*(n*2) 
    draw.rectangle([x-n,y-n,pic.width-n*5,y+(n1//4+1)*(n*2)],width=2,outline="#ff0000")
    for i in range(n1):
        draw.text((x,y),str(i+1)+".",fill="#000000",font=font)
        x+=2*n
        for j in range(4):
            draw.text((x,y),char[j],fill="#ff0000",font=font)
            x+=3*n                        
        x+=n
        if (i+1)%4==0:
            y+=2*n
            x=n*7
    
    return([end,n1]) 

def generate_completion(pic,list,x,y,n1): #生成填空题，list为二维列表，存储每个小题几个空[[1,2],[1,1,1]],x,y 为位置，n1为题号
    draw=ImageDraw.Draw(pic)
    font=ImageFont.truetype("simsun.ttc", int(n*1.5))
    draw.text((x,y),"二、填空题",fill="#000000",font=font)
    draw.text((x+n*50,y),str(y),fill="#000000",font=font)
    y+=3*n
    draw.rectangle([x,y,pic.width-n*5,pic.height-n*5],width=2,outline="#ff0000")
    y+=3*n
    font=ImageFont.truetype("simsun.ttc", int(n*1.3))
    x+=n
    for i in range(len(list)):
        if (pic.height-y)<(len(list[i])+1)*3*n :
            break
        draw.text((x,y),str(n1)+".",fill=0,font=font)
        draw.text((x+n*50,y),str(y),fill="#000000",font=font)
        x+=2*n
        y+=2*n
        for j in range(len(list[i])):
            draw.text((x,y),"("+str(j+1)+")",fill=0,font=font)
            draw.text((x+n*50,y),str(y),fill="#000000",font=font)
            x+=2*n
            for k in range(list[i][j]):
                if x>pic.width-n*20:
                    x=n*11
                    y+=3*n
                draw.text((x,y),"____________________",fill=0,font=font)                
                x+=16*n
            y+=3*n
            x=9*n
        x=n*7
        draw.line((x-n,y,pic.width-5*n,y),fill="#ff0000",width=2)
        draw.text((x+n*50,y),str(y),fill="#000000",font=font)
        y+=2*n
        n1+=1

paper=genarate_papaer(2500)
n=int(paper.width/82)
d=ImageDraw.Draw(paper)
x=n*7
y=n*35
font=ImageFont.truetype("simsun.ttc", n*3)
d.text(((paper.width-n*3*6)/2,n*4),"精准练习答题卡",fill=0,font=font)
pos=genarate_select(30,paper,x,y)
generate_completion(paper,[[1,1,2],[2,1],[1,2,5],[1,1,1],[1,2,2,2,2,2]],n*6,pos[0]+n*2,pos[1]+1)
img=Image.open("pic/name.png")
name_width=int(paper.width/4)
img=img.resize((name_width,int(img.height*579/name_width)))
number_height=img.height
paper.paste(img,(n*6,n*8))
img=Image.open("pic/number.png")
img=img.resize((int(813/number_height*1151),number_height))
paper.paste(img,(n*7+name_width,n*8))
qr_paste("信息技术-打发士大夫士大夫-测试",paper,(n*7+name_width+img.width,n*8),10)
paper.save("papaer.png")
paper.show()