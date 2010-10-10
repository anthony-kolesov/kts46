var dom = {
    "roadCanvas": "#road-canvas",
    "cmdPause": "#cmd_model_pause",
    "cmdRun": "#cmd_model_run",
    "modelType": "#model-type"
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


function drawPythonModel(drawModel, modelState, dc){
    var margin = defaults.margin; // [px]
    var roadMargin = defaults.lightHeight; // [px] - margin between car and road.
    var lightHeight = defaults.lightHeight; // [m]
    var lightGreenColor = defaults.lightGreenColor;
    var lightRedColor = defaults.lightRedColor;
    var scale = (dc.canvas.height - margin * 2) / this.road.length;

    var r = {};
    $.extend(r, defaults.Road);
    $.extend(r, modelDescription.road);

    // Clear canvas.
    dc.clearRect(0, 0, dc.canvas.width, dc.canvas.height);

    // Draw road.
    dc.strokeStyle = r.borderColor;
    dc.fillStyle = r.color;
    dc.fillRect(margin, margin, r.width * scale, r.length * scale);
    dc.strokeRect(margin, margin, r.width * scale, r.length * scale);

    // Draw cars.
    for (var i in modelState.cars) {
        // if (!this.cars[i]) continue;

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
    for (var i in modelState.lights) {
        var tl = modelDescription.lights[i];

        var x = margin;
        var y = margin + tl.position * scale + lightHeight;
        var width = r.width * scale;
        var height = lightHeight * scale;

        dc.fillStyle = tl.state === "g" ? lightGreenColor : lightRedColor;
        dc.fillRect(x, y, width, height);
    }
}

function drawModel() {
    var c = $(dom.roadCanvas);
    var dc = c.get(0).getContext("2d");
    var model = c.data("model");
    var modelType = c.data("model-type");
    if (modelType === "py") {
        var dm = c.data("draw-model");
        var stateStr = model.get_state_data();
        if (c.data("current-state") !== stateStr ){
            logmsg("CURRENT STATE: "+stateStr);
            c.data("current-state", stateStr);
        }
        var state = $.parseJSON(stateStr);
        for (var i in state.lights) {
            dm.lights[i].switch(state.lights[i].state);
        }
        for (var carId in state.cars) {
            var car = state.cars[carId];

            if (car.action && car.action === "del") {
                // Delete old car.
                dm.cars[carId] = undefined;
            } else if (car.action && car.action === "add") {
                // Add new car
                dm.cars[carId] = new Car(car);
            } else {
                // Update existing car.
                dm.cars[carId].position = car.position;
            }
        }
    }
    dm.draw(dc);
}


// Move cars and redraws canvas.
function updateRoadState() {
    var c = $(dom.roadCanvas);
    if (c.data("model-type") === "js")
        c.data("model").run_step(0.04);
    else
        c.data("model").run_step(40);
    drawModel();

    // Setup new timer.
    var timerId = setTimeout("updateRoadState();", 40);
    $(dom.roadCanvas).data("modelTimerId", timerId);
}


/**
 * Draws initial view of canvas.
 */
function drawInitialCanvas() {
    // Pause current model, so new model will not be runned by old interval timer.
    pauseModel();

    var c = $(dom.roadCanvas);
    var dc = c.get(0).getContext("2d");

    if ( $(dom.modelType).attr('value') === "js" ) {
        var r = new Road({"length": 300});
        var car = new Car();
        var model = new Model({"road": r, "cars":[car], "lights": [new SimpleTrafficLight()]});

        c.data("model", model);
        c.data("model-type","js");
        drawModel();
    } else {
        const PyModel = new Components.Constructor(
            "@kolesov.blogspot.com/RoadNetworkModel;1",
            "nsIRoadNetworkModel");
        var model = new PyModel();
        c.data("model", model);
        c.data("model-type","py");
        var descrStr = model.get_description_data();
        var descr = $.parseJSON(descrStr);
        c.data("model-description", descr);
        logmsg("NETWORK: " + descrStr);
        logmsg("STATE: " + model.get_state_data());

        var road = new Road(descr.road);
        var lights = {};
        for (var i in descr.lights)
            lights[descr.lights[i].id] = new SimpleTrafficLight(descr.lights[i]);
        logmsg("Creating draw model");
        var drawingModel = new Model({
            "road":road,
            "lights":lights,
            "cars": {}
        });
        logmsg("Saving draw model to data.");
        c.data("draw-model", drawingModel);
        drawModel();
    }
}

function openJavaScriptConsole() {
    var wwatch = Components.classes["@mozilla.org/embedcomp/window-watcher;1"]
                         .getService(Components.interfaces.nsIWindowWatcher);
    wwatch.openWindow(null, "chrome://global/content/console.xul", "_blank",
                    "chrome,dialog=no,all", null);
}

function logmsg(str) {
    Components.classes['@mozilla.org/consoleservice;1']
        .getService(Components.interfaces.nsIConsoleService)
        .logStringMessage(str);
}

function pauseModel(){
    // Pause model.
    var c = $(dom.roadCanvas);
    var timerId = c.data("modelTimerId");
    clearTimeout(timerId);
    c.removeData("modelTimerId");

    // UI modification.
    $(dom.cmdPause).attr('disabled', true);
    $(dom.cmdRun).removeAttr('disabled');
    $(dom.modelType).removeAttr('disabled');
}


function runModel(){
    if ($(dom.roadCanvas).data("modelTimerId")) {
        // Do nothing, because model is already running.
        // Or model will start to run faster.
        return;
    }
    updateRoadState();
    // var timerId = setTimeout("updateRoadState();", 40);
    // $(dom.roadCanvas).data("modelTimerId", timerId);

    // UI modification.
    $(dom.cmdPause).removeAttr('disabled');
    $(dom.cmdRun).attr('disabled', true);
    $(dom.modelType).attr('disabled', true);
}
