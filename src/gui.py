#!/home/pi/.virtualenvs/cv/bin/python 

# Local libraries
from sting import Sting
from menus import generateMenus
from menu import GoBack


# Libraries

from RPi import GPIO

import numpy as np
import cv2
import argparse
import subprocess
import time
import boto3
import copy
from botocore.session import Session
from botocore.client import Config

import traceback
import sys

import threading
import Queue


def imgToJpg(img):
    retVal, jpgBuf = cv2.imencode('.jpeg', img)
    if retVal:
        return bytes(jpgBuf.tostring())
    return None



try:
    from imutils.video.pivideostream import PiVideoStream as VideoStream
except ImportError:
    from imutils.video import VideoStream


class Toast(object):
    fontScale = .75
    def __init__(self, text, timeout = 3, fontScale = .75):
        self.text = text
        self.fontScale = fontScale
        if timeout:
            self.expireTime = time.time() + timeout
        else:
            self.expireTime = 0

    def checkTimeout(self):
        if self.expireTime and self.expireTime < time.time():
            return None
        return self

class FaceRekognizer(object):

    def __init__(self, collectionId):
        self.collectionId = collectionId
        self.faceId = None
        self.allThreadStarted = False
        self._finished = False
        self.threads = []
        self.resultsQ = Queue.Queue()
        config = Config(connect_timeout = 1, read_timeout = 2)
        session = Session()
        self.rekClient = session.create_client('rekognition', config = config)


    def addImage(self, img, last = False):
        if self.allThreadStarted:
            return

        thread = threading.Thread(target = self.checkRekognition, args = (img, ))
        thread.start()
        self.threads.append(thread)
        if last:
            self.allThreadStarted = True

    def checkRekognition(self, img):
        ident = threading.current_thread().ident
        faceId = None
        startTime = time.time()
        try:
            res = self.rekClient.search_faces_by_image(
                    CollectionId = self.collectionId, 
                    Image = {'Bytes': imgToJpg(img)})

            if res['FaceMatches']:
                faceId = res['FaceMatches'][0]['Face']['FaceId']
                self.resultsQ.put_nowait(faceId)
                self.allThreadStarted = True
        except:
            pass

        elapsed = time.time() - startTime

    @property
    def finished(self):
        return self.allThreadStarted and all([not t.isAlive() for t in self.threads])

    def destroy(self):
        self.__del__()

    def __del__(self):
        for thread in self.threads:
            thread.join(.5)

    def getResult(self):
        if self.faceId is None and self.finished:
            self.faceId = ''
            while not self.resultsQ.empty():
                self.faceId = self.resultsQ.get_nowait()
                self.resultsQ.task_done()

        return self.faceId



class StingGui(object):

    buttonPins = { p:i for i,p in enumerate((17, 22, 23, 27)) }
    framerate  = 90
    screenWidth = 320
    screenHeight = 240

    blue = (0xff, 0, 0)
    green = (0, 0xa0, 0)
    red   = (0, 0, 0xff)

    faceTimeout = 1.0
    logoTimeout = 5.0


    collectionId = 'sturdy-sting'

    def __init__(self, showLogo = True):

        self.ready                  = False
        self.menu                   = generateMenus(self)
        self._oldMenu               = None

        self.toast                  = None
        self._oldToast              = None 

        self._oldButton             = None

        self.running                = True

        self.fireEnable             = True
        self.addWhiteListFlag       = False
        self.removeWhiteListFlag    = False

        self.showLogo               = showLogo
        self.startTime              = time.time()

        self.logoImage              = cv2.imread('logo.png')
        self.faceCascade            = cv2.CascadeClassifier('face_cascade.xml')

        self.videoStream            = VideoStream(framerate = self.framerate, resolution = (self.screenWidth, self.screenHeight))

        self.isEnemy                = False
        self.rekClient              = boto3.client('rekognition')


    def __enter__(self):
        self.ready = True
        self.videoStream.start()

        GPIO.setmode(GPIO.BCM)
        for buttonPin in self.buttonPins.keys():
            GPIO.setup(buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.add_event_detect(buttonPin, GPIO.FALLING, callback = self.buttonPressed, bouncetime = 50)

        cv2.namedWindow('disp', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('disp', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        return self

    def __exit__(self, *args):
        self.videoStream.stop()
        for buttonPin in self.buttonPins.keys():
            GPIO.remove_event_detect(buttonPin)
            GPIO.cleanup(buttonPin)

    def buttonPressed(self, buttonPin):
        # The built-in debounce in rpi.GPIO isn't very good,
        # so we add our own
        time.sleep(.010)

        pressed = not GPIO.input(buttonPin)
        if pressed:
            buttonIndex = self.buttonPins[buttonPin]
            print 'button', buttonIndex
            self.menu = self.menu.select(buttonIndex)

    def stop(self):
        self.running = False

    def addOverlay(self, frame):

        if self.showLogo:
            delta = time.time() - self.startTime
            if delta > self.logoTimeout:
                self.showLogo = False
            else:
                weight = (self.logoTimeout - delta) / self.logoTimeout
                return cv2.addWeighted(frame, 1.0, self.logoImage, weight, 0)

        if self.toast:
            self.toast = self.toast.checkTimeout()

        if not self.toast:
            self.toast = Toast('Weapon Hot' if self.fireEnable else 'Weapon Safe', 0)

        menuChanged  = self.menu != self._oldMenu
        toastChanged = self.toast != self._oldToast

        if menuChanged or toastChanged:
            self._oldMenu = self.menu
            self._oldToast = self.toast
            texts = ([ x[0] for x in self.menu.options ] + ['', '', '', ''] )[:4]
            heightStep = self.screenHeight / len(texts)
            yOffset = heightStep / 2
            thickness = 1
            fontFace = cv2.FONT_HERSHEY_DUPLEX
            fontScale = getattr(self.menu, 'fontScale', 1.0)

            img = np.zeros((self.screenHeight, self.screenWidth, 3), np.uint8)
            for i,text in enumerate(texts):
                size, dummy = cv2.getTextSize(text, fontFace, fontScale, thickness)
                w,h = size
                x = self.screenWidth - w - 5
                y = i * heightStep + h + yOffset
                cv2.putText(img, text, (x,y), fontFace, fontScale ,(255,255,255), thickness)

            thickness = 2
            if self.menu.title:
                size, dummy = cv2.getTextSize(self.menu.title, fontFace, fontScale, thickness)
                w,h = size
                x = 0
                y = h 
                cv2.putText(img, self.menu.title, (x,y), fontFace, fontScale ,(255,255,255), thickness)

            if self.toast:
                fontScale = getattr(self.toast, 'fontScale', 1.0)
                size, dummy = cv2.getTextSize(text, fontFace, fontScale, thickness)
                x = 0
                y = int(self.screenHeight - size[1] * 1.1)
                cv2.putText(img, self.toast.text, (x,y), fontFace, fontScale ,(255,255,255), thickness)
            self._menuImage = img

        return cv2.add(frame, self._menuImage)




    def getFrame(self):
        frame = self.videoStream.read()
        frame = cv2.flip(frame, -1) # rotate 180
        return frame

    def getFaces(self, frame): 
        ''' Returns an array of tuples which are (faceImage, (x1, y1, x2, y2)) '''

        ret = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faceLocations = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
                flags = cv2.CASCADE_SCALE_IMAGE)

        for (x, y, w, h) in faceLocations:
            cx,cy = int(x + w / 2), int(y + h / 2)
            hw,hh = [int(q * 2) / 2 for q in (w,h) ]
            x1,x2 = cx - hw, cx + hw
            y1,y2 = cy - hh, cy + hh
            
            imgH, imgW = frame.shape[0:2]

            x1,y1 = [ max(q, 0) for q in (x1,y1) ]
            x2,y2 = [ min(q, r) for q,r in ((x2,imgW),(y2,imgH)) ]

            if (x2 - x1) > 0 and (y2 - y1) > 0:
                faceImage  = copy.deepcopy(gray[y1:y2, x1:x2])
                ret.append((faceImage,(x1,y1,x2,y2)))

        return ret

    def drawBoxesAroundFaces(self, frame, faces):
        color = self.red if self.isEnemy else self.blue
        for face, box in faces:
            cv2.rectangle(frame, box[0:2], box[2:4], color, 2)
            
    def mainLoop(self):
        if not self.ready:
            raise RuntimeError('Class not in ready state use "with" statement')

        frameTries              = 5

        lastFaceFoundTime       = 0
        faceFound               = False
        faceId                  = None
        frameTriesRemaining     = 0

        faceRek                 = None

        loopStart               = time.time()

        with Sting() as sting:
            while self.running:
                loopElapsed = time.time() - loopStart
                if loopElapsed > .2:
                    print 'loop took %d milliseconds' % ( loopElapsed * 1000 )
                loopStart = time.time()
                frame = self.getFrame()
                faces = self.getFaces(frame)
                self.drawBoxesAroundFaces(frame, faces)

                faceThisFrame = len(faces) > 0

                if faceThisFrame:
                    if faceFound == False:
                        if not self.addWhiteListFlag:
                            if faceRek:
                                faceRek.destroy()
                            faceRek = FaceRekognizer(self.collectionId)
                            frameTriesRemaining     = frameTries

                        faceId                  = None
                        self.isEnemy            = False

                    faceFound = True
                    lastFaceFoundTime = time.time()
                    faceImage = faces[0][0]

                    # Identify, Friend or Foe?
                    if frameTriesRemaining and faceRek:
                        frameTriesRemaining -= 1
                        faceRek.addImage(faceImage, frameTriesRemaining > 0)

                    if self.addWhiteListFlag:
                        jpg = imgToJpg(faceImage)
                        args = {'CollectionId': self.collectionId, 'Image': {'Bytes': jpg} }
                        try: 
                            ret = self.rekClient.index_faces(**args)
                            self.toast = Toast('Friend added', 3)
                            self.menu = self.menu.select(GoBack())
                            faceId = None
                            faceFound = False
                            isEnemy = False
                        except:
                            pass

                    elif self.removeWhiteListFlag and faceId:
                        ret = self.rekClient.delete_faces(CollectionId = self.collectionId, FaceIds = [ faceId ])
                        print 'called delete_faces'
                        self.toast = Toast('Friend removed', 3)
                        self.menu = self.menu.select(GoBack())
                        faceId = None
                        faceFound = False
                        isEnemy = True


                # Coast for a bit if we don't find a faces for a few frames
                elif faceFound and time.time() - lastFaceFoundTime > self.faceTimeout:
                        faceFound           = False
                        faceId              = None

                if faceRek and faceRek.finished:
                    faceId = faceRek.getResult()
                    self.isEnemy = not faceId
                    faceRek.destroy()
                    faceRek = None

                if faceRek:
                    print 'Checking    \r',
                else:
                    if faceFound:
                        if self.isEnemy:
                            print 'Enemy         \r',
                        else:
                            print 'Friend         \r',
                    else:
                        print 'idle               \r',

                sys.stdout.flush()

                # Where the rubber meets the road
                if self.fireEnable and faceFound:
                    if self.isEnemy or (faceRek and not faceRek.finished):
                        sting.flywheel = True
                        if self.isEnemy:
                            sting.trigger = True
                    else:
                        sting.trigger = False
                        sting.flywheel = False
                else:
                    sting.trigger = False
                    sting.flywheel = False


                # Update display
                frame = self.addOverlay(frame)
                cv2.imshow('disp', frame)
                cv2.waitKey(2)



parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--logo', action = 'store_true', default = True)
group.add_argument('--no-logo', action = 'store_false', dest = 'logo' )
args = parser.parse_args()
    
shutdown = True

with StingGui(showLogo = args.logo) as stingGui:
    try:
        stingGui.mainLoop()
    except KeyboardInterrupt:
        shutdown = False
    except: # Don't shut off machine on exception
        traceback.print_exc()
        shutdown = False

if shutdown:
    subprocess.check_call(('shutdown', 'now'))

sys.exit()




