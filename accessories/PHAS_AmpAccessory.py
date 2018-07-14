from digi.xbee.io import IOLine, IOMode
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH
from PHAS.RFHandler import RFHandler
import time
import asyncio
import concurrent.futures

POWER_ON_SAFETY_DELAY = 20.0    #Delay in s after a shutdown before powering back up

class AmplifierAccessory(Accessory):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_switch = self.add_preload_service('Switch')
        self.amplifier = serv_switch.configure_char('On', setter_callback=self.setAmplifierPower)

    def startAmpWithHandler(self, accRFHandler):
        self.rfHandler = accRFHandler
        self.rfHandler.addRemoteAccessory("Amplifier", "0013A2004183853B")
        self.rfHandler.addAccessoryCallback("Amplifier", self.amplifierCallback)

        self.eventLoop = asyncio.new_event_loop()
        self.amplifierSetterTask = None

        self.lastSwitchState = self.rfHandler.getInputStateOfAccessoryPin("Amplifier", IOLine.DIO2_AD2)
        self.amplifier.value = 0
        self.rfHandler.setDigitalConfigurationOfAccessoryPin("Amplifier", IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_LOW)
        self.amplifier.notify()
        self.lastPowerOffTime = time.time()



    def amplifierCallback(self, ioSample):
        newSwitchState = ioSample.get_digital_value(IOLine.DIO2_AD2)
        if newSwitchState != self.lastSwitchState:
            self.toggleAmplifierPower()
            self.lastSwitchState = newSwitchState

    def setAmplifierPower(self, newState):
        if self.amplifierSetterTask == None:
            self.amplifierSetterTask = self.eventLoop.create_task(self.setAmplifierPowerAsync(newState))
            print("setAmplifierPowerTask created")
            self.eventLoop.run_until_complete(self.amplifierSetterTask)
        else:
            self.amplifierSetterTask.cancel()
            self.amplifierSetterTask = None
            print("setAmplifierPowerTask cancelled")

    async def setAmplifierPowerAsync(self, newState):
        if newState == 1:
            if time.time() - self.lastPowerOffTime < POWER_ON_SAFETY_DELAY:     #TODO Maybe find a new way to indicate to HomeKit users power up is delayed
                print("Delaying power up")
                try:
                    await asyncio.sleep(POWER_ON_SAFETY_DELAY - time.time() + self.lastPowerOffTime)
                    self.rfHandler.setDigitalConfigurationOfAccessoryPin("Amplifier", IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_HIGH)
                    print("End of delay --> Powered up")
                except concurrent.futures.CancelledError:
                    print("Cancelling Power Up")
            else:
                print("Powering up immediately")
                self.rfHandler.setDigitalConfigurationOfAccessoryPin("Amplifier", IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_HIGH)
        else:
            print("Shutdown immediately")
            self.rfHandler.setDigitalConfigurationOfAccessoryPin("Amplifier", IOLine.DIO1_AD1, IOMode.DIGITAL_OUT_LOW)
            self.lastPowerOffTime = time.time()
        self.amplifierSetterTask = None

    def toggleAmplifierPower(self):
        if self.amplifier.value == 0:
            self.amplifier.client_update_value(1)
        else:
            self.amplifier.client_update_value(0)
