# PHAS
PHAS - Personal Home Automation System - Based on HomeKit and XBee

HomeKit Automation System using a Raspberry Pi Zero W as its base and XBee3 RF modules to communicate with accessories.
The HomeKit server used is [HAP-python](https://github.com/ikalchev/HAP-python/) and is provided by ikalchev. 

As the XBee3 RF's firmware doesn't support IO control from microPython for now, the IO are controlled in API mode with AT commands directly from the digi [python-xbee](https://github.com/digidotcom/python-xbee) library.

## Installation
1. Follow the installation instructions from HAP-python and python-xbee
2. Replace the content of ```accessories``` from HAP-python with our own
3. Replace ```main.py``` with our own

## Hardware
- The hub system based on Raspberry Pi Zero W and XBee3 RF
- Accessories : For now, there is only a switch for my HiFi tube amplifier (power up or shutdown through HomeKit or the original switch)
- See [PHAS-Hardware](https://github.com/aronisch/PHAS-Hardware)
