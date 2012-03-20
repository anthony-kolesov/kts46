(function(){

    function sumArray(array) {
        var result = 0, i, l
        for (i = 0, l = array.length; i < l; i++) { 
            result += array[i]
        }
        return result
    }


    function proc(p) {
        var model = this
        p.draw = drawFrame.bind(p, model)
        p.setup = function() {
            p.frameRate(model.viewParameters.frameRate)
            p.size(model.viewParameters.size.x * model.viewParameters.scale,
                   model.viewParameters.size.y * model.viewParameters.scale)
            p.background(200)

            // Setup traffic lights
            model.framesCount = 0
            model.trafficLightsStates = {}

            drawRoads(p, model)
        }
    }

    
    function drawRoads(p, model) {
        var road, roadId, horizontalRoad, tlid, tl
        p.scale(model.viewParameters.scale)
        for (roadId in model.view.roads) {
            if (!model.view.roads.hasOwnProperty(roadId))
                continue
            p.stroke(0)
            p.fill(0)
            road = model.view.roads[roadId]
            horizontalRoad = Math.abs(road.x1 - road.x2) > Math.abs(road.y1 - road.y2)
            p.beginShape()
            if (horizontalRoad) {
                p.vertex(road.x1, road.y1 - road.width/2)
                p.vertex(road.x2, road.y2 - road.width/2)
                p.vertex(road.x2, road.y2 + road.width/2)
                p.vertex(road.x1, road.y1 + road.width/2)
            } else {
                p.vertex(road.x1 + road.width/2, road.y1)
                p.vertex(road.x2 + road.width/2, road.y2)
                p.vertex(road.x2 - road.width/2, road.y2)
                p.vertex(road.x1 - road.width/2, road.y1)
            }
            p.endShape()
            // Middle line
            p.stroke(255)
            p.line(road.x1, road.y1, road.x2, road.y2)

            // Traffic lights
            for (tlid in road.trafficLights) {
                if (road.trafficLights.hasOwnProperty(tlid) && tlid in model.trafficLightsStates) {
                    tl = road.trafficLights[tlid]
                    if (model.trafficLightsStates[tlid] === 'g') {
                        p.stroke(0, 255, 0)
                        p.fill(0, 255, 0)
                    } else {
                        p.stroke(255, 0, 0)
                        p.fill(255, 0, 0)
                    }
                    p.rect(tl.coords[0], tl.coords[1], 2, 2)
                }
            }
        }
    }
    

    function drawFrame(model) {
        // Stop if no more cars.
        if (model.cars.length === 0) {
            this.exit()
            return
        }
        
        var currentCars = model.cars.shift()
          , i, l, car, tl

        // Setup traffic lights states.
        if (model.framesCount in model.trafficLights) {
            for (i = 0, l = model.trafficLights[model.framesCount].length; i < l; ++i) {
                tl = model.trafficLights[model.framesCount][i]
                model.trafficLightsStates[tl.id] = tl.state
            }
        }

        drawRoads(this, model)
        this.stroke(255)
        this.fill(255)
        for (i = 0, l = currentCars.length; i < l; ++i) {
            car = currentCars[i]
            // road = model.view.roads[car.road || 0]
            this.rect(car.p[0], car.p[1], car.l, car.w)
        }

        model.framesCount += 1
    }


    function drawModel(model) {
        var canvas = document.getElementById('drawboard')
          , p = new Processing(canvas, proc.bind(model) )
    }

    $(document).ready(function(){
        $('#open').click(function(){
            var file = document.getElementById('model-file').files[0]
              , reader = new FileReader()
            reader.onload = function(e) {
                drawModel(JSON.parse(e.target.result))
            }
            reader.onerror = console.log
            reader.readAsText(file)
        })
    })
})()
