var dom = {
    "roadCanvas": "#road-canvas",
    "cmdPause": "#cmd_model_pause",
    "cmdRun": "#cmd_model_run",
    "modelType": "#model-type"
};
var RNS = {
    "PREFERENCE_BRANCH": "extensions.rns.",
    "DOM": {
        "carGenIntervalBox": "#car-gen-rate-box",
        "modelParamBoxes": "#model-params textbox, #model-params button"
    }
};

//function runQuery() {
//    //const SimpleConstructor = new Components.Constructor("@mozilla.org/js_simple_component;1", "nsISimple");
//    var SimpleConstructor = new Components.Constructor("@mozilla.org/PySimple;1", "nsISimple");
//    var s = new SimpleConstructor();
//    document.getElementById("query-text").value = s.yourName;
//}


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

function drawModel() {
    var c = $(dom.roadCanvas);
    var dc = c.get(0).getContext("2d");
    var model = c.data("model");
    var modelType = c.data("model-type");
    if (modelType === "py") {
        var dm = c.data("draw-model");
        var stateStr = model.get_state_data();
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
        var r = new Road({"length": 300, "width": 10});
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
        var drawingModel = new Model({
            "road":road,
            "lights":lights,
            "cars": {}
        });
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
    $(RNS.DOM.modelParamBoxes).attr('disabled', true);
}


function runModel(){
    if ($(dom.roadCanvas).data("modelTimerId")) {
        // Do nothing, because model is already running.
        // Without this model will start to run faster.
        return;
    }
    updateRoadState();

    // UI modification.
    $(dom.cmdPause).removeAttr('disabled');
    $(dom.cmdRun).attr('disabled', true);
    $(dom.modelType).attr('disabled', true);
    $(RNS.DOM.modelParamBoxes).removeAttr('disabled');
}


function getPreferences(){
    return Components.classes["@mozilla.org/preferences-service;1"]
        .getService(Components.interfaces.nsIPrefService)
        .getBranch(RNS.PREFERENCE_BRANCH);
}


/**
 * Applies changes of parameters to the model.
 */
function applyModelParams() {
    logmsg('Apply model params.');

    var c = $(dom.roadCanvas);
    var model = c.data("model");
    model.params.carGenerationInterval = $(RNS.DOM.carGenIntervalBox).val();
}


/**
 * Reset all made, but not applied changes.
 */
function resetModelParams(){
    logmsg("Reset model params.");
}
