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

#CONSTANTS
HIGH   = "HIGH"
LOW    = "LOW"
INPUT  = "INPUT"
OUTPUT = "OUTPUT"

#ERRORS
DRIVER_NOT_DEFINED = "Driver is not defined" # -1

class Pinguino():
    
    pinCount = 17
    driver = None
    debug = False
    
    def __init__(self, driver=None):
        if (driver != None):
	    self.setDriver(driver)

    # ---------------------------------------------------------------------- 
    # Connection Functions
    # ---------------------------------------------------------------------- 
    def disconnect(self):
        try:
             self.driver.disconnect()
        except AttributeError:
            return self.driverError("disconnect")

    # ---------------------------------------------------------------------- 
    # Debug Functions
    # ---------------------------------------------------------------------- 
    
    def startDebug(self):
        self.debug = True
        
    # ---------------------------------------------------------------------- 
    def endDebug(self):
        self.debug = False
        
    # ---------------------------------------------------------------------- 
    def getDebug(self):
        return self.debug  
        
    # ---------------------------------------------------------------------- 
    def driverError(self, function):
        if (self.debug):
            raise Exception (function,DRIVER_NOT_DEFINED)
        return -1
    
    # ---------------------------------------------------------------------- 
    # Drivers
    # ---------------------------------------------------------------------- 
    
    def setDriver(self, driver):
        self.driver = driver

    # ---------------------------------------------------------------------- 
    def getDriver(self):
        return self.driver

    # ---------------------------------------------------------------------- 
    # Pinguino Functions
    # ---------------------------------------------------------------------- 

    def pinMode(self, pin, mode):
        try:
             self.driver.pinMode(pin, mode)
        except AttributeError:
            return self.driverError("pinMode")
        
    # ---------------------------------------------------------------------- 
    def digitalWrite(self, pin, write):
        try:
            self.driver.digitalWrite(pin, write)
        except AttributeError:
            return self.driverError("digitalWrite")
        
    # ----------------------------------------------------------------------
    def digitalRead(self, pin):
        try:
            return self.driver.digitalRead(pin)
        except AttributeError:
            return self.driverError("digitalRead") 
    
    # ----------------------------------------------------------------------
    def analogWrite(self, pin, write):
        try:
            self.driver.analogWrite(pin, write)
            return self.analogRead(pin)
        except AttributeError:
            return self.driverError("analogWrite") 
        
    # ----------------------------------------------------------------------
    def analogRead(self, pin):
        try:
            return self.driver.analogRead(pin)
        except AttributeError:
            return self.driverError("analogRead") 
        
    # ----------------------------------------------------------------------
    def eepromRead(self, mem):
        try:
            return self.driver.eepromRead(mem)
        except AttributeError:
            return self.driverError("eepromRead") 
    
    # ----------------------------------------------------------------------
    def eepromWrite(self, mem, value):
        try:
            self.driver.eepromWrite(mem, str(value))
            return self.eepromRead(mem)
        except AttributeError:
            return self.driverError("eepromWrite") 
        
    # ---------------------------------------------------------------------- 
    # Extra Functions
    # ---------------------------------------------------------------------- 

    def delay(self, ms):
        time.sleep(ms/1e3)
        
    # ----------------------------------------------------------------------
    def delayMicroseconds(self, us):
        time.sleep(us/1e6)
        
    # ----------------------------------------------------------------------
    def allOutput(self):
        for n in range(0, self.pinCount-1):
            self.pinMode(n,OUTPUT)
        
    # ----------------------------------------------------------------------
    def allInput(self):
        for n in range(0, self.pinCount-1):
            self.pinMode(n,INPUT)
        
    # ----------------------------------------------------------------------
    def allHigh(self):
        for n in range(0, self.pinCount-1):
            self.pinMode(n,HIGH)

    # ----------------------------------------------------------------------
    def allLow(self):
        for n in range(0, self.pinCount-1):
            self.pinMode(n,LOW)
        
    # ----------------------------------------------------------------------
    def reset(self):
        try:
            return self.driver.reset()
        except AttributeError:
            return self.driverError("reset") 

