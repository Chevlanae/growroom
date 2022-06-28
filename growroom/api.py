from flask import Flask, request, render_template
from gpiozero import OutputDevice, InputDevice
import asyncio

# local
from devices import DHT22, DS18B20

# local GPIO devices
dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
pumprelay = OutputDevice(24)
llpk1 = InputDevice(25)

# flask
app = Flask(__name__)

# async init
loop = asyncio.new_event_loop()
tasks = set()


async def water_loop(timeOn: int, timeOff: int):
    print("Water cycle started...")
    while True:
        print("Relay On...")
        pumprelay.on()
        await asyncio.sleep(timeOn)
        print("Relay Off...")
        pumprelay.off()
        await asyncio.sleep(timeOff)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/DHT22")
def read_DHT22():

    humidity, temperature = dht22.read()

    return {
        "humidity": humidity,
        "temperature": temperature
    }


@app.route("/DS18B20")
def read_DS18B20():

    return {
        "temperature": ds18b20.read()
    }


@app.route("/relay")
def set_relay():

    try:
        power = request.args.get('power')
    except:
        power = ""

    if power == "on" and len(tasks) == 0:

        tasks.add(loop.create_task(water_loop(60, 180)))

        if loop.is_running() == False:
            loop.run_forever()

    elif power == "off":

        for task in tasks:
            task.cancel()

        tasks.clear()

        loop.call_soon_threadsafe(loop.stop)
        print("Water cycle stopped...")

        pumprelay.off()
        print("Relay Off...")

    return {
        'power_state': pumprelay.value,
        'loop_running': len(tasks) > 0
    }


@app.route("/LLPK1")
def read_LLPK1():

    return {
        "state": llpk1.value
    }
