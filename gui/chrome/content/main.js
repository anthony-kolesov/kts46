function runQuery() {
	//const SimpleConstructor = new Components.Constructor("@mozilla.org/js_simple_component;1", "nsISimple");
	var SimpleConstructor = new Components.Constructor("@mozilla.org/PySimple;1", "nsISimple");
	var s = new SimpleConstructor();
	document.getElementById("query-text").value = s.yourName;
}


/**
 * Shows window with information about application.
 */
function showAboutInfo() {
	alert('(C)2010 Anthony Kolesov\nanthony.kolesov -at- gmail.com');   
}


/**
 * Closes application.
 */
function closeApp(){
	window.close();
}


// Move cars and redraws canvas.
function updateRoadState() {
	var c = $("#road-canvas");
	var dc = c.get(0).getContext("2d");
	
	// var road = c.data("road").draw(dc);
	// var car = c.data("car").draw(dc);
	var model = c.data("model");
	model.runStep(1.0);
	for (var i in model.cars){
		if (!model.cars[i]) continue;
		
		var car = model.cars[i];
		car.position += 1.0;
		
		if (car.position+car.length >= model.road.length){
			model.cars[i] = undefined;
		}
	}
	model.draw(dc);
	
	/*if (car.y + car.height < road.height + road.y) {
		car.y += 1;
	} else {
		clearInterval(c.data("modelTimerId"));
		c.removeData("modelTimerId");
	}
	*/
}


/**
 * Draws initial view of canvas.
 */
function drawInitialCanvas() {
	var c = document.getElementById("road-canvas");
	var dc = c.getContext("2d");
	
	var r = new Road({"length": 300 });
	var car = new Car({"position": 40});
	var model = new Model({"road": r, "cars":[car], "lights": [new SimpleTrafficLight()] });
	
	$(c).data("model", model);
	
	updateRoadState();
	var timerId = setInterval("updateRoadState()", 10);
	$(c).data("modelTimerId", timerId);
}

