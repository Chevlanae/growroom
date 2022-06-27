from flask import Flask, request, render_template
from gpiozero import OutputDevice, InputDevice

# local
from devices import DHT22, DS18B20

dht22 = DHT22(27, 23)
ds18b20 = DS18B20()
relay = OutputDevice(24)
llpk1 = InputDevice(25)

app = Flask(__name__)


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

        if power == "on":
            relay.on()
        elif power == "off":
            relay.off()
    except:
        pass

    return {
        'power_state': relay.value
    }


@app.route("/LLPK1")
def read_LLPK1():

    return {
        "state": llpk1.value
    }
