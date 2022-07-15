from flask import Flask, make_response, request, render_template
from gpiozero import OutputDevice, InputDevice
import asyncio

# local
from devices import DHT22, DS18B20
from persistence import task_handler


# local GPIO devices
dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
llpk1 = InputDevice(25)
relays = {
    "pump_relay": OutputDevice(24),
}

# start task handler
th = task_handler(".tasks")

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
    args = {
        "id": request.args.get("id"),
        "timeOn": request.args.get("timeOn", "60", type=str),
        "timeOff": request.args.get("timeOff", "300", type=str)
    }

    # if no "id" query parameter then return list of all running loops
    if args.id == None:

        arr = []

        for task in th.tasks_set:
            arr.append(task.get_name())

        return {
            "running_tasks": arr
        }

    # set relay
    try:
        args["relay"] = relays[args.id]
    except KeyError:
        return make_response('''Invalid query param "id"''', 400)

    # operation param
    execution = request.args.get("execution", "", type=str)

    # ?execution=start
    if execution == "start":
        th.start(args.id, **args)

    # ?execution=stop
    elif execution == "stop":
        th.stop(args.id)

    # loop state
    loop_state = "Stopped"
    for task in th.tasks_set:
        if task.get_name() == args.id:
            loop_state = "Running"

    return {
        'power_state': args.relay.value,
        'loop_state': loop_state
    }
