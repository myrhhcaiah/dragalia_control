from inputs import get_gamepad
import math
import threading

DEAD_ZONE = .06

class InputData(object):
    BUTTONS = ["LeftTrigger", "RightTrigger", "LeftBumper", "RightBumper", "A", "B", "Y", "X", "LeftThumb", "RightThumb", "Back", "Start", "LeftDPad", "RightDPad", "UpDPad", "DownDPad"]

    def __init__(self):
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

    def __repr__(self):
        data = []
        data.append("-- InputData start")
        if self.LeftJoystickY != 0 or self.LeftJoystickX != 0:
            data.append(f"LeftJoystick [{self.LeftJoystickX}, {self.LeftJoystickY}]")
        if self.RightJoystickY != 0 or self.RightJoystickX != 0:
            data.append(f"RightJoystick [{self.RightJoystickX}, {self.RightJoystickY}]")
        for button in InputData.BUTTONS:
            val = getattr(self, button)
            if val != 0:
                data.append(f"pressed {button}")
        data.append("-- InputData end\n")
        return "\n".join(data)

    def left_stick_tilted(self):
        return self.LeftJoystickY != 0 or self.LeftJoystickX != 0

    def right_stick_tilted(self):
        return self.RightJoystickY != 0 or self.RightJoystickX != 0

    def get_pressed(self):
        pressed = []
        for button in InputData.BUTTONS:
            val = getattr(self, button)
            if val != 0:
                pressed.append(button)
        return pressed


# below is from: https://github.com/kevinhughes27/TensorKart/blob/master/record.py
class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()


    def read(self): # return the buttons/triggers that you care about in this methode
        result = InputData()

        if self.LeftJoystickY > DEAD_ZONE or self.LeftJoystickY < -DEAD_ZONE:
            result.LeftJoystickY = self.LeftJoystickY
        if self.LeftJoystickX > DEAD_ZONE or self.LeftJoystickX < -DEAD_ZONE:
            result.LeftJoystickX = self.LeftJoystickX
        if self.RightJoystickY > DEAD_ZONE or self.RightJoystickY < -DEAD_ZONE:
            result.RightJoystickY = self.RightJoystickY
        if self.RightJoystickX > DEAD_ZONE or self.RightJoystickX < -DEAD_ZONE:
            result.RightJoystickX = self.RightJoystickX

        result.LeftTrigger = self.LeftTrigger
        result.RightTrigger = self.RightTrigger
        result.LeftBumper = self.LeftBumper
        result.RightBumper = self.RightBumper
        result.A = self.A
        result.X = self.X
        result.Y = self.Y
        result.B = self.B
        result.LeftThumb = self.LeftThumb
        result.RightThumb = self.RightThumb
        result.Back = self.Back
        result.Start = self.Start
        result.LeftDPad = self.LeftDPad
        result.RightDPad = self.RightDPad
        result.UpDPad = self.UpDPad
        result.DownDPad = self.DownDPad

        return result


    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.X = event.state
                elif event.code == 'BTN_WEST':
                    self.Y = event.state
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state




if __name__ == '__main__':
    joy = XboxController()
    while True:
        print(joy.read())
