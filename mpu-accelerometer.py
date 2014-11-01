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
import smbus
import math
import os
from termcolor import colored
import threading

import RPi.GPIO as GPIO

from bluetooth import *
import os
import glob
import time, sys, signal
 
#variablen
t = 0.6634
alarmTiltThreshold= 30
port = 0
server_sock = 0
client_sock = 0

#ultrasound Variable
TriggerPin = 24
EchoPin = 23
distance = '---'
sounds_Speed = 34300

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
	global TriggerPin, EchoPin

	GPIO.setup(TriggerPin, GPIO.OUT)
	GPIO.setup(EchoPin, GPIO.IN)
	
	GPIO.output(TriggerPin, False)
	time.sleep(2)
	print (colored("GPIO ready for use...", 'green'))
	
	
def firePulseTrain():
	global TriggerPin
	GPIO.output(TriggerPin, True)
	time.sleep(0.00001)
	GPIO.output(TriggerPin, False)
	print (colored("Pulse's Train fired!", 'green'))
	
def waitForEcho():
	global distance, EchoPin, soundsSpeed
	print (colored("Listening for Echo", 'green'))
	timeStart = 0
	timeEnd = 0
	while GPIO.input(EchoPin) == 0:
		timeStart = time.time()
	while GPIO.input(EchoPin) == 1:
		timeEnd = time.time()
	trainLenght = timeEnd - timeStart
	print (timeEnd)
	print (timeStart)
	print (trainLenght)
	
	a = raw_input()
	distance = trainLenght * sounds_Speed / 2
	distance = round(distance, 3)
	if distance >=100:
		distance =distance /100
		unit = 'm'
	else:
		unit = 'cm'
		distance = "%.3f %s" % (distance, unit)
	return distance
	
def distanceCheckerThread(args1, stopEvent):
	while (True):
		print (colored("*********************************************************************", 'red'))
		firePulseTrain()
		x = waitForEcho()
		time.sleep(2)
		print (colored("*********************************************************************", 'red'))
	

def dist(a,b):
	return math.sqrt((a*a)+(b*b))

def get_y_rotation(x,y,z):
	radians = math.atan2(x, dist(y,z))
	return -math.degrees(radians)

def get_x_rotation(x,y,z):
	radians = math.atan2(y, dist(x,z))
	return math.degrees(radians)
	
def configBluetooth():
	global server_sock, port
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
	#os.system('clear')
	global distance
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
	mylist = [ ( (gyro_xout, (gyro_xout / 131), "%.5f" % accel_xout_scaled, "%.3f" % tiltX, 30), 'X'),
           ( (gyro_yout, (gyro_yout / 131), "%.5f" % accel_yout_scaled, "%.3f" % tiltY, 30), 'Y'),
           ( (gyro_zout, (gyro_zout / 131), "%.5f" % accel_zout_scaled, '----------------', '--------------'), 'Z')]

	header = ('xxxxxxxx','Scale','Beschleunigung','Rotationswinkel','Schwellenwert','Axis')

	longg = dict(zip((0,1,2,3,4,5),(len(str(x)) for x in header)))

	for tu,x in mylist:
		longg.update(( i, max(longg[i],len(str(el))) ) for i,el in enumerate(tu))
		longg[5] = max(longg[5],len(str(x)))
	fofo = ' | '.join('%%-%ss' % longg[i] for i in xrange(0,6))

	print (colored ('\n'.join((fofo % header,
					 '-|-'.join( longg[i]*'-' for i in xrange(6)),
					 '\n'.join(fofo % (a,b,c,d,e,f) for (a,b,c,d,e),f in mylist))), 'green'))
	print (colored("Distance: %s" % distance, 'green'))
	###
	
	tiltX = math.fabs(tiltX)
	tiltY = math.fabs(tiltY)
	
	if (tiltX > alarmTiltThreshold):
		print (colored("*********************************************************************", 'red'))
		print (colored("**********Achtung.... Notfall an der X-Axis detektiert!!!!!!*********", 'red'))
		print (colored("*********************************************************************", 'red'))
		alarmMessage = "alarm!"
		
		global client_sock
		
		#client_sock.send(alarmMessage)
		#a= raw_input()
		#time.sleep(1)
		
		#print colored("***********************************************************", 'red')
	elif (tiltY > alarmTiltThreshold):
		print (colored("*********************************************************************", 'red'))
		print (colored("**********Achtung.... Notfall an der Y-Axis detektiert!!!!!!*********", 'red'))
		print (colored("*********************************************************************", 'red'))
		alarmMessage = "alarm!"
		
		global client_sock
		
		#client_sock.send(alarmMessage)
		#a= raw_input()
		#time.sleep(1)
	
	threading.Timer(t, timer).start()
	
if __name__ == '__main__':
	os.system('clear')
	print (colored("Accelerometer Beispiel!", 'red'))
	# Power management registers
	power_mgmt_1 = 0x6b
	power_mgmt_2 = 0x6c

	bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards
	address = 0x68       # This is the address value read via the i2cdetect command

	# Now wake the 6050 up as it starts in sleep mode
	bus.write_byte_data(address, power_mgmt_1, 0)

	#configBluetooth()
	
	#waitConnection()
	
	#print (colored("Socket: ", 'green'))

	time.sleep(1)
	
	
	#set the listener to the Ctrl+C event
	###signal.signal(signal.SIGINT, signalHandler)
	prepareUltraSoundPins()
	threadStoper = threading.Event()
	HC_SR04 = threading.Thread(target = distanceCheckerThread, args=(1, threadStoper))
	#run a thread for the distance
	HC_SR04.start()
	timer()
