var dom = {
	"roadCanvas": "#road-canvas",
	"cmdPause": "#cmd_model_pause",
	"cmdRun": "#cmd_model_run"
};


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


function drawModel(aModel, aDc) {
	var c = (aDc && aModel) || $(dom.roadCanvas);
	var dc = aDc || c.get(0).getContext("2d");
	var model = aModel || c.data("model");
	model.draw(dc);
}


// Move cars and redraws canvas.
function updateRoadState() {
	var model = $(dom.roadCanvas).data("model");
	model.runStep(0.04);
	drawModel(model)
}


/**
 * Draws initial view of canvas.
 */
function drawInitialCanvas() {
	// Pause current model, so new model will not be runned by old interval timer.
	pauseModel();
	
	var c = $(dom.roadCanvas);
	var dc = c.get(0).getContext("2d");
	
	var r = new Road({"length": 300});
	var car = new Car();
	var model = new Model({"road": r, "cars":[car], "lights": [new SimpleTrafficLight()]});
	
	c.data("model", model);
	
	drawModel(model);
}


function pauseModel(){
	// Pause model.
	var c = $(dom.roadCanvas);
	var timerId = c.data("modelTimerId");
	clearInterval(timerId);
	c.removeData("modelTimerId");
	
	// UI modification.
	$(dom.cmdPause).attr('disabled', true);
	$(dom.cmdRun).removeAttr('disabled');
}


function runModel(){
	if ($(dom.roadCanvas).data("modelTimerId")) {
		// Do nothing, because model is already running.
		// Or model will start to run faster.
		return;
	}
	updateRoadState();
	var timerId = setInterval("updateRoadState();", 40);
	$(dom.roadCanvas).data("modelTimerId", timerId);
	
	// UI modification.
	$(dom.cmdPause).removeAttr('disabled');
	$(dom.cmdRun).attr('disabled', true);
}

