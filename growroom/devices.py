import adafruit_dht
import board
import time
import asyncio
from gpiozero import OutputDevice
from gpiozero.pins import mock
from w1thermsensor import W1ThermSensor, Sensor


class DHT22:
    '''Simple class for interacting with the DHT22 sensor using CircuitPython and gpiozero'''

    def __init__(self, dataPin: int, powerPin: int = None):
        '''dataPin is the output pin, and powerPin is the ACC pin on the sensor.
        You can connect the ACC pin to either a GPIO pin and specify the pin number, or a 3.3v/5v pin and leave the powerPin parameter empty.'''

        # set power pin to a mock pin if there is none specified
        if powerPin is None:

            # Mock pin https://gpiozero.readthedocs.io/en/stable/api_pins.html#mock-pins
            self.power = OutputDevice(1, pin_factory=mock.MockFactory())

        else:

            # GPIO pin with a high of 3.3v
            self.power = OutputDevice(powerPin)

        # Adafruit bullshit https://github.com/adafruit/Adafruit_CircuitPython_DHT
        self.device = adafruit_dht.DHT22(getattr(board, "D" + str(dataPin)))

    def read(self):
        '''Reads the sensor and returns the data in a tuple: (humidity, temperature).
        If the sensor is powered off it will be turned on, read, and turned off again.
        If the sensor is malfunctioning or disconnected the function will attempt to read the sensor for 60 seconds, then return (None, None) if there is no reading.'''

        # init
        power_state = self.power.value  # get current power state
        timeout = time.time() + 15  # 15 second timeout
        humidity, temperature = None, None  # result

        self.power.on()  # power sensor on if it isn't already

        # loop until a result is returned, or until timeout has been reached
        while time.time() < timeout:

            try:

                # give the sensor 3 seconds, otherwise a bug will occur where the sensor will output the data from when it was previously powered on.
                time.sleep(3.0)

                # read sensor
                humidity, temperature = self.device.humidity, self.device.temperature

            except RuntimeError:

                # if read operation fails, try again
                continue

            except Exception as error:

                # halt for any other exceptions
                raise error

            finally:

                if humidity and temperature is not None:

                    # turn device off if it was powered off previously
                    if power_state <= 0:
                        self.power.off()

                    # end loop when result is produced
                    break

        return humidity, temperature

    def readOne(self):
        '''Same as the read function except it only reads the sensor once, even if the reading might fail.
        If the reading fails the function returns None.'''

        try:
            # read sensor
            return self.device.humidity, self.device.temperature

        except RuntimeError:
            # return None if reading fails
            return None, None


class DS18B20:
    '''Simple class to interact with the DS18B20 sensor. Uses https://pypi.org/project/w1thermsensor/'''

    def __init__(self, sensor: W1ThermSensor = None):
        '''self.device = sensor or W1ThermSensor(Sensor.DS18B20)'''

        self.device = sensor or W1ThermSensor(Sensor.DS18B20)

    def read(self):
        '''Reads sensor data and returns a float.'''

        return self.device.get_temperature()

    @staticmethod
    def list_devices() -> list[W1ThermSensor]:
        '''Returns result of W1ThermSensor.get_available_sensors(Sensor.DS18B20)'''

        return W1ThermSensor.get_available_sensors(Sensor.DS18B20)

    @staticmethod
    def read_all() -> list[float]:
        '''Reads temperature data from all sensors and returns an array of floats.'''

        result = []

        for device in W1ThermSensor.get_available_sensors(Sensor.DS18B20):
            result.append(device.get_temperature())

        return result


async def power_loop(relay: OutputDevice, timeOn: int, timeOff: int, id=""):
    '''Infinite loop that turns a relay on and off at the provided intervals'''

    print("Power cycle started...")

    while True:

        relay.on()
        print("Relay " + id + " On...")

        await asyncio.sleep(timeOn)

        relay.off()
        print("Relay " + id + " Off...")

        await asyncio.sleep(timeOff)
