import RPi.GPIO as GPIO
import time
import argparse
import sys
import signal
import mysql.connector
from datetime import datetime

# Deklaracja pinow
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq7_dpin = 26
mq7_apin = 0
fanPin = 18

# Pin init
def init():
         GPIO.setwarnings(False)
         GPIO.cleanup()
         GPIO.setmode(GPIO.BCM)
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         GPIO.setup(mq7_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
	 GPIO.setup(fanPin, GPIO.OUT)

# Czytanie danych z SPI od MCP3008
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start zegara
        GPIO.output(cspin, False)

        commandout = adcnum
        commandout |= 0x18
        commandout <<= 3
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1
        return adcout

# Sterowanie wentylatorem
maxCO = 0.25

def fanON():
    GPIO.output(fanPin, True)
    return()
def fanOFF():
    GPIO.output(fanPin, False)
    return()

def getCO(COvalue):
    CO_temp = COvalue
    if CO_temp > maxCO:
        fanON()
	i=1
	time.sleep(5)
    else:
        fanOFF()
	i=0
	time.sleep(5)
    return i

def setPIN(mode):
    GPIO.output(fanPin, mode)
    return()

# Glowna petla programu
def main():
         init()
         print("Kalibracja...")
         time.sleep(1)

	 # Insert do bazy danych
         add_point = ("INSERT INTO reading "
               "(point, date_insert, fan_con) "
               "VALUES (%(COvalue)s, %(DateTime)s, %(TempI)s)")

         while True:
                  cnx = mysql.connector.connect(user='root', password='root', host='localhost', database='czad')
                  cursor = cnx.cursor()
                  COlevel=readadc(mq7_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
                  COvalue=(COlevel/1024.)
                  DateTime=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
		  if (COvalue < 500 and COvalue > 0):
                      temp_i = getCO(COvalue)
		      print("Aktualna wartosc procentowa stezenia CO: " + str("%.2f"%((COlevel/1024.))) + "%, stan wentylatora: ("+ str(temp_i)+")")
		      data = {
                          'COvalue': COvalue,
                          'DateTime': DateTime,
			  'TempI': temp_i,
                          }
                      cursor.execute(add_point, data)
		  else:
                      break
                  COvalue=0
                  cnx.commit()
                  cursor.close()
                  cnx.close()

# Zainicjowanie programu
if __name__ =='__main__':
         try:
                 main()
                 pass
         except KeyboardInterrupt:
                  pass

GPIO.cleanup()
