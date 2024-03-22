
import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import creat_paper
img=Image.new("RGB",(1000,1000),"white")
creat_paper.generate_barcode("123456789101112",img,(300,400),128)
#显示图片
img.show()