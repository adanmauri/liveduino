#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Adán Mauri Ungaro <adan.mauri@gmail.com>
#
# This file is part of FrameDuino. FrameDuino is free software; you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.  See the file
# COPYING included with this distribution for more information.

import time
import bluetooth
import os
from abstract_driver import AbstractDriver
from pprint import pprint

#ERRORS
DEVICES_NOT_FOUND    = "Could not find bluetooth devices nearby."
DEVICE_NOT_CONNECTED = "Could not find target bluetooth device nearby."

class BluetoothDriver(AbstractDriver):
    
    DEVICE_NAME    = None
    DEVICE_ADDRESS = None
    DEVICE_PORT    = 1
    DEV            = None
    
    # ----------------------------------------------------------------------
    # Basic Functions
    # ----------------------------------------------------------------------
    
    def __init__(self, name="Pinguino", dev=None):
        self.DEVICE_NAME = name
        
        list_devs = BluetoothDriver.nearbyDevs(self.DEVICE_NAME)        
        if dev is None:
            if list_devs:
                self.DEVICE_ADDRESS = list_devs[0]
            else:
                raise Exception(DEVICES_NOT_FOUND)
        else:
            if not dev in list_devs:
                raise Exception(DEVICE_NOT_CONNECTED)
            else:
                self.DEVICE_ADDRESS = dev
        
        self.__connect__()

    # ----------------------------------------------------------------------        
    def __connect__(self):
        pprint(self.DEVICE_ADDRESS)
        while(True):    
            try:
                self.DEV = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.DEV.connect((self.DEVICE_ADDRESS, self.DEVICE_PORT))
                break;
            except bluetooth.btcommon.BluetoothError as error:
                self.DEV.close()
                print "Could not connect: ", error, "; Retrying in 10s..."
                time.sleep(10)
            
    # ----------------------------------------------------------------------        
    def __disconnect__(self):
        self.DEV.close()      
     
    # ----------------------------------------------------------------------        
    def disconnect(self):
        self.__disconnect__()         
               
    # ----------------------------------------------------------------------
    # I/O Functions
    # ----------------------------------------------------------------------
    
    def write(self, msg):
        self.DEV.send(msg)
        '''try:
            
        except usb.USBError, V:
            raise Exception(V[1])'''

    #----------------------------------------------------------------------
    def read(self, length=1024):
        return self.DEV.recv(length)
        '''try:
            return "".join(map(chr, self.dh.bulkRead(self.ENDPOINT_IN, length, self.TIMEOUT)))
        except usb.core.USBError, V:
            raise Exception(V[1])'''

    def readProcess(self, cmd):
        self.write(cmd)
        return self.read()
    
    # ----------------------------------------------------------------------
    # Static Methods
    # ----------------------------------------------------------------------
    @staticmethod        
    def nearbyDevs(target_name = "Pinguino"):
        devs = []
        pprint(devs)
        nearby_devices = bluetooth.discover_devices()
        pprint(nearby_devices)
        for dev in nearby_devices:
            if target_name == bluetooth.lookup_name( dev ):
                devs.append(dev)
        return devs   

