# Test script to pull image from GT511C3

import fps 
import sys 
import time
import test_raw as raw

if __name__ == '__main__':
    scanner = fps.FPS_GT511C3(baud=115200)
    scanner.SetLED(True) # Turns ON the CMOS LED
    time.sleep(2)
    #raw_image = raw.GetRawImg(scanner)
    #print('We got...')
    #print(raw_image)
    #print('...end')
    #raw.SaveImage('kikkeli3', raw_image)
    raw.Enroll(scanner, '20')
    scanner.SetLED(False)
    time.sleep(5)
    scanner.Close() # Closes serial connection
    #print(type(raw_image))
