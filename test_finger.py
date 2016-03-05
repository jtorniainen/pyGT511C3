import fps
import time


def test_finger_press():
	scanner = fps.FPS_GT511C3(baud=115200)
	scanner.set_led(True)
	scanner.serial_dbg = False

	try:
		while True:
			finger_status = scanner.is_press_finger()
			if finger_status:
				fps.debug_msg('Finger detected!', ':)')
			else:
				fps.debug_msg('No finger', ':(')
			time.sleep(1)

	except KeyboardInterrupt:
		print('\nExitting')

	scanner.set_led(False)
	scanner.close()


if __name__ == '__main__':
	test_finger_press()
