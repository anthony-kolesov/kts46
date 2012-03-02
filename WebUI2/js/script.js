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
          , roads, road, roadId, horizontalRoad
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
