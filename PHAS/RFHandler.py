from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.io import IOLine, IOMode
from digi.xbee.models.address import XBee64BitAddress
from digi.xbee.exception import TimeoutException
import logging

logger = logging.getLogger(__name__)

class RFHandler:

    def __init__(self, PORT, BAUD_RATE):
        self.baseXbee = XBeeDevice(PORT, BAUD_RATE)
        self.baseXbee.open()
        self.remoteAccessories = {}
        self.accessoryCallbacks = {}
        self.baseXbee.add_io_sample_received_callback(self.ioSampleCallback)

    def stop(self):
        logger.info("Stopping RFHandler")
        self.baseXbee.close()

    def addAccessoryCallback(self, accessoryName, callbackFct):
        self.accessoryCallbacks[accessoryName] = callbackFct

    def addRemoteAccessory(self, accessoryName, xbeeAddressString):
        self.remoteAccessories[accessoryName] = RemoteXBeeDevice(self.baseXbee, XBee64BitAddress.from_hex_string(xbeeAddressString))

    def removeRemoteAccessory(self, accessoryName):
        del self.remoteAccessories[accessoryName]

    def getAccessoriesNames(self):
        return remoteAccessories.keys()

    def getAccessoryNameFromXbeeDevice(self, remoteXbee):
        for key, value in self.remoteAccessories.items():
            if remoteXbee == value:
                return key
        return None

    def setDigitalConfigurationOfAccessoryPin(self, accessoryName, pin, config):        #TODO : CATCH TIMEOUT ERRORS
        sent = 0
        while not sent:
            try:
                self.remoteAccessories[accessoryName].set_io_configuration(pin, config)
                sent = 1
            except TimeoutException:
                logger.debug("TimeOutException in setDigitalConfigurationOfAccessoryPin")

    def getInputStateOfAccessoryPin(self, accessoryName, pin):                          #TODO : CATCH TIMEOUT ERRORS
        while 1:
            try:
                return self.remoteAccessories[accessoryName].get_dio_value(pin)
            except TimeoutException:
                logger.debug("TimeOutException in getInputStateOfAccessoryPin")

    def getDigitalConfigurationOfAccessoryPin(self, accessoryName, pin):                #TODO : CATCH TIMEOUT ERRORS
        while 1:
            try:
                return self.remoteAccessories[accessoryName].get_io_configuration(pin)
            except TimeoutException:
                logger.debug("TimeOutException in getInputStateOfAccessoryPin")

    def ioSampleCallback(self, ioSample, remoteXbee, sendTime):
        currentAccessoryName = self.getAccessoryNameFromXbeeDevice(remoteXbee)
        if currentAccessoryName in self.accessoryCallbacks:
            self.accessoryCallbacks[currentAccessoryName](ioSample, sendTime)
