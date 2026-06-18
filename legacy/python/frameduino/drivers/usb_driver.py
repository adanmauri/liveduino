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

import usb
import os
from abstract_driver import AbstractDriver

#ERRORS
INCORRECT_BOOTLOADER = "Incorrect bootloader version, available: 2, 4"
DEVICES_NOT_FOUND    = "No open devices found or no device connected."
DEVICE_NOT_CONNECTED = "Device is not open or no device connected."

class USBDriver(AbstractDriver):
    
    VENDOR        = 0x04D8
    PRODUCT       = 0xFEAA

    TIMEOUT       = None
    INTERFACE     = 0
    ENDPOINT_OUT  = 0x01

    BOOTLOADER    = None
    CONFIGURATION = 0x03
    ENDPOINT_IN   = 0x82
            
    DEVNAME       = None
    DEV           = None
    
    # ----------------------------------------------------------------------
    # Basic Functions
    # ----------------------------------------------------------------------
    
    def __init__(self, bootloader=4, timeout=1000, dev=None):
        self.TIMEOUT = timeout  #1000

        if bootloader == 2 or 4:
            self.setBootloader(bootloader)
        else:
            raise Exception(INCORRECT_BOOTLOADER)

        list_devs = USBDriver.avalilableDevs()
        if dev is None:
            if list_devs:
                self.DEV = list_devs[0]
            else:
                raise Exception(DEVICES_NOT_FOUND)
        else:
            if not dev in list_devs:
                raise Exception(DEVICE_NOT_CONNECTED)
            else:
                self.DEV = dev

        self.__connect__()

    # ----------------------------------------------------------------------        
    def __connect__(self):
        try:
            self.dh = self.DEV.open()
            self.dh.setConfiguration(self.CONFIGURATION)
            self.dh.claimInterface(self.INTERFACE)
        except usb.core.USBError, V:
            raise Exception(V[1])

    # ----------------------------------------------------------------------                    
    def setBootloader(self, bootloader):  
         self.BOOTLOADER = bootloader
         if (self.BOOTLOADER == 2):
            self.CONFIGURATION = 0x03
            self.ENDPOINT_IN   = 0x82
         else:
            if (self.BOOTLOADER == 4):
                self.CONFIGURATION = 0x01
                self.ENDPOINT_IN   = 0x81

    # ----------------------------------------------------------------------                    
    def getBootloader(self, bootloader):  
         return self.BOOTLOADER
    
    # ----------------------------------------------------------------------
    # I/O Functions
    # ----------------------------------------------------------------------
    
    def write(self, msg):
        try:
            self.dh.bulkWrite(self.ENDPOINT_OUT, msg, self.TIMEOUT)
        except usb.USBError, V:
            raise Exception(V[1])

    #----------------------------------------------------------------------
    def read(self, length=64):
        try:
            return "".join(map(chr, self.dh.bulkRead(self.ENDPOINT_IN, length, self.TIMEOUT)))
        except usb.core.USBError, V:
            raise Exception(V[1])

    def readProcess(self, cmd):
        self.write(cmd)
        return self.read()

    # ----------------------------------------------------------------------
    # Static Methods
    # ----------------------------------------------------------------------
    @staticmethod        
    def avalilableDevs():
        devs = []
        busses = usb.busses()
        for bus in busses:
            for dev in bus.devices:
                if dev.idVendor == USBDriver.VENDOR and dev.idProduct == USBDriver.PRODUCT:
                    devs.append(dev)
        return devs

