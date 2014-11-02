#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  untitled.py
#  
#  Copyright 2014  <pi@Xoce-Raspberrypi>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
from __future__ import print_function
import RPi.GPIO as GPIO

from termcolor import colored
from multiprocessing import Process, Value, Array
from bluetooth import *
from argparse import *

import smbus
import math
import os
import threading
import glob
import time
import sys
import signal
import argparse
import logging

 
#variablen
t = 0.6634
#alarmTiltThreshold= 30
port = 0
server_sock = 0
client_sock = 0

#ultrasound Variable

distance = Value('d', 3.1415927)
SOUNDS_SPEED = 34300
TRIGGER = 24
ECHO = 23
HC_SR04 = 0

#threshold values
exceptionCounter = 0
watchDog = Value('i', 0)
prevValue = 0
xTiltThreshold = 0
yTiltThreshold = 0

def signalHandler(signal, frame):
	print("Code interupted!")
	sys.exit(0)

def read_byte(adr):
	return bus.read_byte_data(address, adr)

def read_word(adr):
	high = bus.read_byte_data(address, adr)
	low = bus.read_byte_data(address, adr+1)
	val = (high << 8) + low
	return val

def read_word_2c(adr):
	val = read_word(adr)
	if (val >= 0x8000):
		return -((65535 - val) + 1)
	else:
		return val

def prepareUltraSoundPins():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	global TRIGGER, ECHO
	print (colored("calculating distance", 'green'))
	GPIO.setup(TRIGGER, GPIO.OUT)
	GPIO.setup(ECHO, GPIO.IN)
	GPIO.output(TRIGGER, False)
	time.sleep(2)
	print (colored("GPIO ready for use...", 'green'))
	
	
def calculteDistance(d):
	#os.system('clear')
	global TRIGGER
	global ECHO
	global SOUNDS_SPEED
	#global distance
	global exceptionCounter
	#global watchDog
	
	GPIO.output(TRIGGER, True)
	#time.sleep(0.0000000001)
	GPIO.output(TRIGGER, False)
	#time.sleep(0.00001)
	#try:
		
	startsTime = time.time()
	while GPIO.input(ECHO) == 0:
		startsTime = time.time()
		
		
	endsTime = time.time()
	while GPIO.input(ECHO) == 1:
		endsTime = time.time()
		
	pulseDuration = endsTime - startsTime
	#except:
		#exceptionCounter += 1
		#pass 
	distance = pulseDuration *  SOUNDS_SPEED / 2
	distance = round(distance, 3)
	
	d.value = distance
	
	
	#GPIO.cleanup()	
	print (colored("Distance updated to: %s" % (distance), 'red'))
	
def distanceCheckerThread(d, watchDog):
	logging.debug('Thread ON!')
	#global watchDog
	while True:
		calculteDistance(d)
		time.sleep(1)
		watchDog.value +=1
		#time.sleep(2)
		#print (colored("*********************************************************************", 'red'))
	

def dist(a,b):
	return math.sqrt((a*a)+(b*b))

def get_y_rotation(x,y,z):
	radians = math.atan2(x, dist(y,z))
	return -math.degrees(radians)

def get_x_rotation(x,y,z):
	radians = math.atan2(y, dist(x,z))
	return math.degrees(radians)
	
def configBluetooth():
	global server_sock
	global port
	server_sock=BluetoothSocket( RFCOMM )
	server_sock.bind(("",2))
	server_sock.listen(1)
	
	port = server_sock.getsockname()[1]
	
	uuid = "fa87c0d0-afac-11de-8a39-0800200c9a66"
	advertise_service( server_sock, "Notfall-Schuh",
					   service_id = uuid,
					   service_classes = [ uuid, SERIAL_PORT_CLASS ],
					   profiles = [ SERIAL_PORT_PROFILE ], 
						)
	client_info = 0

def waitConnection():
	global port
	global server_sock
	global client_sock
	print ("Waiting for connection on RFCOMM channel %d" % port)
	client_sock, client_info = server_sock.accept()
	print ("Accepted connection from ", client_info)
	print ("Socket: ", client_sock)

def timer():
	os.system('clear')
	global distance
	global exceptionCounter
	global watchDog
	global HC_SR04
	global prevValue
	gyro_xout = read_word_2c(0x43)
	gyro_yout = read_word_2c(0x45)
	gyro_zout = read_word_2c(0x47)
	
	accel_xout = read_word_2c(0x3b)
	accel_yout = read_word_2c(0x3d)
	accel_zout = read_word_2c(0x3f)

	accel_xout_scaled = accel_xout / 16384.0
	accel_yout_scaled = accel_yout / 16384.0
	accel_zout_scaled = accel_zout / 16384.0
	
	tiltX = get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
	tiltY = get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
	

	### Table
	mylist = [ ( (gyro_xout, (gyro_xout / 131), "%.5f" % accel_xout_scaled, "%.3f" % tiltX, xTiltThreshold), 'X'),
           ( (gyro_yout, (gyro_yout / 131), "%.5f" % accel_yout_scaled, "%.3f" % tiltY, yTiltThreshold), 'Y'),
           ( (gyro_zout, (gyro_zout / 131), "%.5f" % accel_zout_scaled, '----------------', '--------------'), 'Z')]

	header = ('xxxxxxxx','Scale','Beschleunigung','Rotationswinkel','Schwellenwert','Axis(%d:%d)'%(exceptionCounter,watchDog.value))
	'''
	if watchDog == prevValue:
		exceptionCounter +=1
		if exceptionCounter > 10:
			exceptionCounter = 0
			HC_SR04.process.terminate()
			time.sleep(1)
			HC_SR04.start()
	else:
		prevValue = watchDog
		exceptionCounter =0
	'''
	longg = dict(zip((0,1,2,3,4,5),(len(str(x)) for x in header)))

	for tu,x in mylist:
		longg.update(( i, max(longg[i],len(str(el))) ) for i,el in enumerate(tu))
		longg[5] = max(longg[5],len(str(x)))
	fofo = ' | '.join('%%-%ss' % longg[i] for i in xrange(0,6))

	print (colored ('\n'.join((fofo % header,
					 '-|-'.join( longg[i]*'-' for i in xrange(6)),
					 '\n'.join(fofo % (a,b,c,d,e,f) for (a,b,c,d,e),f in mylist))), 'green'))
	
	unit = '-'
	if distance.value >= 100:
		distance.value = distance.value/100
		unit = 'm'
	else:
		unit = 'cm'
	#distance = "%s %s" % (distance, unit)
	print (colored("Distance: %s %s" % (distance.value, unit), 'green'))
	#print (colored(HC_SR04, 'green'))
	'''
	if not HC_SR04.isAlive():
		print (colored("thread D!! " , 'red'))
	else:
		print (colored("thread A!! " , 'green'))
	'''
	distace = '???'
	###
	
	alarmMessage = "x=%.3f--y=%.3f!" % (tiltX,tiltY)
	client_sock.send(alarmMessage)
	
	tiltX = math.fabs(tiltX)
	tiltY = math.fabs(tiltY)
	
	if (tiltX > xTiltThreshold):
		print (colored("*********************************************************************", 'red'))
		print (colored("**********Achtung.... Notfall an der X-Axis detektiert!!!!!!*********", 'red'))
		print (colored("*********************************************************************", 'red'))
		alarmMessage = "alarm!"
		
		global client_sock
		
		client_sock.send(alarmMessage)
		#a= raw_input()
		#time.sleep(1)
		
		#print colored("***********************************************************", 'red')
	elif (tiltY > yTiltThreshold):
		print (colored("*********************************************************************", 'red'))
		print (colored("**********Achtung.... Notfall an der Y-Axis detektiert!!!!!!*********", 'red'))
		print (colored("*********************************************************************", 'red'))
		alarmMessage = "alarm!"
		
		global client_sock
		
		client_sock.send(alarmMessage)
		#a= raw_input()
		#time.sleep(1)
	
	threading.Timer(t, timer).start()
	
if __name__ == '__main__':
	global xTiltThreshold
	global yTiltThreshold
	global HC_SR04
	os.system('clear')
	parser = argparse.ArgumentParser(description = 'Emergency-Shoe Notificator. \nGigatronik Mobile Solutions GmbH \nAuthor: José Pereira', formatter_class=RawTextHelpFormatter)
	parser.add_argument('-x', '--x-tilt', dest ='X_TILT', default = 100, type =int, help = "Threshold value for the tilt on the X-Axis." )
	parser.add_argument('-y', '--y-tilt', dest ='Y_TILT', default = 100, type =int, help = "Threshold value for the tilt on the Y-Axis." )
	args = parser.parse_args()
	xTiltThreshold = args.X_TILT
	yTiltThreshold = args.Y_TILT
	print (colored("Sensor+OpenGL Beispiel!", 'red'))
	#print (colored("Threshold X axis:! %d °" % xTiltThreshold, 'red'))
	#print (colored("Threshold Y axis:! %d °" % yTiltThreshold, 'red'))
	#sys.exit(1)
	# Power management registers
	power_mgmt_1 = 0x6b
	power_mgmt_2 = 0x6c

	bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards
	address = 0x68       # This is the address value read via the i2cdetect command

	# Now wake the 6050 up as it starts in sleep mode
	bus.write_byte_data(address, power_mgmt_1, 0)
	
	configBluetooth()
	
	waitConnection()
	
	time.sleep(1)
	
	#set the listener to the Ctrl+C event
	###signal.signal(signal.SIGINT, signalHandler)
	#prepareUltraSoundPins()
	#threadStoper = threading.Event()
	#HC_SR04 = threading.Thread(name = 'HC-SR04 Thread', target = distanceCheckerThread)
	#HC_SR04 = Process(name = 'HC-SR04 Thread', target = distanceCheckerThread, args =(distance, watchDog))
	#run a thread for the distance
	#HC_SR04.setDaemon(True)
	#HC_SR04.start()
	
	#HC_SR04.run()
	
	timer()
