
'''
Originally
Created on 08/04/2014

@author: jeanmachuca

Modified on 28/02/2016 by github.com/jtorniainen

SAMPLE CODE:

This script is a test for device connected to GPIO port in raspberry pi

For test purpose:

Step 1:
Connect the TX pin of the fingerprint GT511C3 to RX in the GPIO

Step 2:
Connect the RX pin of the fingerprint GT511C3 to TX in the GPIO

Step 3:
Connect the VCC pin of the fingerprint GTC511C3 to VCC 3,3 in GPIO

Step 4:
Connect the Ground pin of fingerprint GT511C3 to ground pin in GPIO


This may be works fine, if don't, try to change the fingerprint baud rate
with baud_to_115200.py sample code


'''
import fps
import time

if __name__ == '__main__':
    fps = fps.FPS_GT511C3()
    fps.SetLED(True)  # Turns ON the CMOS LED
    time.sleep(5)
    fps.SetLED(False)  # Turns ON the CMOS LED
    time.sleep(5)
    fps.Close()  # Closes serial connection
