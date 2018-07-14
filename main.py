"""
HAP-python main python with PHAS Accessory
"""
# HAP-python packages
import logging
import signal
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
import pyhap.loader as loader

# import PHAS
from accessories.PHAS_AmpAccessory import AmplifierAccessory
from PHAS.RFHandler import RFHandler

logging.basicConfig(level=logging.INFO)

# Start the accessory on port 51826
driver = AccessoryDriver(port=51826)

# Start the XBee RF handler
rfHandler = RFHandler("/dev/serial0", 115200)

# Create and add the PHAS Amplifier Accessory to the driver
ampAcc = AmplifierAccessory(driver,"Amplifier")
ampAcc.startAmpWithHandler(rfHandler)
driver.add_accessory(accessory=ampAcc)

# We want SIGTERM (kill) to be handled by the driver itself,
# so that it can gracefully stop the accessory, server and advertising.
signal.signal(signal.SIGTERM, driver.signal_handler)

# Start it!
driver.start()
