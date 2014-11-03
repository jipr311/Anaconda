/*
 * untitled.c
 * 
 * Copyright 2014  <pi@Xoce-Raspberrypi>
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 * 
 * 
 */


#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/hci.h>
#include <bluetooth/hci_lib.h>

// to compile gcc must be invoked and link against libbluetooth
// gcc -o <output> <source.c> -lbluetooth
// need the parameter -lbluetooth
int main(void)
{
	printf("OpenGl Demo\n");
	
	inquiry_info *ii = NULL;
	int maxResp, numResp;
	int deviceId, socket, len, flags;
	int i;
	char address[19] = {0};
	char name[248] = {0};
	
	deviceId = hci_get_route(NULL);
	socket = hci_open_dev(deviceId);
	if (deviceId < 0 || socket < 0) {
		perror("opening socket");
		exit(1);
	}
	len = 8;
	maxResp = 255;
	flags = IREQ_CACHE_FLUSH;
	ii = (inquiry_info*)malloc(maxResp * sizeof(inquiry_info));
	numResp = hci_inquiry(deviceId, len, maxResp, NULL, &ii, flags);
	if(numResp < 0 ) perror("hci_inquiry");
	
	for (i = 0; i< numResp; i++) {
		ba2str(&(ii+i)-> bdaddr, address);
		memset (name, 0 , sizeof(name));
		if (hci_read_remote_name(socket, &(ii+i)->bdaddr, sizeof(name), name, 0) < 0)
			strcpy (name, "[unknown]");
			printf("%s %s\n", address, name);

	}
	free(ii);
	close (socket);
	return 0; 
	
}

