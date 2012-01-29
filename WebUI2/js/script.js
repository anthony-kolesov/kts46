(function(){
    $(document).ready(function(){
        $('#open').click(function(){
            var file = document.getElementById('model-file').files[0]
              , reader = new FileReader()
            reader.onload = function(e) {
                var modelDefinition = e.target.result
                alert(modelDefinition)
            }
            reader.onerror = function(e) {
                console.log(e)
            }
            reader.readAsText(file)
        })
    })
})()
