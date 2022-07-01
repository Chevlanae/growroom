async function DHT22() {
	let request = await fetch("/DHT22");

	return await request.json();
}

async function DS18B20() {
	let request = await fetch("/DS18B20");

	return await request.json();
}

async function LLPK1() {
	let request = await fetch("/LLPK1");

	return await request.json();
}

/**
 * Gets data about a given loop. Toggle the execution of the loop with the "loop_state" parameter.
 * @param {boolean | null} loop_state Toggles loop execution depending on the given "loop_state". For example, if loop_state == true, then GET /loop?execution=stop
 * @returns {Promise<any>}
 */
async function loop(loop_state = null) {
	if (loop_state === true) {
		let response = await fetch("/loop?execution=stop");

		return await response.json();
	} else if (loop_state === false) {
		let response = await fetch("/loop?execution=start");

		return await response.json();
	} else {
		let response = await fetch("/loop");

		return await response.json();
	}
}

var airTemp = document.getElementById("air-temp"),
	airHumidity = document.getElementById("air-humidity"),
	waterTemp = document.getElementById("water-temp"),
	waterLevel = document.getElementById("water-level"),
	waterLoopStatus = document.getElementById("loop-status"),
	relayPowerState = document.getElementById("relay-status"),
	refreshToggle = document.getElementById("refresh-toggle"),
	refreshInterval;

function refreshMeters() {
	DHT22().then((response) => {
		airTemp.innerText = response.temperature + "° C";
		airHumidity.innerText = response.humidity + "% RH";
	});

	DS18B20().then((response) => {
		waterTemp.innerText = response.temperature + "° C";
	});

	LLPK1().then((response) => {
		waterLevel.innerText = !response.state;
	});

	loop().then((response) => {
		waterLoopStatus.innerText = response.loop_running;
		relayPowerState.innerText = Boolean(response.power_state) ? "on" : "off";
	});
}

function toggleLoop() {
	loop().then((response) => {
		loop(response.loop_running).then((response) => (waterLoopStatus.innerText = response.loop_running));

		refreshMeters();
	});
}

function autoRefresh() {
	if (refreshToggle.checked) {
		refreshMeters();
		refreshInterval = setInterval(refreshMeters, 30 * 1000);
	} else {
		clearInterval(refreshInterval);
	}
}

document.getElementById("refresh").addEventListener("click", refreshMeters);
document.getElementById("toggle-loop").addEventListener("click", toggleLoop);
refreshToggle.addEventListener("input", autoRefresh);

if (refreshToggle.checked) {
	refreshToggle.click();
}
