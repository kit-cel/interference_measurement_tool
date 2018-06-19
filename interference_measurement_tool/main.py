import sys # We need sys so that we can pass argv to QApplication
import os

import GUI # This file holds our MainWindow and all design related things
        # it also keeps events etc that we defined in Qt Designer

from PyQt5 import QtGui, QtWidgets# Import the PyQt module we'll need
import time
from threading import Thread
from PIL import Image
import math
import yaml
import subprocess
import numpy as np

class GUIApp(QtWidgets.QMainWindow, GUI.Ui_MainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
            # It sets up layout and widgets that are defined
        self.StartMeasurement.clicked.connect(self.Measurement)
        self.Close.clicked.connect(self.exit)
        self.Location.currentIndexChanged.connect(self.change_map)
        self.Map.mousePressEvent = self.getPos
        self.change_map()


    def Measurement(self): #Durchführung der Messung
        Ort = str(self.Location.currentText())
        Zeit = str(self.Time.currentText())
        lon_pos = str(self.Lon_Pos.text())
        lat_pos = str(self.Lat_Pos.text())

        working_path = os.getcwd()
        uper_path = working_path[:working_path.rfind("/")]
        uper_path = uper_path[:uper_path.rfind("/")]
        Path = uper_path + "/Messungen/" + Ort + "/" + Zeit + "/" + lon_pos + "_" + lat_pos

        def kismet(): #Startbefehl Kismet
            os.system("sudo /usr/bin/kismet_server -f " + working_path + "/KismetConfig/kismet.conf")

        norm_line1 = "ncsource=wlp0s20f0u1u1:hop=false,dwell=10,fcsfail=true,channellist=Channel"
        norm_line2 = "ncsource=wlp0s20f0u1u2:hop=false,dwell=10,fcsfail=true,channellist=Channel"
        norm_line3 = "ncsource=wlp0s20f0u1u3:hop=false,dwell=10,fcsfail=true,channellist=Channel"

        progress = 0
        self.Progress.setValue(progress)



        for i in range(1, 14, 3): #Durchlaufen der 13 Kanäle
            #Override Kismet Config with normelized Config
            os.system('cp KismetConfig/kismet_BU.conf KismetConfig/kismet.conf')

            k = Thread(target=kismet)
            #Channel für jeweiligen Dongel einstellen
            channel1 = norm_line1 + str(i)
            channel2 = norm_line2 + str(i+1)
            channel3 = norm_line3 + str(i+2)
            self.edit_channel(norm_line1,channel1)
            if i < 13:
                self.edit_channel(norm_line2,channel2)
                self.edit_channel(norm_line3,channel3)
            else:
                self.edit_channel(norm_line2,"#"+channel2)
                self.edit_channel(norm_line3,"#"+channel3)

            #Kismet einmalstartet zum Konfigurieren
            k.start()
            time.sleep(1)
            os.system("sudo pkill kismet_server")
            k.join()
            self.delet_Channelfiles(uper_path)
            time.sleep(2)

            #Kismet starten für Messung
            k = Thread(target=kismet)
            k.start()
            time.sleep(11)
            os.system("sudo pkill kismet_server")
            k.join()
            time.sleep(1.5)
            #Nomrzeile für Dongles einstellen
            self.edit_channel(channel1,norm_line1) #Schleife um alle 13 Kanäle abzuarbeiten
            if i < 13:
                self.edit_channel(channel2,norm_line2)
                self.edit_channel(channel3,norm_line3)
            else:
                self.edit_channel("#"+channel2,norm_line2)
                self.edit_channel("#"+channel3,norm_line3)
            self.save_Channelfiles(i,Path,uper_path)
            progress += 1
            self.Progress.setValue(progress)

        #IQ Measurement at 2.45GHz
        CF=2.4e9
        output_file = working_path + '/IQ_Temp/IQ.bin'
        for i in range(0,43,1):
            print( 'IQ-Measurement CF = ' + str(CF) )
            repeat = True
            count = 0
            while repeat and count < 5:
                #Open GNU-Radio as subprocess to catch console output
                grc_output = subprocess.Popen(['python','IQ_Meas_2_45GHz.py','--CF' , str(CF), '--outputfile' , output_file], stdout=subprocess.PIPE ).communicate()[0]
                #Counts Tags saw bei grc if >1 the overflow appeared
                overflow_count = grc_output.decode('utf-8').count('Tag Debug:') #Popen returns Byte -> convert to string
                max_value = self.clipping_test(output_file)
                if overflow_count > 1:
                    print('\nOverflow appeared -> repeat measurement')
                elif max_value >= 2:
                    print('\nSignal clipped -> repeat measurement')
                else:
                    repeat = False
            time.sleep(0.5)
            move_command = "mv IQ_Temp/IQ.bin " + Path +"/IQ_"+ str(int(CF/1e6)) +".bin"
            os.system(move_command)
            time.sleep(1)
            progress += 1
            count += 1
            CF = CF + 2e6
            self.Progress.setValue(progress)

        #IQ Measurement at 866.hMHz
        repeat = True
        count = 0
        while repeat and count < 5:
            grc_output = subprocess.Popen(['python','IQ_Meas_800MHz.py','--outputfile' , output_file], stdout=subprocess.PIPE ).communicate()[0]
            #Counts Tags saw bei grc if >1 the overflow appeared
            overflow_count = grc_output.decode('utf-8').count('Tag Debug:') #Popen returns Byte -> convert to string
            max_value = self.clipping_test(output_file)
            if overflow_count > 1:
                print('\nOverflow appeared -> repeat measurement')
            elif max_value >= 2:
                print('\nSignal clipped -> repeat measurement')
            else:
                repeat = False
        time.sleep(0.5)
        os.system("mv IQ_Temp/IQ.bin " + Path +"/IQ_0800.bin")
        progress += 1
        count += 1
        self.Progress.setValue(progress)

        self.save_Notefile(Path,Ort,Zeit)
        self.save_mark_pos(Path)

    def clipping_test(self,file):
        data = np.fromfile(file,dtype=np.complex64)
        data = np.square(np.abs(data))
        data_max = np.max(data)
        self.amp_max.setText(str(data_max))
        return data_max

    def edit_channel(self,old_line,new_line):
        #Ändern des Kanals im Config File
        path = "KismetConfig/kismet.conf"
        f = open(path,'r')
        filedata = f.read()
        f.close()
        newdata = filedata.replace(old_line, new_line)
        f = open(path,'w')
        f.write(newdata)
        f.close()


    def exit(self):
        self.delet_mark_pos()
        exit()

    def save_Channelfiles(self,Channel,path,uper_path):
        path = path + "/Channel" + str(Channel)
        command = "mkdir -p " + path + " && mv " + uper_path +"/Kismet/* " + path
        os.system(command)

    def delet_Channelfiles(self,uper_path):
        os.system("rm -f " + uper_path + "/Kismet/*")


    def save_Notefile(self,path,ort,zeit):
        note = self.Position.toPlainText()
        localtime = time.asctime( time.localtime(time.time()) )

        stream = open("Note.yaml","w")
        Note = Messung_Note(ort,zeit,localtime,[self.lat_pos , self.lon_pos],note,["Denise" , "30ECBBB"],self.Pixel_pos)
        yaml.dump(Note,stream)

        command = "mkdir -p " + path + " && mv Note.yaml " + path
        os.system(command)
        self.Position.clear()


    def change_map(self):
        if self.Location.currentIndex() == 0:
            self.set_map_value("KIT_17_68597_45005.png",68597,45005,17)

        elif self.Location.currentIndex() == 1:
            self.set_map_value("Kaiserstraße_17_68592_45007.png",68592,45007,17)

        elif self.Location.currentIndex() == 2:
            self.set_map_value("Hbf_17_68592_45015.png",68592,45015,17)

        elif self.Location.currentIndex() == 3:
            self.set_map_value("Gewerbegebiet_17_68607_45007.png",68607,45007,17)

        elif self.Location.currentIndex() == 4:
            self.set_map_value("Neureut_17_68950_44984.png",68593,45004,17)

        elif self.Location.currentIndex() == 5:
            self.set_map_value("Südstadt_17_68589_45010.png",68589,45009,17)

        elif self.Location.currentIndex() == 6:
            self.set_map_value("Zoo_17_68592_45012.png",68592,45012,17)

        elif self.Location.currentIndex() == 7:
            self.set_map_value("Schloss_17_68593_45004.png",68593,45004,17)


    def set_map_value(self,Karte,Xtile,Ytile,Zoom):
        pixmap_image = QtGui.QPixmap(Karte)
        self.Map.setPixmap(pixmap_image)
        self.xtile = Xtile
        self.ytile = Ytile
        self.zoom = Zoom
        self.pic = Image.open(Karte)


    def getPos(self,event):
        x = event.pos().x()
        y = event.pos().y()
        self.Pixel_pos = [x,y]
        n = 2.0 ** self.zoom
        lon_deg = ((self.xtile + (x / 256.0)) / n) * 360.0 - 180.0
        self.lon_pos = self.dd2dms(lon_deg) + "O"
        self.Lon_Pos.setText(self.lon_pos)
        lat_deg = lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (self.ytile + y / 256) / n)))
        lat_deg = math.degrees(lat_rad)
        self.lat_pos = self.dd2dms(lat_deg) + "N"
        self.Lat_Pos.setText(self.lat_pos)
        self.mark_pos(x,y)


    def dd2dms(self,deg):
        d = int(deg)
        md = abs(deg - d) * 60
        m = int(md)
        sd = (md - m) * 60
        pos = str(d)+"°"+str(m)+"m"+str(sd)+"s"
        return(pos)


    def mark_pos(self,x,y):
        Pic = Image.new("RGB",(1280,768))
        Pic = self.pic.copy()
        for i in range (y-1,y+1):
            if i >= 0 and i < 768:
                for j in range (x-7,x+7):
                    if j > 0 and j < 1280:
                        Pic.putpixel((j,i),(255,0,0))
        for i in range (y-7,y+7):
            if i >= 0 and i < 768:
                for j in range (x-1,x+1):
                    if j > 0 and j < 1280:
                        Pic.putpixel((j,i),(255,0,0))
        Pic.save("position.png")
        pixmap_image = QtGui.QPixmap("position.png")
        self.Map.setPixmap(pixmap_image)


    def save_mark_pos(self,path):
        command = "mv position.png " + path
        os.system(command)

    def delet_mark_pos(self):
        cur_dir = os.getcwd()
        file_list= os.listdir(cur_dir)
        if "position.png" in file_list:
            os.system("rm position.png")


class Messung_Note(yaml.YAMLObject):
    yaml_tag = "Messumgebung"
    def __init__(self,Ort,Zeit,Uhrzeit,Position,Kommentar,UHD_Device,Pixel_Pos):
        self.Ort = Ort
        self.Zeit = Zeit
        self.Uhrzeit = Uhrzeit
        self.Position = Position
        self.Kommentar = Kommentar
        self.UHD_Device = UHD_Device
        self.Pixel_Pos = Pixel_Pos


def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = GUIApp()			# We set the form to be our App (design)
    form.show()			# Show the form
    app.exec_()			# and execute the app


if __name__ == '__main__':			# if we're running file directly and not importing it
    main()			# run the main function
