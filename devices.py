import adafruit_dht
import board
import asyncio
import smbus
import time
import io
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from gpiozero import OutputDevice
from gpiozero.pins import mock
from w1thermsensor import W1ThermSensor, Sensor


class Camera():
    class StreamingOutput(io.BufferedIOBase):

        def __init__(self):
            self.frame = None
            self.condition = Condition()

        def write(self, buf):
            with self.condition:
                self.frame = buf
                self.condition.notify_all()

    def __init__(self):

        self.module = Picamera2()
        self.module.video_configuration.size = (620, 480)
        self.output = self.StreamingOutput()
        self.module.sensor_modes
        self.module.start_recording(
            JpegEncoder(q=50), FileOutput(self.output))

    def gen_stream(self):

        while True:
            with self.output.condition:
                self.output.condition.wait()
                frame = self.output.frame
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n'b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')


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

    async def read(self):
        '''Reads the sensor and returns the data in a tuple: (humidity, temperature).
        If the sensor is powered off it will be turned on, read, and turned off again.'''

        # init
        power_state = self.power.value  # get current power state
        humidity, temperature = None, None  # result

        self.power.on()  # power sensor on if it isn't already

        # loop until a result is returned
        while True:

            try:

                # give the sensor 3 seconds, otherwise a bug will occur where the sensor will output the data from when it was previously powered on.
                await asyncio.sleep(3)

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
        '''Same as the read function except it only reads the sensor once, even if the reading raises an exception.
        If the reading raises an exception, returns None.'''

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

        try:
            self.device = sensor or W1ThermSensor(Sensor.DS18B20)
        except:
            pass

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


class ADS1115:

    def __init__(self):

        # I2C addresses of the device
        self.I2C_Addresses = [0x48, 0x49]

        # ADS1115 Register Map
        self.Register_Map = {
            "CONVERT": 0x00,  # Conversion register
            "CONFIG": 0x01,  # Configuration register
            "LOWTHRESH": 0x02,  # Lo_thresh register
            "HITHRESH": 0x03,  # Hi_thresh register
        }

        # ADS1115 Configuration Register
        self.Config_Options = {
            "NOEFFECT": 0x00,  # No effect
            "SINGLE": 0x80,  # Single conversion
            "MUX_DIFF_0_1": 0x00,  # Differential P = AIN0, N = AIN1 (default)
            "MUX_DIFF_0_3": 0x10,  # Differential P = AIN0, N = AIN3
            "MUX_DIFF_1_3": 0x20,  # Differential P = AIN1, N = AIN3
            "MUX_DIFF_2_3": 0x30,  # Differential P = AIN2, N = AIN3
            "MUX_SINGLE_0": 0x40,  # Single-ended P = AIN0, N = GND
            "MUX_SINGLE_1": 0x50,  # Single-ended P = AIN1, N = GND
            "MUX_SINGLE_2": 0x60,  # Single-ended P = AIN2, N = GND
            "MUX_SINGLE_3": 0x70,  # Single-ended P = AIN3, N = GND
            "PGA_6_144V": 0x00,  # +/-6.144V range = Gain 2/3
            "PGA_4_096V": 0x02,  # +/-4.096V range = Gain 1
            "PGA_2_048V": 0x04,  # +/-2.048V range = Gain 2 (default)
            "PGA_1_024V": 0x06,  # +/-1.024V range = Gain 4
            "PGA_0_512V": 0x08,  # +/-0.512V range = Gain 8
            "PGA_0_256V": 0x0A,  # +/-0.256V range = Gain 16
            "MODE_CONTIN": 0x00,  # Continuous conversion mode
            "MODE_SINGLE": 0x01,  # Power-down single-shot mode (default)
            "DR_8SPS": 0x00,  # 8 samples per second
            "DR_16SPS": 0x20,  # 16 samples per second
            "DR_32SPS": 0x40,  # 32 samples per second
            "DR_64SPS": 0x60,  # 64 samples per second
            "DR_128SPS": 0x80,  # 128 samples per second (default)
            "DR_250SPS": 0xA0,  # 250 samples per second
            "DR_475SPS": 0xC0,  # 475 samples per second
            "DR_860SPS": 0xE0,  # 860 samples per second
            "CMODE_TRAD":
            0x00,  # Traditional comparator with hysteresis (default)
            "CMODE_WINDOW": 0x10,  # Window comparator
            "CPOL_ACTVLOW": 0x00,  # ALERT/RDY pin is low when active (default)
            "CPOL_ACTVHI": 0x08,  # ALERT/RDY pin is high when active
            "CLAT_NONLAT": 0x00,  # Non-latching comparator (default)
            "CLAT_LATCH": 0x04,  # Latching comparator
            "CQUE_1CONV": 0x00,  # Assert ALERT/RDY after one conversions
            "CQUE_2CONV": 0x01,  # Assert ALERT/RDY after two conversions
            "CQUE_4CONV": 0x02,  # Assert ALERT/RDY after four conversions
            "CQUE_NONE":
            # Disable the comparator and put ALERT/RDY in high state (default)
            0x03,
        }

        # Get I2C bus
        self.bus = smbus.SMBus(1)

        # Set operation params
        self.current_address = self.I2C_Addresses[0]
        self.coefficient = 0.125
        self.gain = 0x02
        self.channel = 0
        self.metadata = {
            "analogBuffer": [
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0
            ],
            "analogBufferTemp": [
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0
            ],
            "analogBufferIndex":
            0,
            "copyIndex":
            0,
            "averageVoltage":
            0,
            "tdsValue":
            0,
            "calibrationFactor":
            125,
        }

    def setGain(self, gain):

        self.gain = gain

        if gain == self.Config_Options["PGA_6_144V"]:
            self.coefficient = 0.1875
        elif gain == self.Config_Options["PGA_4_096V"]:
            self.coefficient = 0.125
        elif gain == self.Config_Options["PGA_2_048V"]:
            self.coefficient = 0.0625
        elif gain == self.Config_Options["PGA_1_024V"]:
            self.coefficient = 0.03125
        elif gain == self.Config_Options["PGA_0_512V"]:
            self.coefficient = 0.015625
        elif gain == self.Config_Options["PGA_0_256V"]:
            self.coefficient = 0.0078125
        else:
            self.coefficient = 0.125

    def setChannel(self, channel):
        self.channel = channel if channel > 3 else 0

    def setSingle(self):

        Option_Value = "MUX_SINGLE_" + str(self.channel)

        block = [
            self.Config_Options["SINGLE"]
            | self.Config_Options[Option_Value]
            | self.gain
            | self.Config_Options["MODE_CONTIN"],
            self.Config_Options["DR_128SPS"]
            | self.Config_Options["CQUE_NONE"],
        ]

        self.bus.write_i2c_block_data(self.current_address,
                                      self.Register_Map["CONFIG"], block)

    def setDifferential(self):

        if self.channel == 0:
            block = [
                self.Config_Options["SINGLE"]
                | self.Config_Options["MUX_DIFF_0_1"]
                | self.gain
                | self.Config_Options["MODE_CONTIN"],
                self.Config_Options["DR_128SPS"]
                | self.Config_Options["CQUE_NONE"],
            ]
        elif self.channel == 1:
            block = [
                self.Config_Options["SINGLE"]
                | self.Config_Options["MUX_DIFF_0_3"]
                | self.gain
                | self.Config_Options["MODE_CONTIN"],
                self.Config_Options["DR_128SPS"]
                | self.Config_Options["CQUE_NONE"],
            ]
        elif self.channel == 2:
            block = [
                self.Config_Options["SINGLE"]
                | self.Config_Options["MUX_DIFF_1_3"]
                | self.gain
                | self.Config_Options["MODE_CONTIN"],
                self.Config_Options["DR_128SPS"]
                | self.Config_Options["CQUE_NONE"],
            ]
        elif self.channel == 3:
            block = [
                self.Config_Options["SINGLE"]
                | self.Config_Options["MUX_DIFF_2_3"]
                | self.gain
                | self.Config_Options["MODE_CONTIN"],
                self.Config_Options["DR_128SPS"]
                | self.Config_Options["CQUE_NONE"],
            ]

        self.bus.write_i2c_block_data(self.current_address,
                                      self.Register_Map["CONFIG"], block)

    def readValue(self):
        """Read data back from Conversion Register, 2 bytes
        raw_adc MSB, raw_adc LSB"""

        data = self.bus.read_i2c_block_data(self.current_address,
                                            self.Register_Map["CONVERT"], 2)

        # Convert the data
        raw_adc = data[0] * 256 + data[1]

        if raw_adc > 32767:
            raw_adc -= 65535

        # Return converted data
        return int(float(raw_adc) * self.coefficient)

    def readVoltage(self, channel):
        self.setChannel(channel)
        self.setSingle()
        time.sleep(0.1)
        return self.readValue()

    def ComparatorVoltage(self, channel):
        self.setChannel(channel)
        self.setDifferential()
        time.sleep(0.1)
        return self.readValue()

    def getMedianTemp(self):
        temp = 0.0
        bufferLen = len(self.metadata["analogBuffer"])
        for j in range(bufferLen - 1):
            for i in range(bufferLen - j - 1):
                if (self.metadata["analogBufferTemp"][i] >
                        self.metadata["analogBufferTemp"][i + 1]):
                    temp = self.metadata["analogBufferTemp"][i]
                    self.metadata["analogBufferTemp"][i] = self.metadata[
                        "analogBufferTemp"][i + 1]
                    self.metadata["analogBufferTemp"][i + 1] = temp
        if bufferLen & 1 > 0:
            temp = self.metadata["analogBufferTemp"][(bufferLen - 1) / 2]
        else:
            temp = (
                self.metadata["analogBufferTemp"][int(bufferLen / 2)] +
                self.metadata["analogBufferTemp"][int(bufferLen / 2 - 1)]) / 2
        return float(temp)

    def interpVoltage(self):

        analogSampleTimepoint = time.time()
        printTimepoint = time.time()

        while True:

            if time.time() - analogSampleTimepoint > 0.04:
                # print(" test.......... ")
                analogSampleTimepoint = time.time()

                self.metadata["analogBuffer"][
                    self.metadata["analogBufferIndex"]] = self.readVoltage(1)

                self.metadata["analogBufferIndex"] += self.metadata[
                    "analogBufferIndex"]

                if self.metadata["analogBufferIndex"] == 30:
                    self.metadata["analogBufferIndex"] = 0

            if time.time() - printTimepoint > 0.8:
                # print(" test ")
                printTimepoint = time.time()

                for self.metadata["copyIndex"] in range(30):
                    self.metadata["analogBufferTemp"][
                        self.metadata["copyIndex"]] = self.readVoltage(1)

                self.metadata["averageVoltage"] = self.getMedianTemp() * (
                    5.0 / 1024.0)

                compensationCoefficient = 1.0 + 0.02 * self.metadata[
                    "calibrationFactor"]

                compensationVolatge = (self.metadata["averageVoltage"] /
                                       compensationCoefficient)

                self.metadata["tdsValue"] = (
                    133.42 * compensationVolatge**3 -
                    255.86 * compensationVolatge**2 +
                    857.39 * compensationVolatge) * 0.5
