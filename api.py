from flask import Flask, make_response, request, render_template, Response
from gpiozero import InputDevice
import asyncio

# local
from devices import DHT22, DS18B20, ADS1115, Camera
from persistence import task_handler

# local camera
pi_camera = Camera()

# local GPIO devices
dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
llpk1 = InputDevice(25)
ads1115 = ADS1115()
relays = {
    "pump_relay": 24,
}

# start task handler
th = task_handler(".tasks")

# flask
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html', relays=relays.keys())


@app.route('/camera_feed')
def camera_feed():
    return Response(pi_camera.gen_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/DHT22")
async def read_DHT22():

    try:
        humidity, temperature = await asyncio.wait_for(dht22.read(), timeout=15.0)
    except asyncio.TimeoutError:
        humidity, temperature = None, None

    return {"humidity": humidity, "temperature": temperature}


@app.route("/DS18B20")
def read_DS18B20():

    return {"temperature": round(ds18b20.read(), 1)}


@app.route("/LLPK1")
def read_LLPK1():

    return {"state": llpk1.value}


@app.route("/loop")
def set_loop():

    # query params
    args = {
        "id": request.args.get("id"),
        "timeOn": request.args.get("timeOn", "60", type=int),
        "timeOff": request.args.get("timeOff", "300", type=int)
    }

    # if no "id" query parameter then return list of all running loops
    if args["id"] == None:

        arr = []

        for task in th.tasks_set:
            arr.append(task.get_name())

        return {"running_tasks": arr}

    # set relay in args dict
    try:
        args["relay_pin"] = relays[args["id"]]
    except KeyError:
        return make_response('''Invalid query param "id"''', 400)

    # main operation
    execution = request.args.get("execution", "", type=str)

    # ?execution=start
    if execution == "start":
        th.start('power_loop', args["id"], **args)

    # ?execution=stop
    elif execution == "stop":
        th.stop(args["id"])

    task = th.fetch_task(args["id"])

    # get loop task state
    if task != None:
        loop_state = "Running"
    else:
        loop_state = "Stopped"

    return {
        'loop_state': loop_state,
        'loop_info': th.fetch_task_info(args["id"])
    }


@app.route("/ADS1115")
def read_TDS():

    if th.fetch_task("ADS1115") == None:
        th.start("run_tds", "ADS1115")

    return {
        "averageVoltage": ads1115.metadata["averageVoltage"],
        "tdsValue": ads1115.metadata["tdsValue"]
    }
