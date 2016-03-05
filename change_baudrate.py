'''
Created on 08/04/2014

@author: jeanmachuca

SAMPLE CODE:

This is for to change the fingerprint baud rate 9600 to 115200, 
The baudrate 9600 have troubles with response in usb serial devices

Executes this script only once
'''
import fps, sys

if __name__ == '__main__':
    scanner = fps.FPS_GT511C3()
    scanner.change_baud_rate(115200)
    scanner.close()
    pass

