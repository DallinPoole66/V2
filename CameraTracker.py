import multiprocessing as mp 
import cv2
import numpy as np
import time
import AngleController
import TrackedObject
import serial
connection = serial.Serial("/dev/serial0",baudrate=115200)
class CameraTracker:

    WIDTH = 1920
    HEIGHT = 1080
    FOV = 50
    DEAD_ZONE = WIDTH * 0.02

    def __init__(self, camera_width = 960, camera_height = 540, camera_dead_zone = 0.02):
        self.WIDTH = camera_width
        self.HEIGHT = camera_height
        self.DEAD_ZONE = self.WIDTH * camera_dead_zone


    def make_capture(self):
        # open webcam video stream
        cap = cv2.VideoCapture(0)
        return cap

    def video_in(self, run,  yaw_in, pitch_in ):
        # initialize the HOG descriptor/person detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        cap = self.make_capture()
        cv2.startWindowThread()

        while( run.value == 1 ):
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                with run.get_lock():
                    run.value = 0
                    break

            # Capture frame-by-frame
            ret, frame = cap.read()
            # resizing for faster detection
            frame = cv2.resize(frame, (self.WIDTH, self.HEIGHT))
            if frame is not None:
                result_x, result_y = self.frame_calc( frame, face_cascade )
                with yaw_in.get_lock():
                    yaw_in.value = result_x
                with pitch_in.get_lock():
                    pitch_in.value = result_y
        

        # When everything done, release the capture
        cap.release()




    def frame_calc( self, frame, face_cascade):
        # detect people in the image
        # returns the bounding boxes for the detected objects
        # boxes, weights = hog.detectMultiScale(frame, winStride=(8,8) )
        
        # using a greyscale picture, also for faster detection
        gray = cv2.cvtColor( frame, cv2.COLOR_RGB2GRAY)
        
        boxes = face_cascade.detectMultiScale(gray, minNeighbors= 12, minSize = (100, 100))

        
        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])


        if len(boxes) > 0:
            new_boxes = [boxes[0]]
            boxes = new_boxes


        for (xA, yA, xB, yB) in boxes:
            # display the detected boxes in the color picture
            cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

        
        cv2.imshow('frame', frame)     
        sum = 0
        new_x_offset = 0
        x_offset = 0
        
        if(len(boxes) > 0):
            for box in boxes:
                sum += (box[0] + box[2]) / 2
            
            new_x_offset = sum / len(boxes)
            new_x_offset -= self.WIDTH / 2

        if ( abs(new_x_offset) > self.DEAD_ZONE):
            if(new_x_offset < 0 ):
                x_offset = -1
            else:
                x_offset = 1

        sum = 0
        new_y_offset = 0
        y_offset = 0
        
        if(len(boxes) > 0):
            for box in boxes:
                sum += (box[0] + box[2]) / 2
            
            connection.write( str(sum / self.WIDTH) * self.FOV ))

        return x_offset, y_offset


    def Start(self):   

        run = mp.Value("i", 1)
        yaw_in = mp.Value("i", 0)
        pitch_in = mp.Value("i", 0)
        video_in_p = mp.Process(target=self.video_in, args=(run, yaw_in, pitch_in))
        yaw_p = mp.Process(target=AngleController.motor_control, args=((23, 17, 27, 22), yaw_in, run))
        yaw_p = mp.Process(target=AngleController.motor_control, args=((16, 19, 12, 6
        ), yaw_in, run))


        video_in_p.start()
        yaw_p.start()

        while (run.value == 1):        
            #print(yaw_in.value)
            pass
        video_in_p.join()
        yaw_p.join()

if __name__ == "__main__":
    c = CameraTracker()
    c.Start()