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

async function relay(power = null) {
	if (power === true) {
		let response = await fetch("/relay?power=on");

		return await response.json();
	} else if (power === false) {
		let response = await fetch("/relay?power=off");

		return await response.json();
	} else {
		let response = await fetch("/relay");

		return await response.json();
	}
}

var airTemp = document.getElementById("air-temp"),
	airHumidity = document.getElementById("air-humidity"),
	waterTemp = document.getElementById("water-temp"),
	waterLevel = document.getElementById("water-level"),
	waterLoopStatus = document.getElementById("loop-status"),
	refreshToggle = document.getElementById("refresh-toggle"),
	refreshInterval;

function updateMeters() {
	DHT22().then((response) => {
		airTemp.innerText = response.temperature;
		airHumidity.innerText = response.humidity;
	});

	DS18B20().then((response) => {
		waterTemp.innerText = response.temperature;
	});

	LLPK1().then((response) => {
		waterLevel.innerText = !response.state;
	});

	relay().then((response) => {
		waterLoopStatus.innerText = response.loop_running;
	});
}

function toggleLoop() {
	relay().then((response) => {
		if (response.loop_running) {
			relay(false).then((response) => (waterLoopStatus.innerText = response.loop_running));
		} else {
			relay(true).then((response) => (waterLoopStatus.innerText = response.loop_running));
		}
	});
}

function autoRefresh() {
	if (refreshToggle.checked) {
		updateMeters();
		refreshInterval = setInterval(updateMeters, 30000);
	} else {
		clearInterval(refreshInterval);
	}
}

document.getElementById("update").addEventListener("click", updateMeters);
document.getElementById("toggle-loop").addEventListener("click", toggleLoop);
refreshToggle.addEventListener("input", autoRefresh);
