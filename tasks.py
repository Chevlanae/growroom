import asyncio
from gpiozero import OutputDevice
from gpiozero.pins import mock


async def power_loop(relay_pin=None, timeOn=60, timeOff=60, id=""):
    '''Infinite loop that turns a relay on and off at the provided intervals'''

    if relay_pin != None:
        relay = OutputDevice(relay_pin)
    else:
        relay = OutputDevice(1, pin_factory=mock.MockFactory())

    try:
        while True:

            relay.on()
            print(id + " on...")

            await asyncio.sleep(int(timeOn))

            relay.off()
            print(id + " off...")

            await asyncio.sleep(int(timeOff))

    except asyncio.CancelledError:
        print(id + " loop cancelled...")
        relay.off()
