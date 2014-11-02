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
import smbus
import time
import math
import sys

bus = smbus.SMBus(1)
address = 0x1e
bearing  = 0
x_offset = 0
y_offset = 0
scale = 0

class Compass:
	def write_byte(self, adr, value):
		bus.write_byte_data(address, adr, value)
		
	def __init__(self):
		global x_offset
		global y_offset
		global scale
		self.write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
		self.write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
		self.write_byte(2, 0b00000000) # Continuous sampling
		scale = 0.92
		x_offset = 22 #-10
		y_offset = -30 #10
	
	def read_byte(self, adr):
		return bus.read_byte_data(address, adr)

	def read_word(self, adr):
		high = bus.read_byte_data(address, adr)
		low = bus.read_byte_data(address, adr+1)
		val = (high << 8) + low
		return val

	def read_word_2c(self, adr):
		val = self.read_word(adr)
		if (val >= 0x8000):
			return -((65535 - val) + 1)
		else:
			return val
	
	def readSensor(self):
		global x_offset
		global y_offset
		global scale
		
		x_out = (self.read_word_2c(3) - x_offset) * scale
		y_out = (self.read_word_2c(7) - y_offset) * scale
		z_out = (self.read_word_2c(5)) * scale

		bearing  = math.atan2(y_out, x_out) 
		if (bearing < 0):
			bearing += 2 * math.pi
		bearingDegree = math.degrees(bearing)
		#print "Bearing: %.3f" % bearingDegree
		return bearingDegree


