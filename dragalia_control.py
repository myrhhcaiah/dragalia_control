from xbox_controller import XboxController
import subprocess
import os
from time import sleep
from pyminitouch import safe_connection, safe_device, MNTDevice, CommandBuilder
import tkinter
import pyautogui
from win32gui import GetForegroundWindow, FindWindow, GetWindowRect
import time
import sys
import io
import json
import math

SCRCPY_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scrcpy")
SCRCPY = os.path.join(SCRCPY_ROOT, "scrcpy.exe")
ADB = os.path.join(SCRCPY_ROOT, "adb.exe")
STF_SERVICE_APK = os.path.join(os.path.dirname(os.path.realpath(__file__)), "stfservice", "STFService.apk")


SERIAL = ""

USE_MINITOUCH = False

DRAGALIA_TOUCH_CENTER = None
DRAGALIA_TOUCH_MAX = 200
PHONE_RES = None
POSITIONS = {}

POSITIONS_JSON = os.path.join(os.path.dirname(os.path.realpath(__file__)), "positions.json")


SWIPE_COOLDOWN_MS = 20
LAST_SWIPE = 0
RIGHT_BUMPER_DOWN = False

# keeping touches separate
RIGHT_BUMPER_TOUCH_ID = 2
LEFT_STICK_TOUCH_ID = 1


PROCESSES = []


class JSONFile:
    @staticmethod
    def read_json(filename):
        if os.path.exists(filename):
            with open(filename, encoding='utf-8') as data_file:
                data = json.load(data_file)
                return data
        return {}

def set_device_globals():
    global DRAGALIA_TOUCH_CENTER
    global DRAGALIA_TOUCH_MAX
    global PHONE_RES
    global POSITIONS

    size = AdbDevice.get_screen_resolution(SERIAL)['override_size']
    ratio = f"{size[1]/size[0]:.3f}"

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

        DRAGALIA_TOUCH_CENTER = (original_w/2, original_h/2)
        DRAGALIA_TOUCH_MAX = original_w * .25
        PHONE_RES = (original_w, original_h)
        POSITIONS = positions
        print("-----------initial position data START")
        print(json.dumps(POSITIONS, sort_keys=True, indent=4))
        print("-----------initial position data END")
    else:
        print("missing data from json. please add your device's positioning info to positions.json")
        input("press enter to exit")
        sys.exit(1)


# below is inspired by http://ktnr74.blogspot.com/2013/06/emulating-touchscreen-interaction-with.html

class AdbDevice(object):
    def __init__(self, serial=None):
        self.serial = serial

    def adbshell(self, command):
        args = [ADB]
        if self.serial is not None:
            args.append('-s')
            args.append(self.serial)
        args.append('shell')
        args.append(command)
        return os.linesep.join(subprocess.check_output(args).split('\r\n')[0:-1])

    @classmethod
    def devices(cls):
        return [str(dev.split(b'\t')[0])[2:-1] for dev in subprocess.check_output([ADB, 'devices']).splitlines() if dev.endswith(b'\tdevice')]

    @classmethod
    def get_screen_resolution(cls, serial):
        device_info = subprocess.check_output([ADB, '-s', f'{serial}', 'shell', 'wm size']).splitlines()
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



class MinitouchAdbDevice(AdbDevice):
    def __init__(self, serial=None):
        super().__init__(serial=serial)
        self.minitouch_device = None
        self.mouse_is_down = False

    def scale_xy(self, x, y):
        x2 = int(x * int(self.minitouch_device.connection.max_x) / PHONE_RES[0])
        y2 = int(y * int(self.minitouch_device.connection.max_y) / PHONE_RES[1])
        return (x2, y2)

    def down(self, x, y, touch_id):
        self.mouse_is_down = True

        x, y = self.scale_xy(x,y)
        builder = CommandBuilder()
        builder.down(touch_id, x, y, 50)
        # builder.commit()
        builder.publish(self.minitouch_device.connection)

    def move(self, originx, originy, x, y, touch_id):
        if not self.mouse_is_down:
            self.mouse_is_down = True

            x, y = self.scale_xy(originx, originy)
            builder = CommandBuilder()
            builder.down(touch_id, x, y, 50)
            # builder.commit()
            builder.publish(self.minitouch_device.connection)
            return

        x, y = self.scale_xy(x,y)
        builder = CommandBuilder()
        builder.move(touch_id, x, y, 50)
        # builder.commit()
        builder.publish(self.minitouch_device.connection)

    def release(self, touch_id):
        self.mouse_is_down = False

        builder = CommandBuilder()
        builder.up(touch_id)
        # builder.commit()
        builder.publish(self.minitouch_device.connection)

    def tap(self, x, y):
        x, y = self.scale_xy(x,y)
        self.minitouch_device.tap([(x, y)])

    def swipe(self, x, y, x2, y2):
        x, y = self.scale_xy(x,y)
        x2, y2 = self.scale_xy(x2,y2)
        self.minitouch_device.ext_smooth_swipe([(x, y), (x2, y2)], duration=50, part=4)

    def reset(self):
        set_device_globals()


class ScrcpyAdbDevice(AdbDevice):
    def __init__(self, serial=None, window_title = "DRAGALIA"):
        super().__init__(serial=serial)
        self.window_title = window_title
        self.update_window()
        self.mouse_is_down = False

    def update_window(self):
        TITLE_OFFSET = 30
        self.scr_win = 0
        attempts = 0
        while self.scr_win == 0:
            attempts += 1
            if attempts > 10:
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
        x2 = int(x * self.screen_w / PHONE_RES[0]) + self.left_x
        y2 = int(y * self.screen_h / PHONE_RES[1]) + self.left_y
        return (x2, y2)

    def down(self, x, y, touch_id):
        self.mouse_is_down = True

        x, y = self.scale_xy(x, y)
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()

    def move(self, originx, originy, x, y, touch_id):
        if not self.mouse_is_down:
            originx, originy = self.scale_xy(originx, originy)
            pyautogui.moveTo(originx, originy)
            pyautogui.mouseDown()
            self.mouse_is_down = True
            return

        x, y = self.scale_xy(x,y)
        pyautogui.moveTo(x, y)

    def release(self, touch_id):
        self.mouse_is_down = False
        pyautogui.mouseUp()

    def tap(self, x, y):
        print("--tap")
        print(f"tap: physical phone coords ({x},{y})")
        x, y = self.scale_xy(x,y)
        print(f"tap: desktop coords ({x},{y})")
        pyautogui.mouseUp()
        pyautogui.moveTo(x, y)
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
        set_device_globals()
        self.update_window()


TOUCH_GRACE_PERIOD_MS = 0
class JoystickHandler(object):
    def __init__(self, adb_device):
        self.adb_device = adb_device
        self.press_active = False
        self.touch_id = LEFT_STICK_TOUCH_ID
        self.last_touch_ms = 0

    def update(self, input_data):
        now = current_milli_time()
        if input_data.left_stick_tilted() or input_data.LeftThumb:
            self.last_touch_ms = now

        if self.press_active:
            if input_data.left_stick_tilted():
                def easing(x):
                    if False:
                        return x
                    if x >=0 :
                        return 1 - (1 - x) * (1 - x)
                    else:
                        nx = -x
                        return -(1 - (1 - nx) * (1 - nx))
                def squareToCircle(xSquare, ySquare):
                    if True:
                        return xSquare, ySquare
                    # this is incredibly slow
                    xCircle = xSquare * math.sqrt(1 - 0.5*ySquare**2)
                    yCircle = ySquare * math.sqrt(1 - 0.5*xSquare**2)
                    return xCircle, yCircle
                cx, cy = squareToCircle(easing(input_data.LeftJoystickX), easing(input_data.LeftJoystickY))
                dx = cx * DRAGALIA_TOUCH_MAX
                dy = -cy * DRAGALIA_TOUCH_MAX # invert y
                self.adb_device.move(DRAGALIA_TOUCH_CENTER[0], DRAGALIA_TOUCH_CENTER[1], DRAGALIA_TOUCH_CENTER[0] + dx, DRAGALIA_TOUCH_CENTER[1] + dy, self.touch_id)
            elif input_data.LeftThumb:
                x = DRAGALIA_TOUCH_CENTER[0]
                y = DRAGALIA_TOUCH_CENTER[1]
                self.adb_device.move(DRAGALIA_TOUCH_CENTER[0], DRAGALIA_TOUCH_CENTER[1], x, y, self.touch_id)
            else:
                if now - self.last_touch_ms > TOUCH_GRACE_PERIOD_MS:
                    # end touch
                    self.adb_device.release(self.touch_id)
                    self.press_active = False
        else:
            start_touch = False
            if input_data.left_stick_tilted():
                start_touch = True
            elif input_data.LeftThumb:
                start_touch = True
            if start_touch:
                self.press_active = True
                self.adb_device.down(DRAGALIA_TOUCH_CENTER[0], DRAGALIA_TOUCH_CENTER[1], self.touch_id)


def current_milli_time():
    return round(time.time() * 1000)


def handle_input(controller_output, phone_input, joystick_handler):
    input_data = controller_output.read()

    joystick_handler.update(input_data)

    def tap_position(position_name):
        print(f"tapping {position_name}")
        x, y = POSITIONS[position_name]
        phone_input.tap(x, y)

    pressed = input_data.get_pressed_dict()

    global RIGHT_BUMPER_DOWN
    if "RightBumper" in pressed:
        RIGHT_BUMPER_DOWN = True
        x, y = POSITIONS["CENTER"]
        phone_input.down(x, y, RIGHT_BUMPER_TOUCH_ID)
    elif RIGHT_BUMPER_DOWN:
        RIGHT_BUMPER_DOWN = False
        if len(pressed) == 0:
            phone_input.release(RIGHT_BUMPER_TOUCH_ID)
        RIGHT_BUMPER_DOWN = False

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
            dist = math.sqrt(input_data.RightJoystickX**2 + input_data.RightJoystickY**2)

            dx = input_data.RightJoystickX * DRAGALIA_TOUCH_MAX/dist
            dy = -input_data.RightJoystickY * DRAGALIA_TOUCH_MAX/dist
            x = DRAGALIA_TOUCH_CENTER[0] + dx
            y = DRAGALIA_TOUCH_CENTER[1] + dy
            phone_input.swipe(DRAGALIA_TOUCH_CENTER[0], DRAGALIA_TOUCH_CENTER[1], x, y)

    if "RightTrigger" in pressed:
        phone_input.reset()


def pick_device():
    window = tkinter.Tk()
    window.title('Dragalia Control')

    window.columnconfigure(0, weight=1, minsize=100)
    window.columnconfigure(1, weight=4, minsize=500)

    row = 0

    attached_devices = AdbDevice.devices()
    # append true resolutions
    descriptive_devices = []
    for device in attached_devices:
        size = AdbDevice.get_screen_resolution(device)['override_size']
        ratio = f"{size[1]/size[0]:.3f}"
        descriptive_devices.append(f"{device} {size} - ratio {ratio}")

    tkinter.Label(window, text="Device").grid(row=row, sticky='w')
    device_variable = tkinter.StringVar(window)
    if attached_devices:
        device_variable.set(descriptive_devices[0]) # default value
    device_dropdown = tkinter.OptionMenu(window, device_variable, *descriptive_devices)
    device_dropdown.grid(row=row, column=1, sticky='nesw')

    row +=1

    tkinter.Label(window, text="Input").grid(row=row, sticky='w')
    input_variable = tkinter.StringVar(window)
    input_mechanisms = ["Mouse", "Minitouch"]
    input_variable.set(input_mechanisms[0]) # default value
    device_dropdown = tkinter.OptionMenu(window, input_variable, *input_mechanisms)
    device_dropdown.grid(row=row, column=1, sticky='nesw')

    row +=1

    def start():
        global SERIAL
        serial_raw = str(device_variable.get()).split(" ")[0]
        SERIAL = serial_raw
        global USE_MINITOUCH
        input_mechanism = str(input_variable.get())
        USE_MINITOUCH = input_mechanism == input_mechanisms[1]
        start_controller()
    def exit():
        sys.exit("No device")

    if attached_devices:
        run_button = tkinter.Button(window, text = 'Start', command=start)
        run_button.grid(row=row, column=0, sticky="w")
    else:
        run_button = tkinter.Button(window, text = 'Error: No device detected', command=exit)
        run_button.grid(row=row, column=0, sticky="w")

    window.mainloop()


def start_controller():
    try:
        _start_controller()
    except KeyboardInterrupt:
        for p in PROCESSES:
            p.kill()
        sys.exit(1)


def _start_controller():
    set_device_globals()
    controller_output = XboxController()

    REFRESH_HZ = 120
    WINDOW_TITLE = "DRAGALIA"
    pyautogui.PAUSE = 1 / REFRESH_HZ
    pyautogui.FAILSAFE = True

    scrcpy = subprocess.Popen([SCRCPY, "-s", SERIAL, "-m", "1080", "-b", "4M", "--window-title", WINDOW_TITLE], creationflags=subprocess.CREATE_NEW_CONSOLE)
    PROCESSES.append(scrcpy)

    print("Starting")
    print("Device: ", SERIAL)
    print("Use Minitouch: ", USE_MINITOUCH)

    if USE_MINITOUCH:
        def print_and_execute(command):
            print("running: ", command)
            return subprocess.check_output(command)
        # adb -s XXX install .\stfservice\STFService.apk
        print_and_execute([ADB, "-s", SERIAL, "install", STF_SERVICE_APK])
        # adb -s XXX shell am stopservice --user 0 -a jp.co.cyberagent.stf.ACTION_START -n jp.co.cyberagent.stf/.Service
        try:
            print_and_execute([ADB, "-s", SERIAL, "shell", "am", "stopservice", "--user", "0", "-a", "jp.co.cyberagent.stf.ACTION_START", "-n", "jp.co.cyberagent.stf/.Service"])
        except Exception as e:
            pass
        # adb -s XXX shell am start-foreground-service --user 0 -a jp.co.cyberagent.stf.ACTION_START -n jp.co.cyberagent.stf/.Service
        print_and_execute([ADB, "-s", SERIAL, "shell", "am", "start-foreground-service", "--user", "0", "-a", "jp.co.cyberagent.stf.ACTION_START", "-n", "jp.co.cyberagent.stf/.Service"])
        # adb -s XXX forward tcp:1100 localabstract:stfservice
        print_and_execute([ADB, "-s", SERIAL, "forward", "tcp:1100", "localabstract:stfservice"])
        # adb -s XXX shell pm path jp.co.cyberagent.stf
        apk_path_res = print_and_execute([ADB, "-s", SERIAL, "shell", "pm", "path", "jp.co.cyberagent.stf"])
        # > package:/data/app/~~2bbZh8K8Hby6sPuD_ofIFg==/jp.co.cyberagent.stf-Ypqy3GyRRx5ig_7cZmG8AQ==/base.apk
        print("path result:", apk_path_res)
        # APK = /data/app/~~2bbZh8K8Hby6sPuD_ofIFg==/jp.co.cyberagent.stf-Ypqy3GyRRx5ig_7cZmG8AQ==/base.apk
        apk_path = str(apk_path_res).split(":")[1].strip("'\\rn")

        print("path:", apk_path)

        stf_proc = subprocess.Popen([ADB, "-s", SERIAL, "shell"], stdin = subprocess.PIPE)
        stf_proc.stdin.write(f'export CLASSPATH="{apk_path}"\nexec app_process /system/bin jp.co.cyberagent.stf.Agent\n'.encode('utf-8'))
        stf_proc.stdin.flush()
        PROCESSES.append(stf_proc)

        # Minitouch normally works fine with touch id, but with STFService it errors.
        # Need to think about whether this should be fixed
        global LEFT_STICK_TOUCH_ID
        global RIGHT_BUMPER_TOUCH_ID
        LEFT_STICK_TOUCH_ID = 0
        RIGHT_BUMPER_TOUCH_ID = 0

        phone_input = MinitouchAdbDevice(serial = SERIAL)
        joystick_handler = JoystickHandler(phone_input)
        with safe_device(SERIAL) as minitouch_device:
            phone_input.minitouch_device = minitouch_device
            while True:
                handle_input(controller_output, phone_input, joystick_handler)
    else:
        phone_input = ScrcpyAdbDevice(serial = SERIAL, window_title = WINDOW_TITLE)
        joystick_handler = JoystickHandler(phone_input)
        while True:
            handle_input(controller_output, phone_input, joystick_handler)

if __name__ == '__main__':
    pick_device()
