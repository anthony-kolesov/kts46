var RNS = {
    "PREFERENCE_BRANCH": "extensions.rns.",
    "DOM": {
        "carGenIntervalBox": "#car-gen-rate-box",
        "safeDistanceBox": "#safedist-box",
        "minSpeedBox": "#car-speed-min",
        "maxSpeedBox": "#car-speed-max",
        "modelParamBoxes": "#model-params textbox, #model-params button",
        "cmdPause": "#cmd_model_pause",
        "cmdRun": "#cmd_model_run",
        "cmdReset": "#cmd_model_reset",
        "roadCanvas": "#road-canvas",
        "simulationProgress": "#simulation-progress"
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
    var c = $(RNS.DOM.roadCanvas);
    var dc = c.get(0).getContext("2d");
    var model = c.data("model");
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

    dm.draw(dc);
}


// Move cars and redraws canvas.
function updateRoadState() {
    var c = $(RNS.DOM.roadCanvas);
    c.data("model").run_step(40);
    drawModel();

    // Setup new timer.
    var timerId = setTimeout("updateRoadState();", 40);
    $(RNS.DOM.roadCanvas).data("modelTimerId", timerId);
}


/**
 * Draws initial view of canvas.
 */
/*function drawInitialCanvas() {
    // Pause current model, so new model will not be runned by old interval timer.
    pauseModel();

    var c = $(RNS.DOM.roadCanvas);
    var dc = c.get(0).getContext("2d");

    const PyModel = new Components.Constructor(
        "@kolesov.blogspot.com/RoadNetworkModel;1",
        "nsIRoadNetworkModel");
    var model = new PyModel();
    c.data("model", model);
    var descrStr = model.get_description_data();
    var descr = $.parseJSON(descrStr);
    c.data("model-description", descr);

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
}*/

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
    var c = $(RNS.DOM.roadCanvas);
    var timerId = c.data("modelTimerId");
    clearTimeout(timerId);
    c.removeData("modelTimerId");

    // UI modification.
    $(RNS.DOM.cmdPause).attr('disabled', true);
    $(RNS.DOM.cmdRun).removeAttr('disabled');
    $(RNS.DOM.modelParamBoxes).attr('disabled', true);
}


function runModel(){
    if ($(RNS.DOM.roadCanvas).data("modelTimerId")) {
        // Do nothing, because model is already running.
        // Without this model will start to run faster.
        return;
    }
    updateRoadState();

    // UI modification.
    $(RNS.DOM.cmdReset).removeAttr('disabled');
    $(RNS.DOM.cmdPause).removeAttr('disabled');
    $(RNS.DOM.cmdRun).attr('disabled', true);
    $(RNS.DOM.modelParamBoxes).removeAttr('disabled');
}


function getPreferences(){
    return Components.classes["@mozilla.org/preferences-service;1"]
        .getService(Components.interfaces.nsIPrefService)
        .getBranch(RNS.PREFERENCE_BRANCH);
}


function initWindow() {
    $(RNS.DOM.cmdPause).attr('disabled', true);
    $(RNS.DOM.cmdRun).attr('disabled', true);
    $(RNS.DOM.cmdReset).attr('disabled', true);
    $(RNS.DOM.modelParamBoxes).attr('disabled', true);
}


/**
 * Applies changes of parameters to the model.
 */
function applyModelParams() {
    logmsg('Apply model params.');

    let (p = $(RNS.DOM.roadCanvas).data("model").params) {
        p.carGenerationInterval = parseFloat($(RNS.DOM.carGenIntervalBox).val());
        p.safeDistance = parseFloat($(RNS.DOM.safeDistanceBox).val());
        p.maxSpeed = parseFloat($(RNS.DOM.maxSpeedBox).val());
        p.minSpeed = parseFloat($(RNS.DOM.minSpeedBox).val());
    }
}


/**
 * Reset all made, but not applied changes.
 */
function resetModelParams(){
    logmsg("Reset model params.");
}

/**
 * Opens model from the specified file.
 */
function openModel(){
    var nsIFilePicker = Components.interfaces.nsIFilePicker;
    var fp = Components.classes["@mozilla.org/filepicker;1"].createInstance(nsIFilePicker);
    fp.init(window, "Select a File", nsIFilePicker.modeOpen);
    if (fp.show() === nsIFilePicker.returnOK){
        var f = fp.file;

        // This code taken from MDN:
        // https://developer.mozilla.org/en/Code_snippets/File_I//O#section_20
        var yamlData = "";
        var fstream = Components.classes["@mozilla.org/network/file-input-stream;1"].
                        createInstance(Components.interfaces.nsIFileInputStream);
        var cstream = Components.classes["@mozilla.org/intl/converter-input-stream;1"].
                        createInstance(Components.interfaces.nsIConverterInputStream);
        fstream.init(f, -1, 0, 0);
        cstream.init(fstream, "UTF-8", 0, 0);

        let (str = {}) {
          let read = 0;
          do {
            read = cstream.readString(0xffffffff, str); // read as much as we can and put it in str.value
            yamlData += str.value;
          } while (read != 0);
        }
        cstream.close(); // this closes fstream

        $(RNS.DOM.roadCanvas).data("yaml-source", yamlData);
        newModel(yamlData);
    }
}

/**
 * Loads model from YAML description.
 * If there is no description, then default model is used.
 */
function newModel(yamlData) {
    // Pause current model, so new model will not be runned by old interval timer.
    pauseModel();

    var c = $(RNS.DOM.roadCanvas);
    var dc = c.get(0).getContext("2d");

    const PyModel = new Components.Constructor(
        "@kolesov.blogspot.com/RoadNetworkModel;1",
        "nsIRoadNetworkModel");
    var model = new PyModel();

    // Load from YAML if available.
    if (yamlData) {
        model.loadYAML(yamlData);
    } else if (c.data('yaml-source')) {
        model.loadYAML(c.data('yaml-source'));
    }

    c.data("model", model);
    var descrStr = model.get_description_data();
    var descr = $.parseJSON(descrStr);
    c.data("model-description", descr);

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

function simulateModel() {
    var c = $(RNS.DOM.roadCanvas);
    var m = c.data("model");
    var p = function(v, m) {
        $(RNS.DOM.simulationProgress).attr('value', Math.round(v / m)*100);
    };
    m.simulate(100, 0.04, "qq", p);
}
