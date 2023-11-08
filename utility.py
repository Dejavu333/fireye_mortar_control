##############################################
# utility functions
##############################################
import RPi.GPIO as GPIO
def cleanup(pins):
    for pinInd in range(0, len(pins)):
        # GPIO.setmode( GPIO.BOARD ) # todo should not be here
        GPIO.output( pins[pinInd], GPIO.LOW )
    GPIO.cleanup()
