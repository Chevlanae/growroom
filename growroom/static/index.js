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
async function loop(id, timeOn = null, timeOff = null, loop_state = null) {
	if (typeof id === "string") {
		let response,
			queryParams = [];

		queryParams.push("id=" + id);

		if (loop_state === "Running") {
			queryParams.push("execution=stop");
		}

		if (loop_state === "Stopped") {
			queryParams.push("execution=start");

			if (typeof timeOn === "number") {
				queryParams.push("timeOn=" + timeOn.toString());
			}

			if (typeof timeOff === "number") {
				queryParams.push("timeOff=" + timeOff.toString());
			}
		}

		let queryString = queryParams.join("&");

		response = await fetch("/loop?" + queryString);

		return await response.json();
	} else {
		console.error(id + " is an invalid loop ID");
	}
}

var airTemp = document.getElementById("air-temp"),
	airHumidity = document.getElementById("air-humidity"),
	waterTemp = document.getElementById("water-temp"),
	waterLevel = document.getElementById("water-level"),
	refreshToggle = document.getElementById("refresh-toggle"),
	refreshInterval;

function refreshRelay(id) {
	row = document.getElementById("relay-table").querySelector("#" + id);

	try {
		loop(row.id).then((response) => {
			row.querySelector(".power-state").innerText = Boolean(response.power_state) ? "on" : "off";
			row.querySelector(".loop-state").innerText = response.loop_state;
		});
	} catch (e) {
		console.error(e);
	}
}

function refreshAll() {
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

	for (let row of document.querySelector("#relay-table").getElementsByTagName("tr")) {
		if (row.hasAttribute("id")) {
			refreshRelay(row.id);
		}
	}
}

function autoRefresh() {
	if (refreshToggle.checked) {
		refreshAll();
		refreshInterval = setInterval(refreshAll, 20 * 1000);
	} else {
		clearInterval(refreshInterval);
	}
}

document.getElementById("refresh").addEventListener("click", refreshAll);
refreshToggle.addEventListener("input", autoRefresh);

if (refreshToggle.checked) {
	refreshToggle.click();
}

for (let row of document.getElementById("relay-table").getElementsByTagName("tr")) {
	toggle = row.querySelector(".toggle");

	toggle &&
		toggle.addEventListener("click", function () {
			if (row.hasAttribute("id")) {
				loop(row.id).then((response) =>
					loop(row.id, Number(row.querySelector(".timeOn").value) || null, Number(row.querySelector(".timeOff").value) || null, response.loop_state)
				);

				setTimeout(refreshRelay, 1000, row.id);
			}
		});
}
