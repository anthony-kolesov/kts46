defaults = {
	"Model": {},
	"Road": {
		"borderColor": "#666666",
		"color": "#eeeeee",
		"width": 10,
		"length": 1000
	},
	"Car": {
		"borderColor": "#666666",
		"color": "#0000dd",
		"length": 4.5,
		"width": 1.5,
		"position": 0.0,
		"speed": 15.0 // [m/s]
	},
	"SimpleTrafficLight": {
		"interval": 5, // [s]
		"position": 100, // [m] from start
		"state": "g"
	},
	"stopDistance": 2, // [m]
	"newCarGenRate": 3, // [s]
    "margin":5, // [px]
    "roadMargin": 3, // [px]
    "lightHeight": 1.0, // [m]
    "lightGreenColor": "#00ff00",
    "lightRedColor": "#ff0000"

};


// Represents road of the network.
function Road(options) {
	$.extend(this, defaults.Road);
	if(options) $.extend(this, options);
}


// Represents a car on the road.
function Car(options){
	$.extend(this, defaults.Car);
	if(options) $.extend(this, options);
}


// Model of road network.
function Model(options) {
	this.time = 0.0; // [s]
	this.cars = [];
	this.lights = [];
	this.newCarGenTime = 0.0; // [s]
	$.extend(this, defaults.Model);
	if (options) $.extend(this, options);
}


// Simple traffic light, that has two states: green and red.
function SimpleTrafficLight(options) {
	this.lastStateSwitchTime = 0.0; // [s]
	$.extend(this, defaults.SimpleTrafficLight);
	if (options) $.extend(this, options);
}

SimpleTrafficLight.prototype.switch = function(state) {
	this.state = state || ((this.state === "g") ? "r" : "g");
}


Model.prototype.draw = function(dc) {
	var margin = defaults.margin; // [px]
	var roadMargin = defaults.lightHeight; // [px] - margin between car and road.
	var lightHeight = defaults.lightHeight; // [m]
	var lightGreenColor = defaults.lightGreenColor;
	var lightRedColor = defaults.lightRedColor;
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


Model.prototype.run_step = function(timeStep) {
	var newTime = this.time + timeStep;

	for (var i in this.lights) {
		var tl = this.lights[i];
		if (newTime - tl.lastStateSwitchTime > tl.interval) {
			tl.switch();
			tl.lastStateSwitchTime = newTime;
		}
	}

	for (var i in this.cars) {
		if (!this.cars[i]) continue;

		var car = this.cars[i];
		var distanceToMove = car.speed * timeStep;

		// Check for red traffic light.
		var nearestTL = this.getNearestTLight(car.position);
		if(nearestTL && nearestTL.state === "r" &&
		   (nearestTL.position - car.position - defaults.stopDistance) < distanceToMove ) {
			distanceToMove = (nearestTL.position - car.position) - defaults.stopDistance; // Default distance to light or car. temporary.
			if (distanceToMove < 0) distanceToMove = 0;
		}

		// Check for leading car.
		var nearestCar = this.getNearestCar(car.position);
		if(nearestCar &&
		   (nearestCar.position - nearestCar.length - car.position - defaults.stopDistance) < distanceToMove ) {
			distanceToMove = (nearestCar.position - nearestCar.length - car.position) - defaults.stopDistance; // Default distance to light or car. temporary.
			if (distanceToMove < 0) distanceToMove = 0;
		}

		car.position += distanceToMove;
		if (this.road.length < car.position) {
			this.cars[i] = undefined;
		}
	}

	// Generate new car
	if (this.newCarGenTime + defaults.newCarGenRate <= newTime) {
		var speed = Math.floor(Math.random() * 10) + 10;
		var car = new Car({"speed": speed});
		document.getElementById("log-box").value += "Generated car with speed: " + speed + "\n";
		this.cars.push(car);
		this.newCarGenTime = newTime;
	}

	this.time = newTime;
};


// Gets the nearest traffic light to specified position.
Model.prototype.getNearestTLight = function(position){
	return this.getNearestObjectInArray(this.lights, position);
};


Model.prototype.getNearestCar = function(position){
	return this.getNearestObjectInArray(this.cars, position);
};


Model.prototype.getNearestObjectInArray = function(list, position){
	var cur = undefined;
	for (var i in list){
		if (!list[i]) continue;
		var t = list[i];
		var tpos = t.position;
		if (t.length) { tpos -= t.length; }
		// Still not passed and there is no current or is closer than current.
		if (tpos > position && (!cur || cur.position > tpos) ) {
			cur = t;
		}
	}
	return cur;
};
