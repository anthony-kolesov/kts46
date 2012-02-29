(function(){

    function sumArray(array) {
        var result = 0, i, l
        for (i = 0, l = array.length; i < l; i++) { 
            result += array[i]
        }
        return result
    }


    function proc(p) {
        var viewParams = this.view
          , model = this
          , scale = viewParams.scale
          , startx, starty, endx, endy, startName, endName, startPoint, endPoint, roads, i
          , roadx, roady, roadWidth, roadHeight, road
        p.setup = function() {
            p.size(viewParams.size.x * scale, viewParams.size.y * scale)
            p.background(200)
            p.stroke(0)
            p.fill(0)
            p.scale(scale)
            for (roads = Object.keys(model.roads), i = 0, road = model.roads[roads[i]]; i < roads.length; ++i, road = model.roads[roads[i]]) {

                startName = road.points[0][0]
                endName = road.points[1][0]
                startPoint = startName in model.endpoints ? model.endpoints[startName] : model.crossroads[startName]
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
            } 
        }
    }

    function drawModel(model) {
        var canvas = document.getElementById('drawboard')
          , p = new Processing(canvas, proc.bind(model) )
        p.exit()
    }

    $(document).ready(function(){
        $('#open').click(function(){
            var file = document.getElementById('model-file').files[0]
              , reader = new FileReader()
            reader.onload = function(e) {
                drawModel(JSON.parse(e.target.result))
            }
            reader.onerror = function(e) {
                console.log(e)
            }
            reader.readAsText(file)
        })
    })
})()
