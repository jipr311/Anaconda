#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  
#  
#  

from  Compass import *

def main():
	c = Compass()
	c.readSensor()
	print c.readSensor()
	return 0

if __name__ == '__main__':
	while True:
		main()

