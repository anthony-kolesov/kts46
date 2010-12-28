(function($){
$(document).ready(function(){

    $.getJSON('/api/projectStatus/kts_3/', function(data) {
        var progressBlock = $('.progress-block');
        for (var i in data) {
            if (data.hasOwnProperty(i)) {
                var bar = $('<div class="progressbar"></div>');
                bar.attr('id', data[i].name + '-progressbar')
                progressBlock.append(bar);
                var progress = Math.round(data[i].done / data[i].total * 100);
                bar.progressbar({value:  progress});
            }
        }
    });

});
})(jQuery);
