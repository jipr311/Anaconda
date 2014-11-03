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
from Compass import *

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
t = 0.016634

port = 0
server_sock = 0
client_sock = 0
gyroCompass = Compass()
kompassEnabled = 0


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
	advertise_service( server_sock, "3d_OpenGL",
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

def timer():
	global gyroCompass
	global kompassEnabled
	os.system('clear')

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
	mylist = [ ( (gyro_xout, (gyro_xout / 131), "%.5f" % accel_xout_scaled, "%.3f" % tiltX, 0), 'X'),
           ( (gyro_yout, (gyro_yout / 131), "%.5f" % accel_yout_scaled, "%.3f" % tiltY, 0), 'Y'),
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
	
	###

	z = gyroCompass.readSensor()
	if kompassEnabled == 1:
		bluetoothMessage = "x=%.3f--y=%.3f--z=%3.f!" % (tiltX,tiltY, z)
	else:
		bluetoothMessage = "x=%.3f--y=%.3f--z=180.00!" % (tiltX,tiltY)
	client_sock.send(bluetoothMessage)
		
	threading.Timer(t, timer).start()
	
if __name__ == '__main__':

	os.system('clear')
	parser = argparse.ArgumentParser(description = 'OpenGl Tilt Sensor Bluetooth. \nGigatronik Mobile Solutions GmbH \nAuthor: José Pereira', formatter_class=RawTextHelpFormatter)
	parser.add_argument('--kompass', dest ='k_enabled', default = False, action='store_true', help = "Enable the compass sensor." )
	parser.add_argument('--kein-kompass', dest ='k_enabled', default = False, action='store_false', help = "Disable the compass sensor." )
	
	args = parser.parse_args()
	
	kompassEnabled = args.k_enabled

	print (colored("Sensor+OpenGL Beispiel!", 'red'))

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
	
	timer()
