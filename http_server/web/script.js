var kts46 = (function($){

    // cfg
    var serverPollInterval = 30000;
    var jsonRpcPath = "/json-rpc/";
    
    var addProject = function(){
        $("#add-project-confirm").dialog({
            resizable: false,
            height: 200,
            modal: true,
            buttons: {
                "Add project": function() {
                    var projectName = $('#add-project-name').val();
                    var data = JSON.stringify({
                        "method": "addProject",
                        "id": "addProject_" + projectName,
                        "params": [ projectName ]
                    }) + "\n";
                    var $dialog = $(this);
                    $.post(jsonRpcPath, data, function(data) {
                        $dialog.dialog("close");
                    });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    
    var deleteProject = function(projectName){
        $("#delete-project-confirm").dialog({
            resizable: false,
            height: 200,
            modal: true,
            buttons: {
                "Delete project": function() {
                    var data = JSON.stringify({
                        "method": "deleteProject",
                        "id": "deleteProject_" + projectName,
                        "params": [ projectName ]
                    }) + "\n";
                    var $dialog = $(this);
                    $.post(jsonRpcPath, data, function(data) {
                        $dialog.dialog("close");
                    });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
            }
        });
    };

    
    var addJobAction = function(projectName, allFields, dialog) {
        // Taken from jqueryui.com
        var checkRegexp = function( o, regexp, n ) {
            if ( !( regexp.test( o.val() ) ) ) {
                o.addClass( "ui-state-error" );
                // updateTips( n );
                return false;
            } else {
                return true;
            }
        }
    
        var bValid = true;
        
        allFields.removeClass( "ui-state-error" );
        bValid = bValid && checkRegexp($('#add-job-name'), /^[a-zA-Z][0-9a-zA-Z_]+$/i, "Job name may consist of a-z, A-Z, 0-9, underscores, begin with a letter." );
        bValid = bValid && checkRegexp($('#add-job-count'), /^[0-9]+$/i, "Jobs count must be a number." );

        if ( bValid ) {
            var seriesLength = 1;
            
            // Check series identifier
            var isSeriesDOM = document.getElementById("add-job-is-series");
            if (isSeriesDOM.checked) {
                seriesLength = parseInt($('#add-job-count').val());
            }
            
            var file = document.getElementById('add-job-definition').files[0];
            var reader = new FileReader();
            reader.onload = function(e) {
                var definition = e.target.result;
                var jobName = $('#add-job-name').val();
                
                for(var i=1; i<=seriesLength; i++){
                    var efficientName = jobName;
                    if (seriesLength > 1) {
                        efficientName += '-s' + i; 
                    }
                    
                    var params = JSON.stringify({
                        method: "addJob",
                        id: "addJob_" + projectName + "_" + "efficientName",
                        params: [projectName, efficientName, definition]
                    }) + "\n";
                    $.post(jsonRpcPath, params, function(data) {});
                }
                dialog.dialog( "close" );
            };
            reader.readAsText(file);
        }
    };
    
    var addJob = function(projectName) {
        var allFields = $('#add-job-name, #add-job-definition');
    
        $("#add-job-form").dialog({
            // autoOpen: false,
            height: 300,
            width: 350,
            modal: true,
            buttons: {
                "Add job": function(){ addJobAction(projectName, allFields, $(this)); },
                Cancel: function() { $(this).dialog("close"); }
            },
            close: function() { allFields.val("").removeClass("ui-state-error"); }
        });
    };
    
    
    var deleteJob = function() {
        var buttonProject = $(this).data('project');
        var buttonJob = $(this).data('job');
        $( "#delete-job-confirm" ).dialog({
            resizable: false,
            height:200,
            modal: true,
            buttons: {
                "Delete job": function() {
                    var dialog = $(this);
                    var params = JSON.stringify({
                        method: "deleteJob",
                        id: "deleteJob_" + buttonProject + "_" + buttonJob,
                        params: [buttonProject, buttonJob]
                    }) + "\n";
                    console.log(params);
                    $.post(jsonRpcPath, params, function(data) {
                        dialog.dialog("close");
                    });
                },
                Cancel: function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    
    
    var runJob = function() {
        var p = $(this).data('project');
        var j = $(this).data('job');
        var params = JSON.stringify({
            method: "runJob",
            id: "runJob_" + p + "_" + j,
            params: [p, j]
        }) + "\n";
        $.post(jsonRpcPath, params, function(data) {});
    };    
    
    
    var updateStatus = function() {
        $.getJSON('/api/serverStatus/', function(data) {
            if (data.result === "fail") {
                return;
            }
            
            var progressBlock = $('.progress-block');
            // progressBlock.empty(); // remove previous
            for (var i in data) {
                if (data.hasOwnProperty(i)) {
                    var projectName = data[i].project;
                    var projectBlock = $('#project-progress-'+projectName);
                    if (projectBlock.length == 0) {
                        projectBlock = $('<div class="project-block"></div>');
                        projectBlock.attr('id', 'project-progress-'+projectName);
                        progressBlock.prepend(projectBlock);
                        
                        // Add project name
                        var projNameBlock = $('<div class="project-name"></div>');
                        projNameBlock.append('<span class="name">'+projectName+'</span>');
                        projectBlock.append(projNameBlock);
                        
                        // Button to add job
                        var jobAddButton = $('<button><span class="ui-icon ui-icon-plusthick"></span></button>').button();
                        projNameBlock.append(jobAddButton);
                        jobAddButton.data('project', projectName);
                        jobAddButton.click( function(){ addJob( $(this).data('project') ); });
                        
                        // Project deleter.
                        var projDeleteButton = $('<button><span class="ui-icon ui-icon-closethick"></span></button>').button();
                        projNameBlock.append(projDeleteButton);
                        projDeleteButton.data('project', projectName);
                        projDeleteButton.click( function(){
                            deleteProject($(this).data('project'));
                        } );
                    }
                
                    // Check. If dummy job - skip it. But project will still be
                    // created. That is the point of dummy jobs.
                    if (typeof data[i].visible === "undefined" || data[i].visible) {
                        var jobName = data[i].name;
                        
                        // Job wrapper
                        var wrapperId  = 'job-'+projectName+jobName;
                        var jobContainer = $('#'+wrapperId);
                        if (jobContainer.length === 0) {
                            
                            jobContainer = $('<div class="job-container"></div>');
                            jobContainer
                                .attr('id',wrapperId)
                                .data('project', projectName)
                                .data('job', data[i].name);
                            projectBlock.append(jobContainer);
                        
                            // Job runner
                            var jobRunner = $('<button><span class="ui-icon ui-icon-play"></span></button>');
                            jobContainer.append(jobRunner);
                            jobRunner.addClass('job-start').click(runJob)
                                .data('project', projectName).data('job', data[i].name);
                        
                            // Job deleter
                            var jobDeleter = $('<button><span class="ui-icon ui-icon-closethick"></span></button>');
                            jobContainer.append(jobDeleter);
                            jobDeleter.addClass('job-delete').click(deleteJob)
                                .data('project', projectName).data('job', data[i].name);;
                        
                            // Job name
                            var name = $('<div class="job-name"></div>');
                            name.text(data[i].name);
                            jobContainer.append(name);
                    
                            // Job progress value
                            var progressNum = $('<div class="progress-num"></div>');
                            jobContainer.append(progressNum);
                            //progressNum.text([data[i].done, '/', data[i].total].join(""));
                        
                            // Job progressbar
                            var bar = $('<div class="progressbar"></div>');
                            bar.attr('id', jobName + '-progressbar')
                            jobContainer.append(bar);
                            //var progress = Math.round(data[i].done / data[i].total * 100);
                            //bar.progressbar({value:  progress});
                            
                            // Click handler
                            var showStats = function(){
                                var c = $(this).parent();
                                var stats = $('.jobstatistics', c);
                                
                                if (stats.length !== 0) {
                                    stats.remove();
                                } else {
                                    var p = c.data('project');
                                    var j = c.data('job');
                                    var path = ['/api/jobStatistics/',p,'/',j,'/'].join('');
                                    $.getJSON(path, function(data){
                                        stats = $('<pre></pre>');
                                        stats.addClass("jobstatistics");
                                        stats.text(JSON.stringify(data, null, 4));
                                        c.append(stats);    
                                    } );
                                }
                            };
                            bar.click(showStats);
                            progressNum.click(showStats);

                        }
                        
                        // Set progress.
                        $('.progress-num', jobContainer)
                            .text([data[i].done, '/', data[i].total].join(""));
                        var progress = Math.round(data[i].done / data[i].total * 100);
                        $(['#', jobName, '-progressbar'].join("")).progressbar({value:  progress});

                    }
                }
            }
            
            $('.progress-block .last-update-time').text( 'Last update time: ' + new Date() );
        });
    };
    
    // on ready
    $('.jqueryui-button').button();
    $('.add-project-button').click(addProject);
    updateStatus();
    setInterval("kts46.updateStatus();", serverPollInterval);
    
    // google table
    google.load('visualization', '1', {packages:['table']});
    var drawTable = function() {
        console.log("BBBBBBBBBBBB");
        var query = new google.visualization.Query("/api/serverStatus2/");
        console.log(query);
        query.send( function(response){
            console.log('AAAAAAAAAAAAAAAAA');
            var dataTable = response.getDataTable();
            var table = new google.visualization.Table(document.getElementById('progress-table-2'));
            table.draw(dataTable, {showRowNumber: true});
        } );
    };
    google.setOnLoadCallback(drawTable);
    
    return {'updateStatus': updateStatus};
    
})(jQuery);
