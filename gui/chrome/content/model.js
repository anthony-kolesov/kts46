defaults = {
	"Model": {
		"cars": [],
		"lights": []
		// "time": 0.0 // [s]
	},
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
	}
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
	this.time = 0.0;
	$.extend(this, defaults.Model);
	if (options) $.extend(this, options);
}


// Simple traffic light, that has two states: green and red.
function SimpleTrafficLight(options) {
	this.lastStateSwitchTime = 0.0; // [s]
	$.extend(this, defaults.SimpleTrafficLight);
	if (options) $.extend(this, options);
}

SimpleTrafficLight.prototype.switch = function () {
	this.state = (this.state === "g") ? "r" : "g";
}


Model.prototype.draw = function(dc) {
	var margin = 5; // [px]
	var roadMargin = 3; // [px] - margin between car and road.
	var lightHeight = 1.0; // [m]
	var lightGreenColor = "#00ff00";
	var lightRedColor = "#ff0000";
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


Model.prototype.runStep = function(timeStep) {
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
		car.position += distanceToMove;
		
		if (this.road.length < car.position) {
			this.cars[i] = undefined;
		}
	}
	
	this.time = newTime;
};
