(function($){
$(document).ready(function(){

    $.getJSON('/api/serverStatus/', function(data) {
        var progressBlock = $('.progress-block');
        for (var i in data) {
            if (data.hasOwnProperty(i)) {
                var projectName = data[i].project;
                var projectBlock = $('#project-progress-'+projectName);
                if (projectBlock.length === 0) {
                    projectBlock = $('<div class="project-block"></div>');
                    projectBlock.attr('id', 'project-progress-'+projectName);
                    progressBlock.append(projectBlock);
                    
                    // Add project name
                    var projNameBlock = $('<h2 class="project-name"></h2>');
                    projNameBlock.text(projectName);
                    projectBlock.append(projNameBlock);
                }
            
                var name = $('<div class="job-name"></div>');
                name.text(data[i].name);
                projectBlock.append(name);
            
                var progressNum = $('<div class="progress-num"></div>');
                projectBlock.append(progressNum);
                progressNum.text([data[i].done, '/', data[i].total].join(""));
                
                var bar = $('<div class="progressbar"></div>');
                bar.attr('id', data[i].name + '-progressbar')
                projectBlock.append(bar);
                var progress = Math.round(data[i].done / data[i].total * 100);
                bar.progressbar({value:  progress});
            }
        }
    });

});
})(jQuery);
