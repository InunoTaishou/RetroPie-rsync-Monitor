import RPi.GPIO as GPIO
from time import sleep
import os
from subprocess import check_output, CalledProcessError
import threading

# Disable warnings about pins and set the mode to board
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Pin on the GPIO pinout used to control the LED(s)
led_pin = 8


# LED Controller class
# Wrapper for toggling the LED(s)
class LedController:
    def __init__(self, led_pin, led_on=True):
        self.led_pin = led_pin
        self.led_on = led_on

        GPIO.setup(self.led_pin, GPIO.OUT)
        self.set_state(led_on)

    def toggle_led(self):
        self.led_on = not self.led_on
        GPIO.output(self.led_pin, self.led_on)

    def set_state(self, state):
        self.led_on = state
        GPIO.output(self.led_pin, self.led_on)


# rsync Monitor class
# Checks the process list to see if rsync is running
class RsyncMonitor:
    # LedController, delay between flashes
    def __init__(self, led_controller, delay=0.2):
        # User can create the class using a pin number or supply
        # a LedController
        if isinstance(led_controller, int):
            if 40 >= led_controller >= 3:
                led_controller = LedController(led_controller)

        if not isinstance(led_controller, LedController):
            print('Invalid LedController')
            raise ValueError

        if not (isinstance(delay, int) or isinstance(delay, float)):
            print('delay must be int or float')
            raise ValueError

        self.led_controller = led_controller
        self.delay = delay
        self.__flashing = None
        self.__stop_event = None
        self.__rsync_pid = 0

    # Function used for flashing the LED(s)
    # Not inside the main while loop, this is threaded so the flashing
    # is never interrupted from the sleeps
    def __flash(self, stop_event, led, delay):
        led_default_state = led.led_on

        # While the stop event has not been set, keep flashing
        while not stop_event.is_set():
            led.toggle_led()
            stop_event.wait(delay)

        # Put the LED back to the default state we found it in
        led.set_state(led_default_state)

    # Returns true if rsync is running (copying)
    def is_copying(self):
        if self.__rsync_pid:
            # Saved the last rsync PID, check to see if
            # it still exists
            try:
                os.kill(self.__rsync_pid, 0)
            except OSError:
                # Last PID does not exist, continue
                self.__rsync_pid = 0
                pass
            else:
                # Last PID still exists, still running
                return True
        try:
            # Check to see if rsync exists
            check_output(['pidof', 'rsync'])
            # rsync exists, return true
            return True
        # When the process does not exist, subprocess raises a CalledProcessError
        # rsync is not running, return False
        except CalledProcessError:
            return False

    # Monitor function, main loop for this class
    def monitor(self):
        try:
            while True:
                # If rsync is running (copying)
                if self.is_copying():
                    # Not currently flashing the LED(s)
                    if not self.__flashing:
                        # Create the stop event, thread, and start it (start flashing)
                        self.__stop_event = threading.Event()
                        self.__flashing = threading.Thread(target=self.__flash, args=(self.__stop_event, self.led_controller, self.delay))
                        self.__flashing.start()
                # Currently flashing but rsync is no longer running
                elif self.__flashing:
                    # Stop the thread
                    self.__stop_event.set()
                    # Clear it
                    self.__flashing = self.__stop_event = None
                    # Slight delay while we wait for the thread to close
                    sleep(0.1)

                sleep(0.25)
        # Some error happened, close out of this gracefully
        except:
            if self.__flashing:
                self.__stop_event.set()
            return

led_controller = LedController(led_pin)
rsync_monitor = RsyncMonitor(led_controller)

rsync_monitor.monitor()

GPIO.cleanup()
