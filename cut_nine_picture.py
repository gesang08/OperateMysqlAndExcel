#!usr/bin/env python
# _*_ coding: UTF-8 _*_
# @Date    : 2019/3/23
# @Author  : ge sang
# @File    : oop 2.7.py
# @Software: PyCharm
# @input   : one picture
# @output  : get nine pictures by cutting the given picture
# @function: 将一张非规则的图片，剪切成尺寸大小相同的九张图片

from PIL import Image

def fill_image(image):
    """将图片填充为正方形"""
    width, height = image.size
    # 选取长和宽中较大值作为图片的尺寸
    new_image_length = width if width > height else height
    # 生成新图片（白底）
    new_image = Image.new(image.mode, (new_image_length, new_image_length), color='white')
    # 将之前的图片粘贴到新图片中，居中
    if width > height:  # 原图宽大于高，则填充图片的竖直维度
        # (x, y)二元元组表示粘贴上图相对下图的起始位置
        new_image.paste(image, (0, int((new_image_length - height)/2)))
    else:
        new_image.paste(image, (int((new_image_length - width)/2), 0))
    return new_image

def cut_image(image):
    width, height = image.size
    item_width = int(width/3)
    box_list = []
    # (left, upper, right, lower)左上右下的pixel
    for i in range(0, 3):  # 两重循环，生成9张图片基于原图的位置
        for j in range(0, 3):
            box = (j * item_width, i * item_width, (j + 1) * item_width, (i + 1) * item_width)
            box_list.append(box)
    image_list = [image.crop(box) for box in box_list]
    return image_list

def save_images(image_list):
    index = 1
    for image in image_list:
        image.save('D:/prog/' + str(index) + '.png', 'PNG')
        index += 1

if __name__ == '__main__':
    file_path = "D:/prog/init.jpg"
    image = Image.open(file_path)
    # image.show()
    image = fill_image(image)
    image_list = cut_image(image)
    save_images(image_list)
