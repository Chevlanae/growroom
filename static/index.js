//! helper functions

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

		let queryString = "?" + queryParams.join("&");

		response = await fetch("/loop" + queryString);

		return await response.json();
	} else {
		console.error(id + " is an invalid loop ID");
	}
}

//! globals

var airTemp = document.getElementById("air-temp"),
	airHumidity = document.getElementById("air-humidity"),
	waterTemp = document.getElementById("water-temp"),
	waterLevel = document.getElementById("water-level"),
	relayTable = document.getElementById("relay-table"),
	refresh = document.getElementById("refresh"),
	refreshToggle = document.getElementById("refresh-toggle"),
	refreshInterval = document.getElementById("refresh-interval"),
	globalInterval;

//! event handlers
function refreshRelay(id) {
	let row = document.getElementById(id);

	loop(row.id).then((response) => {
		row.querySelector(".loop-state").innerText = response.loop_state;
		row.querySelector(".timeOn").value = response.loop_info.kwargs.timeOn;
		row.querySelector(".timeOff").value = response.loop_info.kwargs.timeOff;
	});

	return true;
}

function refreshAll() {
	DHT22().then((response) => {
		airTemp.innerText = response.temperature + "° C";
		airHumidity.innerText = response.humidity + "%";
	});

	DS18B20().then((response) => {
		waterTemp.innerText = response.temperature + "° C";
	});

	LLPK1().then((response) => {
		waterLevel.innerText = !response.state;
	});

	for (let row of relayTable.getElementsByTagName("tr")) {
		row.id && refreshRelay(row.id) && console.log("Refreshed " + row.id);
	}
}

function autoRefresh() {
	if (refreshToggle.checked) {
		let desiredInterval = Number(refreshInterval.value);

		refreshAll();
		globalInterval = setInterval(refreshAll, desiredInterval * 1000);
	} else {
		clearInterval(globalInterval);
	}
}

//! set event listeners

//uncheck the auto refresh checkbox if it's checked when the page is loaded
if (refreshToggle.checked) {
	refreshToggle.click();
}

//refresh events
refresh.addEventListener("click", refreshAll);
refreshToggle.addEventListener("input", autoRefresh);

//relay table events
for (let row of relayTable.getElementsByTagName("tr")) {
	let toggle = row.querySelector(".toggle");

	toggle &&
		row.hasAttribute("id") &&
		toggle.addEventListener("click", function () {
			loop(row.id).then((response) =>
				loop(row.id, Number(row.querySelector(".timeOn").value) || null, Number(row.querySelector(".timeOff").value) || null, response.loop_state).then(() => refreshRelay(row.id))
			);
		});
}
