var kts46 = (function($){

    // cfg
    var serverPollInterval = 5000; 
    
    var updateStatus = function() {
        $.getJSON('/api/serverStatus/', function(data) {
            var progressBlock = $('.progress-block');
            progressBlock.empty(); // remove previous
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
                
                    // Check. If dummy job - skip it. But project will still be created. That is the point of dummy jobs.
                    if (typeof data[i].visible === "undefined" || data[i].visible) {
                        // Job name
                        var name = $('<div class="job-name"></div>');
                        name.text(data[i].name);
                        projectBlock.append(name);
                    
                        // Job progress value
                        var progressNum = $('<div class="progress-num"></div>');
                        projectBlock.append(progressNum);
                        progressNum.text([data[i].done, '/', data[i].total].join(""));
                        
                        // Job progressbar
                        var bar = $('<div class="progressbar"></div>');
                        bar.attr('id', data[i].name + '-progressbar')
                        projectBlock.append(bar);
                        var progress = Math.round(data[i].done / data[i].total * 100);
                        bar.progressbar({value:  progress});
                    }
                }
            }
            
            progressBlock.append( 'Last update time: ' + new Date() )
        });
    };
    
    var addProject = function(){
        $('#add-project-name').text('Adding project...');
        var projName = $('#add-project-name').val();
        $.getJSON('/api/addProject/' + projName + '/', function(data) {
            $('#add-project-name').text('Project added.');
        });
    };

    $(document).ready(function(){
        $('.jqueryui-button').button();
        $('.add-project-button').click(addProject);
        kts46.updateStatus();
        setInterval("kts46.updateStatus();", serverPollInterval);
    });
    
    return {'updateStatus': updateStatus};
    
})(jQuery);
