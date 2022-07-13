from flask import Flask, make_response, request, render_template
from gpiozero import OutputDevice, InputDevice
import asyncio

# local
from devices import DHT22, DS18B20, power_loop


# local GPIO devices
dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
llpk1 = InputDevice(25)
relays = {
    "pump_relay": OutputDevice(24),
}

# loop init
event_loop = asyncio.new_event_loop()
tasks = set()  # task aggregator

# flask
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html', relays=relays.keys())


@app.route("/DHT22")
async def read_DHT22():

    try:
        humidity, temperature = await asyncio.wait_for(dht22.read(), timeout=15.0)
    except asyncio.TimeoutError:
        humidity, temperature = None, None

    return {
        "humidity": humidity,
        "temperature": temperature
    }


@app.route("/DS18B20")
def read_DS18B20():

    return {
        "temperature": round(ds18b20.read(), 1)
    }


@app.route("/LLPK1")
def read_LLPK1():

    return {
        "state": llpk1.value
    }


@app.route("/relay")
def relay_api():

    # query params
    id = request.args.get("id")
    power = request.args.get("power", "", type=str)

    if id == None:
        connected_relays = []

        for relay in relays.keys():
            connected_relays.append(relay)
        return {
            "connected_relays": connected_relays
        }

    relay = relays[id]

    power == "on" and relay.on()
    power == "off" and relay.off()

    return {
        "power_state": relay.value,
    }


@app.route("/loop")
def set_loop():

    # query params
    id = request.args.get("id")
    execution = request.args.get("execution", "", type=str)
    timeOn = request.args.get("timeOn", "60", type=str)
    timeOff = request.args.get("timeOff", "180", type=str)

    # if no "id" query parameter then return list of all running loops
    if id == None:

        running_loops = []

        for item in tasks:
            running_loops.append(item.get_name())

        return {
            "running_loops": running_loops
        }

    # set relay
    try:
        relay = relays[id]
    except:
        params = {
            "id": id,
            "execution": execution,
            "timeOn": timeOn,
            "timeOff": timeOff
        }

        return make_response({"error": "Invalid relay ID", "params": params}, 400)

    # set task
    task = None
    for item in tasks:
        if item.get_name() == id:
            task = item
            break

    # ?execution=start
    if execution == "start":

        if task == None:

            # create power_loop task and add it to tasks set
            task = event_loop.create_task(
                power_loop(relay, int(timeOn), int(timeOff), id))

            task.set_name(id)

            tasks.add(task)

        # run event loop if it hasn't been triggered already
        if not event_loop.is_running():
            event_loop.run_forever()

        app.logger.log(0, "Power cycle %s started...", id, exc_info=1)

    # ?execution=stop
    elif execution == "stop":

        # cancel task and discard it from tasks set
        task.cancel()
        tasks.discard(task)

        # stop event loop if tasks are complete
        if len(tasks) == 0:
            event_loop.call_soon_threadsafe(event_loop.stop)

        app.logger.log(0, "Power cycle %s stopped...", id, exc_info=1)

    # loop state
    loop_state = "Stopped"
    if task != None:
        loop_state = "Running"

    return {
        'power_state': relay.value,
        'loop_state': loop_state
    }
