from enum import Enum, auto
from domain.entities.mortar import Mortar
from domain.ports.mortar_port import MortarPort

class Usecase: #TODO find a place for this
    def execute():
        pass
# class ErrorLvl(Enum):
#     CRITICAL = auto()
#     WARNING = auto()

# class Error(Enum):
#     NONE: 0
#     BAD_USER_INPUT = ErrorLvl.WARNING



#######################################################################################################
#######################################################################################################
#domain
class Angle:
    value: float

#######################################################################################################
#######################################################################################################


class Request:
    angle: Angle

class Response:
    err: Error

class Tilt_tube_to_angle(Usecase):

    def __init__(self, fetch_tilt_angle_srvc, store_tilt_angle_srvc, actuator_srvc):
        #controller #maybe
        self.fetch_tilt_angle_srvc = fetch_tilt_angle_srvc #maybe call them ports here too
        self.actuator_srvc = actuator_srvc
        self.store_tilt_angle_srvc = store_tilt_angle_srvc
        #presenter #maybe

    def execute(self, req: Request)->Response:
        self.fetch_tilt_angle_srvc.fetch()
        self.actuator_srvc.tilt_tube_to_angle(req.angle.value)
        #if success
        self.store_tilt_angle_srvc.store(req.angle.value)

    def control(T req):
        self.controllerPort.control()
        # if user does smthing than:
        #     response = self.execute(req)
        #     self.present(response)
    
    def present(T res):
        print(res)

    # controller and presnter should be part of IO layer instead they are not ports as it seems