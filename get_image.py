# Test script to pull image from GT511C3

import fps, sys, time
import test_raw as raw

if __name__ == '__main__':
    fps =  FPS.FPS_GT511C3(baud=115200)
    fps.SetLED(True) # Turns ON the CMOS LED
	time.sleep(2)
    raw_image = raw.GetRawImg(fps)
    print('We got...')
    print(raw_image)
    print('...end')
    raw.SaveImage('kikkeli2', raw_image)
    fps.SetLED(False)
    FPS.delay(5)
    fps.Close() # Closes serial connection
    print(type(raw_image))
