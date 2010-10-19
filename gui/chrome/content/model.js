// Represents road of the network.
function Road(options) {
    var p = getPreferences();
    this.color = p.getCharPref("road-color");
    this.borderColor = p.getCharPref("road-border-color");
    this.width = parseFloat(p.getCharPref("road-width")); // [m]
    this.length = parseFloat(p.getCharPref("road-length")); // [m]

	if(options) $.extend(this, options);
}


// Represents a car on the road.
function Car(options){
    var p = getPreferences();
    this.color = p.getCharPref("car-color");
    this.borderColor = p.getCharPref("car-border-color");
    this.width = parseFloat(p.getCharPref("car-width")); // [m]
    this.length = parseFloat(p.getCharPref("car-length")); // [m]
    this.position = parseFloat(p.getCharPref("car-position")); // [m]
    this.speed = parseFloat(p.getCharPref("car-speed")); // [m/s]

	if(options) $.extend(this, options);
}


// Model of road network.
function Model(options) {
	this.time = 0.0; // [s]
	this.cars = [];
	this.lights = [];
	this.newCarGenTime = 0.0; // [s]

    var p = getPreferences();
    this.lightGreenColor = p.getCharPref("tl-green-color");
    this.lightRedColor = p.getCharPref("tl-red-color");
    this.lightHeight = parseFloat(p.getCharPref("tl-height"));
    this.viewMargin = p.getIntPref("view-margin");
    this.stopDistance = parseFloat(p.getCharPref("model-stop-distance"));
    this.carGenRate = parseFloat(p.getCharPref("model-car-gen-rate"));

	if (options) $.extend(this, options);
}


// Simple traffic light, that has two states: green and red.
function SimpleTrafficLight(options) {
    var p = getPreferences();
    this.position = parseFloat(p.getCharPref("tl-position")); // [m]

	this.lastStateSwitchTime = 0.0; // [s]
    this.state = "g";

	if (options) $.extend(this, options);
}

SimpleTrafficLight.prototype.switch = function(state) {
	this.state = state || ((this.state === "g") ? "r" : "g");
}


Model.prototype.draw = function(dc) {
	var margin = this.viewMargin; // [px]
	var roadMargin = this.lightHeight; // [px] - margin between car and road.
	var lightHeight = this.lightHeight;
	var lightGreenColor = this.lightGreenColor;
	var lightRedColor = this.lightRedColor;
	var scale = (dc.canvas.height - margin * 2) / this.road.length;

	var r = this.road;

	// Clear canvas.
	dc.clearRect(0, 0, dc.canvas.width, dc.canvas.height);

	// Draw road.
	dc.strokeStyle = r.borderColor;
	dc.fillStyle = r.color;
	dc.fillRect(margin, margin, r.width * scale, r.length * scale);
	dc.strokeRect(margin, margin, r.width * scale, r.length * scale);

	// Draw cars.
	for (var i in this.cars) {
		if (!this.cars[i]) continue;

		var c = this.cars[i];
		dc.strokeStyle = c.borderColor;
		dc.fillStyle = c.color;

		var x = margin + roadMargin;
		var y = margin + (c.position - c.length) * scale;

		var width = c.drawWidth || (c.drawWidth = c.width * scale);
		var height = c.drawHeight || (c.drawHeight = c.length * scale);
		if (y < margin) { // Car is at top and its end out of road.
			height = y - margin + c.length*scale;
			y = margin;
		} else if (y > dc.canvas.height - margin) { // Car is at bottom.
			var newY = dc.canvas.height.margin;
			height = height - (y - newY);
			y = newY;
		}

		dc.fillRect(x, y, width, height);
		dc.strokeRect(x, y, width, height);
	}

	// Draw traffic lights.
	for (var i in this.lights) {
		var tl = this.lights[i];

		var x = margin;
		var y = margin + tl.position * scale + lightHeight;
		var width = r.width * scale;
		var height = lightHeight * scale;

		dc.fillStyle = tl.state === "g" ? lightGreenColor : lightRedColor;
		dc.fillRect(x, y, width, height);
	}

	return this;
};
