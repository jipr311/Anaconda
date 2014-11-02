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

from termcolor import colored
from dbus import glib
import RPi.GPIO as GPIO

import sys
import os
import time



SOUNDS_SPEED = 34300
TRIGGER = 24
ECHO = 23
def calculte():
	#os.system('clear')
	global TRIGGER, ECHO
	top = 0	
	GPIO.output(TRIGGER, True)
	time.sleep(0.00001)
	GPIO.output(TRIGGER, False)
	#time.sleep(0.00001)
	startsTime = time.time()
	
	while GPIO.input(ECHO) == 0:
		startsTime = time.time()
		#top += 1
		#if top>5:
			#break
		
	top = 0
	endsTime = time.time()
	while GPIO.input(ECHO) == 1:
		endsTime = time.time()
		#top +=1
		
		#if top>5:
			#break
		
	pulseDuration = endsTime-startsTime
	global SOUNDS_SPEED
	distance = pulseDuration *  SOUNDS_SPEED / 2
	distance = round(distance, 3)
	unit = '-'
	if distance >= 100:
		distance = distance/100
		unit = 'm'
	else:
		unit = 'cm'
	print colored("Distance: %.3f %s"%(distance,unit), 'red')
	
	
def main():
	
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	global TRIGGER, ECHO
	print colored("calculating distance", 'green')
	GPIO.setup(TRIGGER, GPIO.OUT)
	GPIO.setup(ECHO, GPIO.IN)
	GPIO.output(TRIGGER, False)
	time.sleep(2)
	while True:
		calculte()
		time.sleep(1)
		print colored("****************", 'yellow')
	GPIO.cleanup()
	return 0

if __name__ == '__main__':
	main()

