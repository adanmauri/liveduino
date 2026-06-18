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

class AbstractDriver(object):

    def __init__(self):
        pass

    # ----------------------------------------------------------------------
    # Pinguino Functions
    # ----------------------------------------------------------------------

    def pinMode(self, pin, mode):
	print pin
        cmd = 'pinMode(%s,%s)' % (pin,mode)
        self.write(cmd)
        
    # ---------------------------------------------------------------------- 
    def digitalWrite(self, pin, write):
        cmd = 'digitalWrite(%s,%s)' % (pin,write)
        self.write(cmd)
        
    #----------------------------------------------------------------------
    def digitalRead(self, pin):
        cmd = 'digitalRead(%s)' % (pin)
        return self.readProcess(cmd)
    
    #----------------------------------------------------------------------
    def analogWrite(self, pin, write):
        cmd = 'analogWrite(%s,%s)' % (pin,write)
        self.write(cmd)
        
    #----------------------------------------------------------------------
    def analogRead(self, pin):
        cmd = 'analogRead(%s)' % (pin)
        return self.readProcess(cmd)
        
    #----------------------------------------------------------------------
    def eepromRead(self, mem):
        cmd = 'eepromRead(%s)' % (mem)
        return self.readProcess(cmd)
    
    #----------------------------------------------------------------------
    def eepromWrite(self, mem, value):
        cmd = 'eepromWrite(%s,%s)' % (mem,value)
        self.write(cmd)
        
    #----------------------------------------------------------------------
    def delay(self, ms):
        pass
        
    #----------------------------------------------------------------------
    def delayMicroseconds(self, us):
        pass
        
    #----------------------------------------------------------------------
    def allOutput(self):
        pass
       
    #----------------------------------------------------------------------
    def reset(self):
        cmd = 'reset'
        self.write(cmd)

