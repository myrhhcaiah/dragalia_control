### What is 'Dragalia Control'?
An app that mirrors your phone to your computer and maps controller input to the screen. Inputs are mapped specifically for Dragalia Lost.

How does it work?
- Detects Android devices and launches an instance of SCRCPY to show the device screen on their PC.
- Reads controller input from a XBox-like controller and forwards them to the SCRCPY window as useful Dragalia Lost input.

See it in action on YouTube: https://youtu.be/Jt_tPyQo_gA 

This targets Windows 10, 64-bit. The buttons are mapped for the Galaxy S9 and Galaxy S10 Plus. For other devices, see the 'What if my device isn't supported?' section.

Since this uses SCRCPY, the requirements are the same. See https://github.com/Genymobile/scrcpy#requirements.
**_This is not optional._**

You really want quick turn off (180 and 90).

### How to use it
1. Follow the instructions to enable ADB debugging from https://github.com/Genymobile/scrcpy#requirements. There are a few videos on this as well: https://www.youtube.com/results?search_query=set+up+scrcpy
2. Download "dragalia_control.zip" from https://github.com/myrhhcaiah/dragalia_control/releases/
3. Unzip it somewhere.
4. Open Dragalia Lost on your phone. Yes it needs to be open first.
5. Run "dragalia_control.exe" from the place you unzipped it.
4. You'll probably get a prompt on your phone asking you to 'authorize your pc'. Accept.
5. A very ugly UI should appear with a dropdown list of phones. If you only have one phone, press 'Start'.
6. It will take a few seconds to start up, but you should see your phone screen in a SCRCPY window.
7. Pressing your controller buttons should move your mouse around.
8. Drop into a level and go nuts. Button mappings are described in 'What are the button mappings?' below.


### What if my device isn't supported?
You'll want to take screenshots of the game on your phone (Ideally, a normal quest and the skill share menu in Kaleidoscope). 

Then you can edit the positions.json file to add support for your device. You can edit an existing entry like this one:
```
    "2.111": {
        "NOTE": "Galaxy s10+; 1440x3040",
        "C1": [116,260],
        "C2": [116,410],
        "C3": [116,581],
        "C4": [116,725],
        "CENTER": [720,1520],
        "DRAGON": [200,2259],
        "KSS1": [288,1944],
        "KSS2": [586,1944],
        "KSS3": [853,1944],
        "KSS4": [1173,1944],
        "KSS5": [288,2245],
        "KSS6": [586,2245],
        "KSS7": [853,2245],
        "KSS8": [1173,2245],
        "MENU": [1346,234],
        "S1": [512,2601],
        "S2": [800,2601],
        "S3": [1040,2601],
        "S4": [1266,2601],
        "w": 1440,
        "h": 3040
    },
```
Replace "2.111" with your screen ratio, rounded to three decimal places. If you launch 'dragalia_control.exe' with your device attached, you'll see it there.

Then you want to update 'w' and 'h' to be the width and height of your screenshots.

The rest of the values are coordinate locations. It's the distance from the **top left corner** to the point on the screen (so, you'll notice that the "MENU" has a high X value and a low Y value; the high X is because it's very far from the left of the screen and the low Y is because it's very close to the top of the screen). I used IrfanView to do these measurements, but it should be possible in any image editor.

The entries "C1", "C2"... are character slots. The buttons on the top left of the screen for switching characters.
The entries "S1", "S2"... are skill slots, at the bottom of the screen.
The entries "KSS1", "KSS2"... are the skill shares in Kaleidoscope. 1-4 are the top row. 5-8 are the bottom row.

You can hot reload edits with the right trigger.

If you end up adding another device successfully, do get in contact with me either here, on youtube or on reddit, I'd be happy to add the position data to the next release.

### What are the button mappings?
Note: *all actions are performed through manipulating the mouse*. There's code to attempt to interleave actions, but you might still get weirdness if you're moving and pressing a skill.

The left stick is for movement. Pressing down quickly will attack. Pressing down for a long time will force strike.

The right stick is for rolling. Flicking the stick quickly will result in a roll. Pressing down will trigger the dragon transformation.

The face buttons (XYAB) are mapped to skills in order (e.g. X = s1, Y = s2, A = s3, B = s4).

When the left shoulder bumper and the left shoulder trigger are held together, the face buttons change to switch characters.

When only the left shoulder bumper is held, the face buttons change to the top row of the Kaleidoscope skill shares.

When only the left shoulder trigger is held, the face buttons change to the bottom row of the Kaleidoscope skill shares.

The Start and Back buttons both map to the Menu button in game.

The right shoulder bumper is for basic attacks. You can hold it down to force strike.

The right shoulder trigger is a **debug** button. Press it if you've moved the SCRCPY window or if you've updated the positions.json (this will recalculate the app position and the data from positions.json).

### What if I don't have an Xbox-like Controller?
Most controllers know how to pretend to be an Xbox Controller. So, if you have a Logitech or something, it probably just works.

If not, there is usually a way to make your controller pretend to be an Xbox Controller. For example, there's an app for Joycons and the Switch Pro Controller: https://github.com/Davidobot/BetterJoy

### Related projects and credits
"Dragalia Controller" is a project with a similar intention and almost the same architecture. I ended up taking the window computation code. Check it out here: https://github.com/thinkaliker/dragalia-controller

The bulk of the Android phone interaction is mediated by scrcpy. It's incredible for mirroring your phone to your computer even if you're not doing something weird like this: https://github.com/Genymobile/scrcpy

The Xbox controller detection code is based off of code in 'TensorKart', which is a deep learning MarioKart project: https://github.com/kevinhughes27/TensorKart/

A small amount of code to read in data from the Android device was based on http://ktnr74.blogspot.com/2013/06/emulating-touchscreen-interaction-with.html. Note that the blog is largely concerned with using 'sendevent' for input, which is the first thing I tried.

### What else?
- I'd like to get rid of the debug button; it should be automatic.
- There's also been reports that the stick isn't completely smooth. It seems like hardware thing, but I'd like to figure out how to alleviate it.
- Multitouch. Even if you usually play with one finger, being able to move and tap a skill seems like the right thing with a controller.
- Force striking is awkward. I'd like it to be "flick the right stick with a modifier".
