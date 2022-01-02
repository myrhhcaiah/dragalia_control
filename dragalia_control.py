from xbox_controller import XboxController
import subprocess
import os
from time import sleep
import tkinter
import pyautogui
from win32gui import GetForegroundWindow, FindWindow, GetWindowRect
import time
import sys
import io
import json


SCRCPY_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scrcpy")
SCRCPY = os.path.join(SCRCPY_ROOT, "scrcpy.exe")
ADB = os.path.join(SCRCPY_ROOT, "adb.exe")

SERIAL = ""

DRAGALIA_TOUCH_CENTER = None
DRAGALIA_TOUCH_MAX = 200
PHONE_RES = None
POSITIONS = {}

POSITIONS_JSON = os.path.join(os.path.dirname(os.path.realpath(__file__)), "positions.json")

class JSONFile:
    @staticmethod
    def read_json(filename):
        if os.path.exists(filename):
            with open(filename, encoding='utf-8') as data_file:
                data = json.load(data_file)
                return data
        return {}

def set_device_globals(device="OTHER"):
    global PHONE_RES
    global DRAGALIA_TOUCH_CENTER
    global POSITIONS

    size = AdbDevice.get_screen_resolution(SERIAL)['override_size']
    ratio = f"{size[1]/size[0]:.3f}"
    PHONE_RES = AdbDevice.get_screen_resolution(SERIAL)["physical_size"]
    DRAGALIA_TOUCH_CENTER = (PHONE_RES[0]/2, PHONE_RES[1]/2)

    json_data = JSONFile.read_json(POSITIONS_JSON)
    if ratio in json_data:
        print("using data from json")

        positions = json_data[ratio]
        keys = ["CENTER", "DRAGON", "MENU", "C1", "C2", "C3", "C4", "S1", "S2", "S3", "S4", "KSS1", "KSS2", "KSS3", "KSS4", "w", "h"]
        for key in keys:
            if key not in positions:
                print(f"Missing {key} in position data. This may cause errors.")
                if key in ["w", "h"]:
                    print("missing data from json. please add your device's positioning info to positions.json")
                    input("press enter to exit")
                    sys.exit(1)
                else:
                    positions[key] = [10, 10]

        original_w = positions["w"]
        original_h = positions["h"]
        def scale_xy(xy):
            x, y = xy
            x2 = int(x * PHONE_RES[0]/ original_w)
            y2 = int(y * PHONE_RES[1]/ original_h)
            return (x2, y2)
        for p in positions:
            if p not in ["w", "h", "NOTE"]:
                POSITIONS[p] = scale_xy(positions[p])
    else:
        print("missing data from json. please add your device's positioning info to positions.json")
        input("press enter to exit")
        sys.exit(1)


# below is inspired by http://ktnr74.blogspot.com/2013/06/emulating-touchscreen-interaction-with.html

class AdbDevice(object):
    def __init__(self, serial=None, adbpath='adb'):
        self.serial = serial
        self.adbpath = adbpath

    def adbshell(self, command):
        args = [self.adbpath]
        if self.serial is not None:
            args.append('-s')
            args.append(self.serial)
        args.append('shell')
        args.append(command)
        return os.linesep.join(subprocess.check_output(args).split('\r\n')[0:-1])

    @classmethod
    def devices(cls, adbpath='adb'):
        return [str(dev.split(b'\t')[0])[2:-1] for dev in subprocess.check_output([adbpath, 'devices']).splitlines() if dev.endswith(b'\tdevice')]

    @classmethod
    def get_screen_resolution(cls, serial, adbpath='adb'):
        device_info = subprocess.check_output([adbpath, '-s', f'{serial}', 'shell', 'wm size']).splitlines()
        """
        Expected:
        Physical size: 1440x3040
        Override size: 1080x2280
        """
        physical_size = None
        override_size = None
        for size in device_info:
            if b': ' in size:
                wxh_str  = size.split(b': ')[1].split(b'x')
                w, h = int(wxh_str[0]), int(wxh_str[1])

                if physical_size == None:
                    physical_size = (w, h)
                if override_size == None:
                    override_size = (w, h)

                if size.startswith(b"Physical"):
                    physical_size = (w, h)
                if size.startswith(b"Override"):
                    override_size = (w, h)
        return {"physical_size": physical_size, "override_size": override_size}

    def scale_xy(self, x, y):
        raise NotImplementedError()

    def down(self, x, y, touch_id):
        raise NotImplementedError()

    def move(self, x, y, touch_id):
        raise NotImplementedError()

    def release(self, touch_id):
        raise NotImplementedError()

    def tap(self, x, y):
        raise NotImplementedError()

    def swipe(self, x, y, x2, y2):
        raise NotImplementedError()


class ScrcpyAdbDevice(AdbDevice):
    def __init__(self, serial=None, adbpath='adb', window_title = "DRAGALIA"):
        super().__init__(serial=serial, adbpath=adbpath)
        self.minitouch_device = None
        self.window_title = window_title
        self.update_window()
        self.mouse_is_down = False

    def update_window(self):
        TITLE_OFFSET = 30
        #wincenter_x, wincenter_y, screen_w, screen_h, left_x, left_y, right_x, right_y
        self.scr_win = 0
        attempts = 0
        while self.scr_win == 0:
            attempts += 1
            if attempts > 7:
                raise ValueError("Could not detect scrcpy window")

            sleep(1.0)
            self.scr_win = FindWindow(None, self.window_title)

        (left_x, left_y, right_x, right_y) = GetWindowRect(self.scr_win)
        self.screen_w = right_x - left_x
        self.screen_h = right_y - left_y - TITLE_OFFSET
        self.left_y = left_y + TITLE_OFFSET
        self.left_x = left_x
        self.right_x = right_x
        self.right_y = right_y

    def scale_xy(self, x, y):
        x2 = int(x * int(self.screen_w) / PHONE_RES[0]) + self.left_x
        y2 = int(y * int(self.screen_h) / PHONE_RES[1]) + self.left_y
        return (x2, y2)

    def down(self, x, y, touch_id):
        self.mouse_is_down = True

        x, y = self.scale_xy(x,y)
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()

    def move(self, x, y, touch_id):
        if not self.mouse_is_down:
            pyautogui.mouseDown()
            self.mouse_is_down = True

        x, y = self.scale_xy(x,y)
        pyautogui.moveTo(x, y)

    def release(self, touch_id):
        self.mouse_is_down = False
        pyautogui.mouseUp()

    def tap(self, x, y):
        x, y = self.scale_xy(x,y)
        pyautogui.mouseUp()
        pyautogui.click(x, y)
        self.mouse_is_down = False

    def swipe(self, x, y, x2, y2):
        x, y = self.scale_xy(x,y)
        x2, y2 = self.scale_xy(x2,y2)

        pyautogui.mouseUp()
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()
        pyautogui.moveTo(x2, y2)
        pyautogui.mouseUp()
        self.mouse_is_down = False

    def reset(self):
        self.update_window()


class JoystickHandler(object):
    def __init__(self, adb_device):
        self.adb_device = adb_device
        self.press_active = False
        self.touch_id = 1

    def update(self, input_data):
        if self.press_active:
            if input_data.left_stick_tilted():
                x = DRAGALIA_TOUCH_CENTER[0] + input_data.LeftJoystickX * DRAGALIA_TOUCH_MAX
                y = DRAGALIA_TOUCH_CENTER[1] - input_data.LeftJoystickY * DRAGALIA_TOUCH_MAX
                self.adb_device.move(x, y, self.touch_id)
            elif input_data.LeftThumb:
                x = DRAGALIA_TOUCH_CENTER[0]
                y = DRAGALIA_TOUCH_CENTER[1]
                self.adb_device.move(x, y, self.touch_id)
            else:
                # end touch
                self.adb_device.release(self.touch_id)
                self.press_active = False
        else:
            touch_location = None
            if input_data.left_stick_tilted():
                x = DRAGALIA_TOUCH_CENTER[0] + input_data.LeftJoystickX * DRAGALIA_TOUCH_MAX
                y = DRAGALIA_TOUCH_CENTER[1] - input_data.LeftJoystickY * DRAGALIA_TOUCH_MAX
                touch_location = (x, y)
            elif input_data.LeftThumb:
                x = DRAGALIA_TOUCH_CENTER[0]
                y = DRAGALIA_TOUCH_CENTER[1]
                touch_location = (x, y)
            if touch_location != None:
                self.press_active = True
                self.adb_device.down(touch_location[0], touch_location[1], self.touch_id)


def current_milli_time():
    return round(time.time() * 1000)


SWIPE_COOLDOWN_MS = 20
LAST_SWIPE = 0
def handle_input(controller_output, phone_input, joystick_handler):
    input_data = controller_output.read()

    joystick_handler.update(input_data)

    def tap_position(position_name):
        print(f"tapping {position_name}")
        x, y = POSITIONS[position_name]
        phone_input.tap(x, y)

    pressed = input_data.get_pressed_dict()
    # left trigger and bumper are modifiers
    # neither is pressed -> skills
    if "LeftTrigger" not in pressed and "LeftBumper" not in pressed:
        if "Y" in pressed:
            tap_position("S1")
        if "X" in pressed:
            tap_position("S2")
        if "A" in pressed:
            tap_position("S3")
        if "B" in pressed:
            tap_position("S4")
    # one modifier is pressed -> kaleidoscope skillshare deck
    if "LeftTrigger" in pressed and "LeftBumper" not in pressed:
        if "Y" in pressed:
            tap_position("KSS5")
        if "X" in pressed:
            tap_position("KSS6")
        if "A" in pressed:
            tap_position("KSS7")
        if "B" in pressed:
            tap_position("KSS8")
    if "LeftTrigger" not in pressed and "LeftBumper" in pressed:
        if "Y" in pressed:
            tap_position("KSS1")
        if "X" in pressed:
            tap_position("KSS2")
        if "A" in pressed:
            tap_position("KSS3")
        if "B" in pressed:
            tap_position("KSS4")
    # both modifiers are pressed -> pick a party member
    if "LeftTrigger" in pressed and "LeftBumper" in pressed:
        if "Y" in pressed:
            tap_position("C1")
        if "X" in pressed:
            tap_position("C2")
        if "A" in pressed:
            tap_position("C3")
        if "B" in pressed:
            tap_position("C4")

    # right stick
    if "RightThumb" in pressed:
        tap_position("DRAGON")
    # these buttons do the same thing because they're mapped backwards on my controller (Logitech G310)
    if "Start" in pressed or "Back" in pressed:
        tap_position("MENU")

    # flicking the right stick is a roll
    if input_data.right_stick_tilted():
        # cooldown on flicks since they're actually quite slow compared to the polling rate
        now = current_milli_time()
        global LAST_SWIPE
        if now - LAST_SWIPE > SWIPE_COOLDOWN_MS:
            LAST_SWIPE = now

            # all flicks are made equal
            dx = input_data.RightJoystickX
            dy = -input_data.RightJoystickY
            if dx > 0:
                dx = DRAGALIA_TOUCH_MAX
            if dx < 0:
                dx = -DRAGALIA_TOUCH_MAX
            if dy > 0:
                dy = DRAGALIA_TOUCH_MAX
            if dy < 0:
                dy = -DRAGALIA_TOUCH_MAX

            x = DRAGALIA_TOUCH_CENTER[0] + dx
            y = DRAGALIA_TOUCH_CENTER[1] + dy
            phone_input.swipe(DRAGALIA_TOUCH_CENTER[0], DRAGALIA_TOUCH_CENTER[1], x, y)

    if "RightBumper" in pressed:
        tap_position("CENTER")
    if "RightTrigger" in pressed:
        phone_input.reset()


def pick_device():
    window = tkinter.Tk()
    window.title('Dragalia Control')

    window.columnconfigure(0, weight=1, minsize=100)
    window.columnconfigure(1, weight=4, minsize=500)

    attached_devices = AdbDevice.devices()
    # append true resolutions
    descriptive_devices = []
    for device in attached_devices:
        size = AdbDevice.get_screen_resolution(device)['override_size']
        ratio = f"{size[1]/size[0]:.3f}"
        descriptive_devices.append(f"{device} {size} - ratio {ratio}")

    tkinter.Label(window, text="Device").grid(row=0, sticky='w')
    device_variable = tkinter.StringVar(window)
    if attached_devices:
        device_variable.set(descriptive_devices[0]) # default value
    device_dropdown = tkinter.OptionMenu(window, device_variable, *descriptive_devices)
    device_dropdown.grid(row=0, column=1, sticky='nesw')

    def start():
        global SERIAL
        serial_raw = str(device_variable.get()).split(" ")[0]
        SERIAL = serial_raw
        start_controller()
    def exit():
        sys.exit("No device")

    if attached_devices:
        run_button = tkinter.Button(window, text = 'Start', command=start)
        run_button.grid(row=1, column=0, sticky="w")
    else:
        run_button = tkinter.Button(window, text = 'Error: No device detected', command=exit)
        run_button.grid(row=1, column=0, sticky="w")

    window.mainloop()


def start_controller():
    set_device_globals("OTHER")
    controller_output = XboxController()

    REFRESH_HZ = 120
    WINDOW_TITLE = "DRAGALIA"
    pyautogui.PAUSE = 1 / REFRESH_HZ
    pyautogui.FAILSAFE = True

    subprocess.Popen([SCRCPY, "-s", SERIAL, "-m", "1080", "-b", "4M", "--window-title", WINDOW_TITLE], creationflags=subprocess.CREATE_NEW_CONSOLE)

    phone_input = ScrcpyAdbDevice(serial = SERIAL, window_title = WINDOW_TITLE)
    joystick_handler = JoystickHandler(phone_input)
    while True:
        handle_input(controller_output, phone_input, joystick_handler)
        sleep(0.01)



if __name__ == '__main__':
    pick_device()
