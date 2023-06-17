
import numpy as np
import cv2 as cv
import Person
import time

try:
    log = open('log.txt',"w")
except:
    print( "Pas d'archive")


cnt_up   = 0
cnt_down = 0


#cap = cv.VideoCapture(0)
cap = cv.VideoCapture('TestVideo.avi')
#camera = PiCamera()
##camera.resolution = (160,120)
##camera.framerate = 5
##rawCapture = PiRGBArray(camera, size=(160,120))
##time.sleep(0.1)


##cap.set(3,160) #Width
##cap.set(4,120) #Height

#Imprime
for i in range(19):
    print( i, cap.get(i))

h = 480
w = 640
frameArea = h*w
areaTH = frameArea/250
print( 'Area Threshold', areaTH)

#Lignes de détections
line_up = int(1.1*(h/3))
up_limit =   int(1*(h/3))

line_down   = int(1.5*(h/3))
down_limit = int(1.6*(h/3))

print( "Limite haute:",str(line_down))
print( "Limite basse:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down];
pt2 =  [w, line_down];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up];
pt4 =  [w, line_up];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit];
pt6 =  [w, up_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit];
pt8 =  [w, down_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

#Soustraire le fond
fgbg = cv.createBackgroundSubtractorMOG2(detectShadows = True)

#filtres
kernelOp = np.ones((3,3),np.uint8)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((11,11),np.uint8)

#Variables
font = cv.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1
zone_comptx = [0, 640]
while(cap.isOpened()):
##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    
    ret, frame = cap.read()
##    frame = image.array

    for i in persons:
        i.age_one() 
    #########################
    #   PRE-PROCES#
    #########################
    
    #appliquer suppression du fond
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    #Binariser gris
    try:
        ret,imBin= cv.threshold(fgmask,200,255,cv.THRESH_BINARY)
        ret,imBin2 = cv.threshold(fgmask2,200,255,cv.THRESH_BINARY)
        #Opening (erode->dilate) para quitar ruido.
        mask = cv.morphologyEx(imBin, cv.MORPH_OPEN, kernelOp)
        mask2 = cv.morphologyEx(imBin2, cv.MORPH_OPEN, kernelOp)
        #Closing (dilate -> erode) para juntar regiones blancas.
        mask =  cv.morphologyEx(mask , cv.MORPH_CLOSE, kernelCl)
        mask2 = cv.morphologyEx(mask2, cv.MORPH_CLOSE, kernelCl)
    except:
        print('EOF')
        print( 'UP:',cnt_up)
        print ('DOWN:',cnt_down)
        break
    #################
    #   Contours #
    #################
    
    # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind.
    contours0, hierarchy = cv.findContours(mask2,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    for cnt in contours0:
        area = cv.contourArea(cnt)
        if area > areaTH:
            #################
            #   TRACKING    #
            #################
            
            
            
            M = cv.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv.boundingRect(cnt)

            new = True
            if cy in range(up_limit,down_limit):
                for i in persons:
                    if abs(x-i.getX()) < w and abs(y-i.getY()) < h :
                        
                        new = False
                        i.updateCoords(cx,cy)   #actualiza coordenadas en el objeto and resets age
                        if i.going_UP(line_down,line_up) == True:
                            cnt_up += 1;
                            print( "ID:",i.getId(),'Detection de sortie date et heure',time.strftime("%c"))
                            log.write("ID: "+str(i.getId())+' Detection de sortie date et heure ' + time.strftime("%c") + '\n')
                        elif i.going_DOWN(line_down,line_up) == True:
                            cnt_down += 1;
                            print( "ID:",i.getId(),'Detection d entrée date et heure',time.strftime("%c"))
                            log.write("ID: " + str(i.getId()) + ' Detection d entrée date et heure ' + time.strftime("%c") + '\n')
                        break
                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        
                        index = persons.index(i)
                        persons.pop(index)
                        del i    # effacer registre i
                if new == True:
                    p = Person.MyPerson(pid,cx,cy, max_p_age)
                    persons.append(p)
                    pid += 1     
            #################
            #   #
            #################
            cv.circle(frame,(cx,cy), 5, (0,0,255), -1)
            img = cv.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            
            #cv.drawContours(frame, cnt, -1, (0,255,0), 3)
            
    #END for cnt in contours0
            
    #########################
    # D#
    #########################
    for i in persons:
##        if len(i.getTracks()) >= 2:
##            pts = np.array(i.getTracks(), np.int32)
##            pts = pts.reshape((-1,1,2))
##            frame = cv.polylines(frame,[pts],False,i.getRGB())
##        if i.getId() == 9:
##            print str(i.getX()), ',', str(i.getY())
        #cv.putText(frame, str(i) ,(i.getX()+20,i.getY()-20),font,0.3,i.getRGB(),1)
        cv.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv.LINE_AA)
        
    #################
    # Affichages #
    #################
    str_up = 'SORTIES:   '+ str(cnt_up)
    str_down = 'ENTREES:  '+ str(cnt_down)
    solde = cnt_down - cnt_up
    str_in= 'PRESENTS: '+ str(solde)
    frame = cv.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
    frame = cv.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
    frame = cv.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
    frame = cv.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
    #cv.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv.LINE_AA)
    cv.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv.LINE_AA)
    #cv.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv.LINE_AA)
    cv.putText(frame, str_down ,(10,60),font,0.5,(255,0,0),1,cv.LINE_AA)
    cv.putText(frame, str_in ,(10,80),font,0.5,(0,255,0),1,cv.LINE_AA)

    cv.imshow('Frame',frame)
    cv.imshow('Mask',mask)    
    

##    rawCapture.truncate(0)
    
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
#END while(cap.isOpened())
    
#################
#   exit #
#################
log.flush()
log.close()
cap.release()
cv.destroyAllWindows()
