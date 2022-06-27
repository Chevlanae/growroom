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

var airTemp = document.getElementById("air-temp"),
	airHumidity = document.getElementById("air-humidity"),
	waterTemp = document.getElementById("water-temp"),
	waterLevel = document.getElementById("water-level");

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
}

document.getElementById("update").addEventListener("click", updateMeters);
