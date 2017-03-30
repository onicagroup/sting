#!/usr/bin/env python



from RPi import GPIO
import time

class Sting(object):

    cutoutPin   = 26
    flywheelPin = 19
    triggerPin  = 13
    spinupTime  = 2

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        self._cutout            = False
        self._flywheel          = False
        self._trigger           = False
        self.ready              = False

        self.autoCutout         = False
        self.autoFlywheel       = False
        self.cutoutAssertTime   = None

    def __enter__(self):
        self.ready = True
        GPIO.setup(self.cutoutPin, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.flywheelPin, GPIO.OUT, initial = GPIO.HIGH)
        GPIO.setup(self.triggerPin, GPIO.OUT, initial = GPIO.HIGH)
        return self

    def __exit__(self, *args):
        GPIO.cleanup(self.cutoutPin)
        GPIO.cleanup(self.flywheelPin)
        GPIO.cleanup(self.triggerPin)



    def checkReady(self):
        if not self.ready:
            raise RuntimeError('Class is not in ready state use "with" statement')

    @property
    def cutout(self):
        return self._cutout

    @cutout.setter
    def cutout(self, state):
        self.checkReady()
        self._cutout = state
        if not state and self.trigger:
            self.trigger = False
            time.sleep(.1)
        GPIO.output(self.cutoutPin, not state)
        self.cutoutAssertTime = time.time() if state else None

    @property
    def flywheel(self):
        return self._flywheel

    @flywheel.setter
    def flywheel(self, state):
        self.checkReady()
        self._flywheel = state
        GPIO.output(self.flywheelPin, not state)

    @property
    def trigger(self):
        return self._trigger

    @trigger.setter
    def trigger(self, state):
        self.checkReady()
        self._trigger = state

        if state:
            if not self.cutout:
                self.autoCutout = True
                self.cutout = True

            if not self.flywheel:
                self.autoFlywheel = True
                self.flywheel = True
                time.sleep(self.spinupTime)

            if time.time() - self.cutoutAssertTime < .1:
                time.sleep(.1)

        else: # NOT state
            if self.autoCutout:
                self.autoCutout = False
                self.cutout = False

            if self.autoFlywheel:
                self.flywheel = False

        GPIO.output(self.triggerPin, not state)

__all__ = [Sting]


if __name__ == '__main__':
    sting = Sting()
    with sting:
        sting.trigger = True
        time.sleep(5)
        sting.trigger = False
