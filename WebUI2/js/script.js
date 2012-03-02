(function(){

    function sumArray(array) {
        var result = 0, i, l
        for (i = 0, l = array.length; i < l; i++) { 
            result += array[i]
        }
        return result
    }


    function proc(cars, p) {
        var viewParams = this.viewParameters
          , model = this
          , scale = viewParams.scale
          , startx, starty, endx, endy, startName, endName, startPoint, endPoint, roads, i
          , roadx, roady, roadWidth, roadHeight, road
          , roadId, horizontalRoad
        p.draw = drawFrame.bind(p, model, cars)
        p.setup = function() {
            p.frameRate(1 / viewParams.frameRate)

            p.size(viewParams.size.x * scale, viewParams.size.y * scale)
            p.background(200)
            p.stroke(0)
            p.fill(0)
            p.scale(scale)
            
            for (roadId in model.view.roads) {
                if (!model.view.roads.hasOwnProperty(roadId))
                    continue
                road = model.view.roads[roadId]
                horizontalRoad = Math.abs(road.x1 - road.x2) > Math.abs(road.y1 - road.y2)
                p.beginShape()
                if (horizontalRoad) {
                    p.vertex(road.x1, road.y1 - road.width)
                    p.vertex(road.x2, road.y2 - road.width)
                    p.vertex(road.x2, road.y2 + road.width)
                    p.vertex(road.x1, road.y1 + road.width)
                } else {
                    p.vertex(road.x1 + road.width, road.y1)
                    p.vertex(road.x2 + road.width, road.y2)
                    p.vertex(road.x2 - road.width, road.y2)
                    p.vertex(road.x1 - road.width, road.y1)
                }
                p.endShape()
            }
            
            /*for (roads = Object.keys(model.view.roads), i = 0, road = model.view.roads[roads[i]]; i < roads.length; ++i, road = model.view.roads[roads[i]]) {

            
            
                startName = road.points[0][0]
                endName = road.points[1][0]
                startPoint = startName in model.endpoints ? model.view.endpoints[startName] : model.crossroads[startName]
                endPoint = endName in model.endpoints ? model.endpoints[endName] : model.crossroads[endName]
                startx = startPoint.coords.x
                starty = startPoint.coords.y                
                endx = endPoint.coords.x                
                endy = endPoint.coords.y                
            
                if (startx === endx) {
                    roadWidth = sumArray(road.lines) * 3
                    roadHeight = endy - starty
                    roadx = startx - roadWidth / 2
                    roady = starty
                } else {
                    roadWidth = endx - startx
                    roadHeight = sumArray(road.lines) * 3
                    roadx = startx
                    roady = starty - roadHeight / 2
                }
                p.rect(roadx, roady, roadWidth, roadHeight)
                // Save for future use
                road.view = {start: {x: startx, y: starty}, end: {x: endx, y: endy} }
            }*/
        }
    }


    function drawFrame(model, cars) {
        var currentCars = cars.shift()
          , i, l, road, car
        /*for (i = 0, l = currentCars.length; i < l; ++i) {
            car = currentCars[i]
            road = model.roads[car.road || 0]
        }*/
        //this.point(model.pointx++, model.pointy++)
    }


    function drawModel(model, cars) {
        var canvas = document.getElementById('drawboard')
          , p = new Processing(canvas, proc.bind(model, cars) )
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
