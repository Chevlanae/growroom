from flask import Flask, request, render_template
from gpiozero import OutputDevice, InputDevice
import asyncio

# local
from devices import DHT22, DS18B20, power_loop

# local GPIO devices
dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
pumprelay = OutputDevice(24)
llpk1 = InputDevice(25)

# flask
app = Flask(__name__)

# async init
event_loop = asyncio.new_event_loop()
tasks = set()  # task aggregator


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


@app.route("/loop")
def set_loop():

    # set power parameter
    try:
        execution = request.args.get('execution')
    except:
        execution = ""

    # query is ?execution=start and there are no tasks
    if execution == "start" and len(tasks) == 0:

        # create power_loop task and add it to tasks set
        tasks.add(event_loop.create_task(power_loop(pumprelay, 60, 180, "0")))

        # run loop if it hasn't been triggered already
        if not event_loop.is_running():
            event_loop.run_forever()

    # query is ?loop=stop
    elif execution == "stop":

        # cancel all tasks
        for task in tasks:
            task.cancel()

        # clear set
        tasks.clear()

        # stop event loop
        if event_loop.is_running():
            event_loop.call_soon_threadsafe(event_loop.stop)

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
