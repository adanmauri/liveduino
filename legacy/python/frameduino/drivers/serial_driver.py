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

import serial
import os
from abstract_driver import AbstractDriver

if os.name == "posix": #GNU/Linux
    os.environ["PORTNAME"] = "/dev/ttyACM%d"

elif os.name == "nt":  #Windows
    os.environ["PORTNAME"] = "COM%d"

#ERRORS
PORTS_NOT_FOUND      = "No open ports found or no device connected."
PORT_NOT_CONNECTED   = "Port is not open or no device connected."
NO_SERIAL_DEVICES    = "No Serial devices connected"

class SerialDriver(AbstractDriver):
        
    PORTNAME = None
    PORT     = None
    BAUDRATE = None
    TIMEOUT  = None
    
    serial      = None

    # ----------------------------------------------------------------------
    # Basic Functions
    # ----------------------------------------------------------------------
        
    def __init__(self, port=None, baudrate=9600, timeout=1):        
        self.TIMEOUT  = timeout   #1
        self.BAUDRATE = baudrate  #9600
        self.PORTNAME = os.getenv("PORTNAME")

        list_ports = SerialDriver.avalilablePorts()
        if port is None:
            if list_ports:
                self.PORT = list_ports[0]
            else:
                raise Exception(PORTS_NOT_FOUND)
        else:
            if not port in list_ports:
                raise Exception(PORT_NOT_CONNECTED)
            else: self.PORT = port

        self.__connect__()

    # ----------------------------------------------------------------------        
    def __connect__(self):
        try:
            self.serial = serial.Serial(port=self.PORTNAME%self.PORT, timeout=self.TIMEOUT, baudrate=self.BAUDRATE)
        except:
            raise Exception(NO_SERIAL_DEVICES)
    
    # ----------------------------------------------------------------------
    # I/O Functions
    # ----------------------------------------------------------------------
    
    def write(self, msg):
        try:
            self.serial.write(msg)
        except serial.serialutil.SerialException, V:
            raise Exception(V[0])

    #----------------------------------------------------------------------
    def read(self, length=64):
        try:
            return self.serial.read(length)
        except usb.USBError, V:
            raise Exception(V[0])

    def readProcess(self, cmd):
        self.write(cmd)
        return self.read()

    # ----------------------------------------------------------------------
    # Static Methods
    # ----------------------------------------------------------------------
    @staticmethod
    def avalilablePorts():
        ports = []
        for port in range(30):
            try:
                dev = serial.Serial(os.getenv("PORTNAME")%port)
                ports.append(port)
                dev.close()
            except:
                continue
        return ports

