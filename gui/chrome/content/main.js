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
	
	var model = c.data("model");
	model.runStep(0.04);
	model.draw(dc);
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
	var timerId = setInterval("updateRoadState()", 40);
	$(c).data("modelTimerId", timerId);
}

