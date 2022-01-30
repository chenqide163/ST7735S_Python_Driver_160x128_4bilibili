# coding : UTF-8
import time #用于计算spi刷新整个屏幕所用时长
import RPi.GPIO as GPIO #用于操作引脚
import spidev #树莓派与屏幕的交互协议为SPI，说明见：https://github.com/doceme/py-spidev
from PIL import Image, ImageFont, ImageDraw #用于创建画布，或者读取具体路径下的图片。给图片添加文字。

screenWidth = 160 #屏幕长度
screenHeight = 128 #屏幕宽度
PinDC = 29 #GPIO.BOARD引脚模式，第29号引脚
PinReset = 16  #GPIO.BOARD引脚模式，第16号引脚

def hardReset(): #重置电平时序
    GPIO.output(PinReset, 0)
    time.sleep(.2)
    GPIO.output(PinReset, 1)
    time.sleep(.5)

def sendCommand(command, *bytes): #发送指令（DC为低电平）和数据（DC为高电平）
    GPIO.output(PinDC, 0)
    spi.writebytes([command])
    if len(bytes) > 0:
        GPIO.output(PinDC, 1)
        spi.writebytes(list(bytes))

def reset(): #屏幕初始化
    sendCommand(0x11);
    sendCommand(0x26, 0x04);  # Set Default Gamma
    sendCommand(0xB1, 0x0e, 0x10);  # Set Frame Rate
    sendCommand(0xC0, 0x08, 0x00);  # Set VRH1[4:0] & VC[2:0] for VCI1 & GVDD
    sendCommand(0xC1, 0x05);  # Set BT[2:0] for AVDD & VCL & VGH & VGL
    sendCommand(0xC5, 0x38, 0x40);  # Set VMH[6:0] & VML[6:0] for VOMH & VCOML
    sendCommand(0x3a, 0x05);  # Set Color Format
    sendCommand(0x36, 0xc8);  # RGB
    sendCommand(0x2A, 0x00, 0x00, 0x00, 0x7F);  # Set Column Address
    sendCommand(0x2B, 0x00, 0x00, 0x00, 0x9F);  # Set Page Address
    sendCommand(0xB4, 0x00);
    sendCommand(0xf2, 0x01);  # Enable Gamma bit
    sendCommand(0xE0, 0x3f, 0x22, 0x20, 0x30, 0x29, 0x0c, 0x4e, 0xb7, 0x3c, 0x19, 0x22, 0x1e, 0x02, 0x01, 0x00);
    sendCommand(0xE1, 0x00, 0x1b, 0x1f, 0x0f, 0x16, 0x13, 0x31, 0x84, 0x43, 0x06, 0x1d, 0x21, 0x3d, 0x3e, 0x3f);
    sendCommand(0x29);  # Display On
    sendCommand(0x2C);

def sendManyBytes(bytes): #发送屏幕数据
    GPIO.output(PinDC, 1)
    spi.writebytes(bytes)

def drawImg(img160x128): #入参为160x128像素的image对象
    picReadStartTime = time.time()
    bytes = []
    i = 0  
    for x in range(0, screenWidth):
        for y in range(screenHeight - 1, -1, -1):
            colorValue = img160x128.getpixel((x, y))
            red = colorValue[0]
            green = colorValue[1]
            blue = colorValue[2]
            red = red >> 3;  # st7735s的红色占5位
            green = green >> 2;  # st7735s的绿色占6位
            blue = blue >> 3;  # st7735s的蓝色占5位
            highBit = 0 | (blue << 3) | (green >> 3);  # 每个像素写入个字节，highBit高字节，lowBit低字节
            lowBit = 0 | (green << 5) | red;
            bytes.append(highBit)
            bytes.append(lowBit)
    picReadTimeConsuming = time.time() - picReadStartTime
    startTime = time.time()
    
    # screenWidth*screenHeight*2 每个像素写入个字节。以下for循环是为了控制每次传入的数组长度，防止这个报错,：OverflowError: Argument list size exceeds 4096 bytes.
    for j in range(2000, screenWidth * screenHeight * 2, 2000):  
        sendManyBytes(bytes[i:j])
        i = i + 2000
    sendManyBytes(bytes[i:screenWidth * screenHeight * 2])
    SpiTimeConsuming = time.time() - startTime
    print("picReadTimeConsuming = %.3fs , SpiTimeConsuming = %.3fs" % (picReadTimeConsuming, SpiTimeConsuming))

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PinDC, GPIO.OUT)
GPIO.setup(PinReset, GPIO.OUT)

spi = spidev.SpiDev() #https://github.com/doceme/py-spidev
spi.open(0, 0) 
spi.max_speed_hz = 24000000 #通信时钟最大频率
spi.mode = 0x00 #SPI的模式，ST7735S为模式0，可以参看我这篇内容：
hardReset()
reset()

image = Image.new('RGB', (160, 128)) #可以使用代码新建画布
#image = Image.open('/home/pi/test.jpg');image = image.convert('RGBA'); image = image.resize((160, 128))  #也可以从地址读取图片文件，并缩放为160x128
draw = ImageDraw.Draw(image)
setFont = ImageFont.truetype("/usr/share/fonts/myfont/STXINWEI.TTF", 32) #字体地址，请参考我这篇内容：https://blog.csdn.net/chenqide163/article/details/106933858
draw.text((35, 0), "离思", font=setFont, fill="#FFA500", direction=None)
setFont = ImageFont.truetype("/usr/share/fonts/myfont/STXINWEI.TTF", 16)
draw.text((105, 15), "元稹", font=setFont, fill="#00FFFF", direction=None)
setFont = ImageFont.truetype("/usr/share/fonts/myfont/STXINWEI.TTF", 20)
draw.text((0, 35), "曾经沧海难为水，", font=setFont, fill="#FFFF00", direction=None)
draw.text((0, 60), "除却巫山不是云。", font=setFont, fill="#FFFF00", direction=None)
draw.text((0, 85), "取次花丛懒回顾，", font=setFont, fill="#FFFF00", direction=None)
draw.text((0, 110), "半缘修道半缘君。", font=setFont, fill="#FFFF00", direction=None)

drawImg(image)