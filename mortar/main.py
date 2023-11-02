# MORTAR
# features:
    # orieentates               manually and remotely   (could be parallel)
    # changes angle of tube     manually and remotely   (could be parallel)
    # fires                     manually and remotely
    # reloads*
    # does leveling*
    # monitors security and emergency stop
    # knows its GEO location and altitude
    # calcs distance to target and angle

# DRONE
# features:
    # get altitude and GEO location of the fire
    # controllable remotely
    # monitors security and emergency lands or returns to base


# CONTROL DEVICE
# features:
    # controls multiple mortars


from abc import ABC, abstractmethod
import RPi.GPIO as GPIO
import time

from constants import CCW, CW
from utility import cleanup

###############################################
# abstract classes
###############################################
class Target(ABC):
    altitude: float = 0.0
    longitude: float = 0.0
    latitude: float = 0.0
    distance: float = 0.0


class Environment(ABC):
    wind: float = 0.0
    temperature: float = 0.0
    humidity: float = 0.0
    pressure: float = 0.0


class Mortar(ABC):
    orientation: float = 0.00
    altitude: float = 0.00
    angle = 0.000
    target: [Target]
    environment: Environment

    @abstractmethod
    def set_tube_orientation(self, chosenOrientation):
        raise NotImplementedError

    @abstractmethod
    def set_tube_angle(self, angle):
        raise NotImplementedError

    @abstractmethod
    def fire(self):
        raise NotImplementedError
    
    @abstractmethod
    def calc_shooting_params(self):
        raise NotImplementedError
    

class StepperMotor(ABC):
    range_of_motion: float
    steps_per_revolution: int 
    steps_per_degree: float
    turn_over_possible: bool
    max_step_delay: float
    min_step_delay: float

    @abstractmethod
    def step(self, step_count, step_delay):  # direction is the sign-/+ of step_count if step_count < 0 then CCW else CW
        raise NotImplementedError
    
    @abstractmethod
    def calc_step_count(self, angle, currentAngle):
        raise NotImplementedError


###############################################
# concrete classes
###############################################
class TinyMortar(Mortar):
    _tubeOrientationMotor: StepperMotor 
    _tubeAngleMotor: StepperMotor 

    def __init__(self, orientationMotor: StepperMotor, angleMotor: StepperMotor):
        self._tubeOrientationMotor = orientationMotor
        self._tubeAngleMotor = angleMotor

    def set_tube_orientation(self, chosenOrientation):
        stepCount = self._tubeOrientationMotor.calc_step_count(chosenOrientation,self.orientation) # todo rename to tube_orientaiton or something       
        self._tubeOrientationMotor.step(step_count=stepCount, step_delay=0.05)

    def set_tube_angle(self, angle):
        stepCount = self._tubeAngleMotor.calc_step_count(angle, self.angle) # todo rename to tube_angle or something
        self._tubeAngleMotor.step(step_count=stepCount, step_delay=0.05)

    def fire(self):
        print("FIRE!!!")

    def calc_shooting_params(self):
        print("Calculating shooting params")


class TinyTubeAngleMotor(StepperMotor):

    def __init__(self):
        self.range_of_motion = 360
        self.steps_per_revolution = 4096
        self.steps_per_degree = self.steps_per_revolution / self.range_of_motion
        self.turn_over_possible = True # todo always false if range_of_motion is less than 360
        self.max_step_delay = 0.1
        self.min_step_delay = 0.01

    def step(self, step_count, step_delay):
        # todo maybe own function # or simplify
        if step_count == 0: return 
        elif step_count < 0: direction = CCW
        else: direction = CW

        if step_delay > self.max_step_delay: step_delay = self.max_step_delay
        elif step_delay < self.min_step_delay: step_delay = self.min_step_delay

        #round step count   # todo maybe own function and must be more precise
        step_count = int(step_count)
        print("step count angleMotor:"+str(step_count))

        # GPIO pins
        in1 = 22
        in2 = 21
        in3 = 36
        in4 = 35
 
        step_sequence = [[1,0,0,1],
                        [1,0,0,0],
                        [1,1,0,0],
                        [0,1,0,0],
                        [0,1,1,0],
                        [0,0,1,0],
                        [0,0,1,1],
                        [0,0,0,1]]

        # setup
        GPIO.setmode( GPIO.BOARD )
        GPIO.setup( in1, GPIO.OUT )
        GPIO.setup( in2, GPIO.OUT )
        GPIO.setup( in3, GPIO.OUT )
        GPIO.setup( in4, GPIO.OUT )

        # initial voltage levels
        GPIO.output( in1, GPIO.LOW )
        GPIO.output( in2, GPIO.LOW )
        GPIO.output( in3, GPIO.LOW )
        GPIO.output( in4, GPIO.LOW )

        motor_pins = [in1,in2,in3,in4]
        motor_step_counter = 0

        try:
            i = 0
            for i in range(abs(step_count)):
                # print ("do",i)
                for pin in range(0, len(motor_pins)):
                    GPIO.output( motor_pins[pin], step_sequence[motor_step_counter][pin] )
                if direction==CW:
                    motor_step_counter = (motor_step_counter - 1) % 8
                elif direction==CCW:
                    motor_step_counter = (motor_step_counter + 1) % 8
                else:
                    print( "direction should always be either CW so True or CCW so False" )
                    cleanup()
                    # exit( 1 ) # todo error handling
                time.sleep( step_delay )
        except Exception as e:
            print(e)
            cleanup(motor_pins)
            # exit( 1 ) # todo error handling
        finally:
            cleanup(motor_pins)
            # exit( 0 ) # todo error handling


    def calc_step_count(self, angle, currentAngle):
        # steps_per_revolution steps is 360° starts from self.orientation otherwise it will be 0°   # todo on startup always mortar should always find 0°
        stepCount = self.steps_per_degree * angle  # should step this many from 0°
        stepCount = stepCount - (self.steps_per_degree * currentAngle) # should step this many from currentAngle
        if self.turn_over_possible==True and stepCount > self.steps_per_revolution/2:
            stepCount = (stepCount - self.steps_per_revolution) # will be negative indicating CCW
        return stepCount    

class TinyTubeOrientationMotor(StepperMotor):

    def __init__(self):
        self.range_of_motion = 360
        self.steps_per_revolution = 200
        self.steps_per_degree = self.steps_per_revolution / self.range_of_motion
        self.turn_over_possible = True # todo always false if range_of_motion is less than 360
        self.max_step_delay = 0.1
        self.min_step_delay = 0.01

    def step(self, step_count, step_delay):
        # todo maybe own function # or simplify
        if step_count == 0: return 
        elif step_count < 0: direction = CCW
        else: direction = CW

        if step_delay > self.max_step_delay: step_delay = self.max_step_delay
        elif step_delay < self.min_step_delay: step_delay = self.min_step_delay

        #round step count   # todo maybe own function and must be more precise
        step_count = int(step_count)
        print("step_count orientationMotor: " + str(step_count))

        DIRPIN = 5     # Direction GPIO Pin
        STEPPIN = 7    # Step GPIO Pin

        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(DIRPIN, GPIO.OUT)
            GPIO.setup(STEPPIN, GPIO.OUT)
            GPIO.output(DIRPIN, CW)

            for x in range(step_count):
                GPIO.output(STEPPIN, GPIO.HIGH)
                time.sleep(step_delay)
                GPIO.output(STEPPIN, GPIO.LOW)
                time.sleep(step_delay)

            time.sleep(1)
            GPIO.output(DIRPIN, CCW)
            for x in range(step_count):
                GPIO.output(STEPPIN, GPIO.HIGH)
                time.sleep(step_delay)
                GPIO.output(STEPPIN, GPIO.LOW)
                time.sleep(step_delay)
        finally:
            GPIO.cleanup()
    
    def calc_step_count(self, angle, currentAngle):
        # 4096 steps is 360° starts from self.orientation otherwise it will be 0°   # todo on startup always mortar should always find 0°
        stepCount = self.steps_per_degree * angle  # should step this many from 0°
        stepCount = stepCount - (self.steps_per_degree * currentAngle) # should step this many from currentAngle

        if self.turn_over_possible==True and stepCount > self.steps_per_revolution/2:
            stepCount = (stepCount - self.steps_per_revolution) # will be negative indicating CCW
        return stepCount    


###############################################
# main
###############################################
if __name__ == "__main__":
    print(CW)
    mortar = TinyMortar(TinyTubeOrientationMotor(), TinyTubeAngleMotor())

    mortar.calc_shooting_params()
    mortar.set_tube_orientation(50)
    mortar.set_tube_angle(356)
    mortar.fire()
