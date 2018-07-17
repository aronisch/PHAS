from digi.xbee.io import IOLine, IOMode
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH
from PHAS.RFHandler import RFHandler
import time, threading
import asyncio
import concurrent.futures

POWER_ON_SAFETY_DELAY = 20.0    #Delay in s after a shutdown before powering back up
DEBOUNCING_DELAY = 0.1          #Delay to debounce the switch

class AmplifierAccessory(Accessory):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #Setup the HomeKit Service and its attached Characteristic
        serv_switch = self.add_preload_service('Switch')
        self.amplifier = serv_switch.configure_char('On', setter_callback=self.setAmplifierPower)

        #Setup the power up thread dealing with the delay
        self.powerUpThread = threading.Thread(target = self.powerUpAsync)
        self.validationEvent = threading.Event()
        self.stoppingThreadEvent = threading.Event()
        self.powerUpEvent = threading.Event()
        self.powerUpThread.delay = 20
        self.powerUpThread.start()

    def stop(self):
        print("Stopping Amp Accessory")
        super().stop()
        self.rfHandler.removeRemoteAccessory(self.display_name)
        self.stoppingThreadEvent.set()
        self.powerUpThread.join()

    def startAmpWithHandler(self, accRFHandler):
        #Add the accessory to the RFHandler and set its IOSample callback
        self.rfHandler = accRFHandler
        self.rfHandler.addRemoteAccessory(self.display_name, "0013A2004183853B")
        self.rfHandler.addAccessoryCallback(self.display_name, self.amplifierCallback)

        #Get the current switch state on the amplifier
        self.lastSwitchState = self.rfHandler.getInputStateOfAccessoryPin(self.display_name, IOLine.DIO2_AD2)

        #Force shutdown the amp and notify it to HomeKit users
        self.rfHandler.setDigitalConfigurationOfAccessoryPin(self.display_name, IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_LOW)
        self.amplifier.value = 0
        self.amplifier.notify()

        #Keep track of the shutdown time and last io sample time
        self.lastPowerOffTime = time.time()
        self.lastSendTime = 0

    #Callback when IOSample are received (ie. when the switch is used)
    def amplifierCallback(self, ioSample, sendTime):
        #print("lastSendTime = ", self.lastSendTime, "current sendTime = ", sendTime)
        if not sendTime - self.lastSendTime < DEBOUNCING_DELAY:
            newSwitchState = ioSample.get_digital_value(IOLine.DIO2_AD2)
            self.lastSendTime = sendTime
            if newSwitchState != self.lastSwitchState:
                self.toggleAmplifierPower()
                self.lastSwitchState = newSwitchState
        else:
            print("DEBOUNCE")

    def toggleAmplifierPower(self):
        if self.amplifier.value == 0:
            self.amplifier.client_update_value(1)
        else:
            self.amplifier.client_update_value(0)

    #Threading function dealing with the delay before powering up
    def powerUpAsync(self):
        t = threading.currentThread()
        while not self.stoppingThreadEvent.is_set():
            #Check if a power up is asked and then wait for the delay
            if self.powerUpEvent.is_set():
                print("Power up with delay : ", getattr(t, "delay"))
                #If this event is set, the powerUp is cancelled (the delay is not applied), else power the amp up
                self.validationEvent.wait(getattr(t, "delay"))
                if not self.validationEvent.is_set():
                    self.rfHandler.setDigitalConfigurationOfAccessoryPin(self.display_name, IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_HIGH)
                    print("Powering up")
                    self.powerUpEvent.clear()
                else:
                    self.validationEvent.clear()
                    self.powerUpEvent.clear()

    def setAmplifierPower(self, newState):
        if newState == 1:
            self.amplifier.value = 1
            self.amplifier.notify()
            if time.time() - self.lastPowerOffTime < POWER_ON_SAFETY_DELAY:     #TODO Maybe find a new way to indicate to HomeKit users power up is delayed
                self.powerUpThread.delay = POWER_ON_SAFETY_DELAY - time.time() + self.lastPowerOffTime
                self.powerUpEvent.set()
            else:
                print("Powering up immediately")
                self.rfHandler.setDigitalConfigurationOfAccessoryPin(self.display_name, IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_HIGH)
        else:
            if self.powerUpEvent.is_set():
                print("Cancelling power up")
                self.validationEvent.set()
            else:
                print("Shutdown immediately")
                self.rfHandler.setDigitalConfigurationOfAccessoryPin(self.display_name, IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_LOW)
                self.lastPowerOffTime = time.time()
                self.amplifier.value = 0
                self.amplifier.notify()
