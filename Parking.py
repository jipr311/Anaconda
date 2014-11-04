#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  
#  
from termcolor import colored
import RPi.GPIO as GPIO
import smbus
import time
import math
import sys

bus = smbus.SMBus(1)
SOUNDS_SPEED = 34300
TRIGGER = 24
ECHO = 23

class Parking:
	
	def calculte(self):
		global TRIGGER, ECHO
		top = 0	
		GPIO.output(TRIGGER, True)
		time.sleep(0.00001)
		GPIO.output(TRIGGER, False)
		#time.sleep(0.00001)
		startsTime = time.time()
		
		while GPIO.input(ECHO) == 0:
			startsTime = time.time()
			
		top = 0
		endsTime = time.time()
		while GPIO.input(ECHO) == 1:
			endsTime = time.time()
			
		pulseDuration = endsTime-startsTime
		global SOUNDS_SPEED
		distance = pulseDuration *  SOUNDS_SPEED / 2
		distance = round(distance, 3)
		'''
		unit = '-'
		if distance >= 100:
			distance = distance/100
			unit = 'm'
		else:
			unit = 'cm'
		'''
		#print colored("Distance: %.3f %s"%(distance,unit), 'red')
		dist ="%.3f"%(distance)
		return dist
		
	def __init__(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		global TRIGGER, ECHO
		#print colored("calculating distance", 'green')
		GPIO.setup(TRIGGER, GPIO.OUT)
		GPIO.setup(ECHO, GPIO.IN)
		GPIO.output(TRIGGER, False)
		time.sleep(2)
		#while True:
			#self.calculte()
			#time.sleep(1)
			#print colored("****************", 'yellow')
		#GPIO.cleanup()



