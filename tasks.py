import asyncio
from gpiozero import OutputDevice
from gpiozero.pins import mock

from devices import ADS1115


async def power_loop(relay_pin=None, timeOn=60, timeOff=60, id=""):
    '''Infinite loop that turns a relay on and off at the provided intervals'''

    if relay_pin != None:
        relay = OutputDevice(relay_pin)
    else:
        relay = OutputDevice(1, pin_factory=mock.MockFactory())

    try:
        while True:

            relay.on()
            print(id + " on")

            await asyncio.sleep(int(timeOn))

            relay.off()
            print(id + " off")

            await asyncio.sleep(int(timeOff))

    except asyncio.CancelledError:
        print(id + " loop cancelled")
        relay.off()


async def run_tds(ads1115: ADS1115):
    if(hasattr(ads1115, "interpVoltage") and callable(getattr(ads1115, "interpVoltage"))):
        try:
            print("TDS sensor active")
            ads1115.interpVoltage()
        except asyncio.CancelledError:
            print("TDS sensor inactive")
    else:
        raise ValueError("Given object is missing method %s", ads1115)
