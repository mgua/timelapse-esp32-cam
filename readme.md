# timelapse-esp32-cam

A wireless esp32 camera module to create timelapse videos

A version with pictures of this file can be found at [https://marco.guardigli.it/2026/01/capturingtimelapses.html]

My wife recently bought a microgreens growing kit. 

It is a simple kit with plastic trays, several varieties of seeds. 

You add water on a  simple layer of wet paper, and in two weeks you can eat lettuce from your microgarden.

The german company producing this kit, [https://zengreens.de] did a good job in making the process easy and fun. 

With the growing microjungle on the table next to the kitchen window, I had the idea of creating time-lapse movies of the growing plants.



## ESP32 Cam Kit hardware

So I bought on Amazon a ESP32 Cam kit. Actually I bought a pack of two, for approx 20e. There are many options for similar products on Amazon. Mine were on special offer being a bit older with USB female socket requiring a cable with the depicted connector.




The ESP32 Cam kit has 2 small circuit boards, to be connected together. The lower one has the usb connector and reset button, and powers the upper one, which has the ESP32 chip, the microsd socket, and the camera, which is connected with a short flex cable. An external antenna with coax connection cable is included (i did not use it).

Next to the camera connector there is a bright LED that can help in taking pictures in low light.


The specific camera sensor included in my kit is based on the OV2640 image sensor, equipped with a simple fixed focus optic and an IR filter. The sensor is a 2Mpixel sensor, and supports multiple resolutions.
The optical barrel can rotate to adjust the focus, but there is a drop of glue in place that is locking the focus in a fixed position. 




On the same board where the camera connector is, but on the lower side, there are the microcontroller ESP32s, the circuit printed antenna, the connector for the external antenna, and the selector jumper that requires desoldering and resoldering tools ans skills to enable and use the external antenna for wifi, having the circuit printed antenna for Bluetooth/BLE.
By default my boards were configured with on-board antenna active. Activating the external antenna requires some decent solder/desolder experience. A small SMD ceramic condenser has to be repositioned.

The specific ESP32 microcontroller on my board is equipped with 2 LX6 CPU cores. It supports wireless 802.11b/g/n Wi Fi+BT/BLE, ultra-low power consumption and deep sleep current as low as 6mA. 









Here is a pin mapping diagram taken from the instruction manual, describing how the camera connector and the microsd card slot are connected to the ESP32:






The jumper/condenser repositioning is not easy, requires a very small tip in your soldering iron, and some skills with copper braid and flux for SMD (surface mounted devices) component removing and repositioning. 



I decided to go with the default, circuit embedded antenna. 
In this single configuration either you use Bluetooth or WiFi, but not both at the same time.



Some other hardware is needed: a 5V power supply and a microUSB cable that is allowing data flow. Consider that not all the USB cables are equipped with internal data wiring: most of them are just recharging cables. To program this ESP32 kit you need a microUSB cable which is data capable.

I also used a third hand tool, which was effective in keeping the camera in position, over the microgreens tray.








## Software setup

On my windows 11 computer I used the following software:

- Arduino IDE
- USB to Serial driver
- Arduino IDE extensions for ESP32
- windows package manager (winget)
- python interpreter (I used Python 3.12)
- a python virtual environment with additioanal components installed via pip (python package manager)
- ffmpeg tools to better compress output video


## Installation details:

I installed the Arduino IDE, from [https://arduino.cc] 

I too installed the USB serial driver so to "see" the USB to serial interface needed for the Arduino IDE to talk with the ESP32. (this driver may be or may not be needed).

I got this ( i renamed the installer to usb_serial_driver_CH341SER.EXE) from [https://www.wch-ic.com/downloads/ch341ser_exe.html] 

After this setup, connecting the ESP32 kit with an appropriate cable to the laptop, produced the typical new device detected sound, and the device was visible in device manager (launch devmgmt from windows search box) as connected to a serial port (COM3 in my case).

The Arduino IDE has to be extended in order to support the ESP32, this will bring in several software components, libraries and example to support many physical devices using ESP32 chip, in its various forms. These extensions may be tricky to install. They are typically described in a .json file which has to be placed in the appropriate Arduino IDE folder. The json file contains instructions to download the packages. My device had a qrcode pointing to a url where a simple manual was available. The manual was a bit tricky to interpret, being partially in chinese. 

For my device, I downloaded the .json file from [https://dl.espressif.com/dl/package_esp32_index.json]

This package_esp32_index.json file has to be put in your in Arduino IDE installation folder, where you have other .json files. 

In my setup the folder is: 

```
c:/Users/<user>/AppData/Local/Arduino15/
```

Restart arduino ide, go to tools, select reload board data, then go again in tools and choose manage libraries. Now click the icon of the board on the left, write "esp32" in the library manager filter search and select "esp32 by Espressif Systems", then Install (version 3.3.5)

The more-info points to this github repo [https://github.com/espressif/arduino-esp32]

Donwload started, but soon I got a "context deadline exceeded" error

To fix this error, a longer network timeout is required. 

We need to change a setting in arduino-cli.yaml (This file sits in the .arduinoIDE hidden folder in your home directory). See https://esp32.com/viewtopic.php?t=47384 

Edit the file 

```
C:\Users\<user>\.arduinoIDE\arduino-cli.yaml
```

and add the following lines, respecting indentation:

```
network:

    connection_timeout: 300s
```

Then save, close and reopen Arduino IDE and retry the install of the esp32 packages: this may require some time. 

Once install is done, we can select the board in the Arduino (tools/board...) board manager. In my case (from the manual) the board name is AI Thinker ESP32-CAM.

Now Arduino IDE is ready to communicate, compile and send programs to the ESP32 board. You can experiment with the examples available in the library. 

My code for camera management is shamelessly copied from the provided camera example, with some customization for the camera sensor (OV2640, designated as CAMERA_MODEL_AI_THINKER) in the board.config.h file and in the main file, to get chip id unique identifier, perform WiFi initialization and start camera webserver.

The following are the specific pin informations, as related to my camera, describing how the camera cable signals are mapped to the ESP32 pins. 
This is important if you want to use the board to read other sensors, like temperature/humidity etc, and you do not want these extra sensor connections to interfere with the camera signals.

```
[...]
#elif defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM  32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  0
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27

#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    21
#define Y4_GPIO_NUM    19
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM    5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

// 4 for flash led or 33 for normal led
#define LED_GPIO_NUM   4
[...]
While supported, I did not use the microsd slot. I left it empty.
```


For python, I used python 3.12, but you can go with any other versions. python 3.14 is also available now. From a powershell command prompt (write "powershell" in the windows search box) you can perform the installation using winget,  

```
winget install Python.Python.3.12
```

During the installation I recommend to install the py launcher.

Once python is installed, close and re-open the command window (so that path gets updated) and you are ready to create the virtual environment.

From a powershell command prompt run the following commands:

```
cd $env:USERPROFILE
py -3.12 -m venv_timelapse
```

Now you created a new python 3.12 virtual environment. This is a folder where your python libraries and components are. 

Now create a folder for your code: conventionally we create a code folder with the same name as its environment (but without the "venv_" prefix). Your code does typically go there.

```
mkdir timelapse
```

Now let's activate and upgrade the new virtual environment: You will see the prompt change once the virtual environment is active. We proceed to updgrade python installation program (pip) and its database, before installing the packages we require.

```
. ./venv_timelapse/Scripts/Activate.ps1
python -m pip install pip --upgrade
```

we are now ready to install the python components we need. Pip will take care of installing the related hierarchical dependencies that are needed. Launching pip within python (python -m pip) ensures that we are using the current python version of pip.

```
python -m pip install pillow numpy requests opencv-python
```


I built the python software with substantial support from Anthropic Claude.ai

There are two python scripts: esp32cam_timelapse.py and assemble_timelapse.py. 

- esp32cam_timelapse.py controls timelapse image acquisition from the camera device, regularly connecting to the ESP32 webserver via its wireless IP address and asking to take a picture.

This software controls camera resolution, led light, sensor parameters, and passes requests to the ESP32 to retrieve each image as a static .jpeg picture. All the parameters are sent to the ESP32 via its webserver interface, which is quite powerful and allows deep control over camera sensor and image processing happening on the ESP32. 

All the pictures are recovered with identical resolution settings, and saved with names in the format prefix_xxxxx where xxxxx is a progressive integer counter. You can ask to start from a specific value. 

Together with each picture the software generates a metadata json text file, with image count, paramters, and acquisition timedate.

The software is controlled via command line interface.



- assemble_timelapse.py takes care of preparing the timelapse movie once the images have been collected. 

This software has command line inteface. It relies on the same virtual environment of the image capture tool. 

It can compress the movie in a much compact format, using ffmpeg tools. This has tbe run once the individual timelapse pictures have been collected and uniformly processed to have a progression frame id and identical resolution and aspect ratio. Movie preparation adds a bottom line where image acquisition timestamps are added to each frame, so to precisely identify each event. Datetime information are not taken from picture file date/time, but from each picture metadata file, as produced by esp32_timelapse.py .



All the mentioned code can be found on [https://github.com/mgua/timelapse-esp32-cam.git]



And here you have our microgreens growing timelapse movie




Happy hacking!

