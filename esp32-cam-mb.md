http://8.217.75.21/Industrial/Multilingual/CBAA0046-044_UK.pdf

# CBAA0046

# Product Introduction

TheESP32-CAM development board is a multifunctional board that integrates the ESP32 chip and cameramodule,
suitable for IoT projects, especially those applications that require image capture and transmission.

The ESP32-CAM development board features an ESP32-S chip, an OV2640 camera, a microSD cardslot, and
several GPIO ports for connecting peripherals. 

This module is a small-sized camera module that can work independently as the smallest system.

A new WiFi+Bluetooth dual-mode developmentboard designed based on ESP32,featuring onboard PCB 
antennas and 2 high-performance 32-bit LX6 CPUs. It adopts a 7-stage pipeline architecture and 
has a frequency adjustment range of 80MHz to 240MHz.

ESP32-CAM is an 802.11b/g/nWiFi+BT/BLE SoC module with ultra-low power consumption and deep sleep 
current as low as 6mA, making it suitable for IoT applications with high power consumption requirements.

Easy to use, ESP32-CAM is a miniature module with camera function, equipped with OV2640 camera, GPIO 
for connecting peripherals, and microSD card for storing captured images. It can be directly plugged 
into the motherboard for use.

ESP32-CAM-MB, as an IoT camera module based on ESP32 chip, integrates the functions of microcontroller
unit (MCU) and image sensor, and is suitable for various application scenarios that require image
capture and wireless transmission.

It can be widely used in various IoT scenarios, including home smartdevices, industrial wireless control,
wireless monitoring, QR wireless recognition, wireless positioning system signals, and other IoT 
applications.

It is an ideal solution for IoT applications.


# PerformanceIntroduction:

Processor: Dualcore 32-bit LX6 microprocessor
Mainfrequency: up to 240MHz
Computing capability: up to 600 DMIPS
SPI Flash： Default 32mbit
Builtin SRAM: 520KB
External PSRAM: 4MB/8MB External PSRAM: 4MB/8MB
Wi-Fi： 802.11b/G/n/e/i
Bluetooth: Bluetooth4.2 BR/EDR and BLE standards
Supports interfaces (2Mbps): UART, SPI, I2C, PWM
Support TF card: Supports up to 4G
IO ports: 9
Serial port speed: default 115200bps
Spectrum range: 2400~2483.5 MHz Spectrum range: 2400~2483.5 MHz
Antenna shape: Integrated PCB, 2dBi gain
Working temperature: -20℃～70℃
Storage environment: -40℃～125℃，<90% RH


# OV2640 Image Sensor:

OV2640 is a widely used camera module, mainly used in embedded systems and IoT devices,
especially in conjunction with development boards such as Arduino, ESP32, and Raspberry Pi.

The performance parameters are as follows:

1.1.    Imagesensor: OV2640 adopts a 1/4inch CMOS sensor, which can provide good image quality.

2.      Resolution: Supports multiple resolutions, 2 million pixels, easyto choose according
        to application scenarios.

3.      Frame rate: At maximum resolution,the OV2640 can achieve a shooting speed of approximately 
        15 frames per second (fps).
        Reducing the resolution can increase the framerate, for example, it can reach over
        30 fps in VGA mode.

4.      Image output format: JPEG (only supports OV2640) BMP、GRAYSCALE


# Preparation stage:

1.      Hardware preparation: Ensure that you have the ESP32-CAM module, USBtoTTL module (for data 
        transfer), power adapter or battery, and necessary connection cables such as DuPont cables.

2.      Software preparation: Install Arduino IDE. If your Arduino IDE version does not include
        development support for ESP32, you will need to install an additional ESP32 development board 
        package. You can find the option to manage IDE packages in the preferences of Arduino IDE, and
        then search for and install the "ESP32" package.
            https://dl.espressif.com/dl/package_esp32_index.json

3.      copy the package_esp32_index.json in the Arduino folder inside you arduino ide installation
        (typically c:/Users/<user>/AppData/Local/Arduino15/  where you have other json files)

4.      Restart arduino ide, go to tools, select reload board data, then go again in tools and choose
        manage libraries. Now click the icon of the board on the left, write °esp32° in the library 
        manager filter search and select esp32 by Espressif Systems, then Install (version 3.3.5)
        The more-info points to this github repo
                https://github.com/espressif/arduino-esp32

        I get the context deadline exceeded error
        ```
        Tool arduino:dfu-util@0.11.0-arduino5 already installed
            Downloading packages
            esp32:esp-rv32@2511
            Failed to install platform: 'esp32:esp32:3.3.5'.
            Error: 4 DEADLINE_EXCEEDED: context deadline exceeded
        ```
        To fix this error, a longer network timeout is required. We need to change a setting in 
        arduino-cli.yaml
        see https://esp32.com/viewtopic.php?t=47384 
        go to edit 
            C:\Users\mgua\.arduinoIDE\arduino-cli.yaml
        and add the following
        ```
            network:
                connection_timeout: 300s
        ```
        close and reopen arduino ide and retry the install of the esp32 packages:
        Tool arduino:dfu-util@0.11.0-arduino5 already installed
        ```
            Downloading packages
            esp32:esp-rv32@2511
            esp32:esp-x32@2511
            esp32:esp32-arduino-libs@idf-release_v5.5-9bb7aa84-v2
            esp32:esptool_py@5.1.0
            esp32:mklittlefs@4.0.2-db0513a
            esp32:mkspiffs@0.2.3
            esp32:openocd-esp32@v0.12.0-esp32-20250707
            esp32:riscv32-esp-elf-gdb@16.3_20250913
            esp32:xtensa-esp-elf-gdb@16.3_20250913
            esp32:esp32@3.3.5
            Installing esp32:esp-rv32@2511
            Configuring tool.
            esp32:esp-rv32@2511 installed
            Installing esp32:esp-x32@2511
            Configuring tool.
            esp32:esp-x32@2511 installed
            Installing esp32:esp32-arduino-libs@idf-release_v5.5-9bb7aa84-v2
            Configuring tool.
            esp32:esp32-arduino-libs@idf-release_v5.5-9bb7aa84-v2 installed
            Installing esp32:esptool_py@5.1.0
            Configuring tool.
            esp32:esptool_py@5.1.0 installed
            Installing esp32:mklittlefs@4.0.2-db0513a
            Configuring tool.
            esp32:mklittlefs@4.0.2-db0513a installed
            Installing esp32:mkspiffs@0.2.3
            Configuring tool.
            esp32:mkspiffs@0.2.3 installed
            Installing esp32:openocd-esp32@v0.12.0-esp32-20250707
            Configuring tool.
            esp32:openocd-esp32@v0.12.0-esp32-20250707 installed
            Installing esp32:riscv32-esp-elf-gdb@16.3_20250913
            Configuring tool.
            esp32:riscv32-esp-elf-gdb@16.3_20250913 installed
            Installing esp32:xtensa-esp-elf-gdb@16.3_20250913
            Configuring tool.
            esp32:xtensa-esp-elf-gdb@16.3_20250913 installed
            Installing platform esp32:esp32@3.3.5
            Configuring platform.
            Platform esp32:esp32@3.3.5 installed
        ```

        once the install is done, we need to select the correct board
        Tools/reload board data/

        The default antenna for ESP32cam is an external antenna, and the signal may not be very good 
        without an external antenna. Check if the jumper 0K resistor on the antenna connector is in 
        the correct position for the desired antenna.


USB to SERIAL adapter and related drivers

i need to prepare my arduino ide to manage a new microcontroller board
I am attaching the only available documentation.
I went on and downloaded the json file from  https://dl.espressif.com/dl/package_esp32_index.json
then installed it (a timeout extension was required in arduino-cli.yaml)

Now i can not "see" the board via usb, and I think I need the USB driver for the interface which is connecting the ESP32 cam board to the usb cable. This thing should be called USB-SERIAL CH340 and in device manager should appear within COM and LPT ports. 
I do not see these in my device manager.
I am not sure if the fact they are missing means my USB cable is not good enough. 
What can I do?

this should be the CH340 driver
https://www.wch-ic.com/downloads/CH341SER_EXE.html 
I installed the driver (CH341SER.EXE). (maybe this installation was not strictly needed)


most likely problem: cable without data lines
Once i replaced the cable, the arduino IDE allowed me to "see" many boards. 

I choose the AI-Thinker ESP32-CAM, as instructed by the pdf document, 
connected to the COM3 Serial port (USB)

Now Arduino IDE shows AI Thinker ESP32-CAM in the active ucontroller selector

following the pdf instructions (with a bit of fantasy), i now go for the chip-id:
File/Examples/(Examples for AI Thinker ESP32-CAM)/Esp32/Chip-ID/GetChipID

this opens a GetChipID.ino sketch

```
/* The true ESP32 chip ID is essentially its MAC address.
This sketch provides an alternate chip ID that matches
the output of the ESP.getChipId() function on ESP8266
(i.e. a 32-bit integer matching the last 3 bytes of
the MAC address. This is less unique than the
MAC address chip ID, but is helpful when you need
an identifier that can be no more than a 32-bit integer
(like for switch...case).

created 2020-06-07 by cweinhofer
with help from Cicicok */

uint32_t chipId = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  for (int i = 0; i < 17; i = i + 8) {
    chipId |= ((ESP.getEfuseMac() >> (40 - i)) & 0xff) << i;
  }

  Serial.printf("ESP32 Chip model = %s Rev %d\n", ESP.getChipModel(), ESP.getChipRevision());
  Serial.printf("This chip has %d cores\n", ESP.getChipCores());
  Serial.print("Chip ID: ");
  Serial.println(chipId);

  delay(3000);
}

```

I compile this, then upload it. in the serial monitor i see garbage, 
that becomes clear once i set speed to 115200

```
[...]
13:42:46.185 -> Chip ID: 12699436
13:42:49.184 -> ESP32 Chip model = ESP32-D0WD-V3 Rev 301
13:42:49.184 -> This chip has 2 cores
[...]
``





