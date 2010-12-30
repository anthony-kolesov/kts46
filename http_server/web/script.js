var kts46 = (function($){

    // cfg
    var serverPollInterval = 50000; 
    
    var addJob = function(projectName) {
        var allFields = $('#add-job-name, #add-job-definition');
    
        $("#add-job-form").dialog({
            //autoOpen: false,
            height: 300,
            width: 350,
            modal: true,
            buttons: {
                "Add job": function() {
                    // Taken from jqueryui.com
                    var checkRegexp = function( o, regexp, n ) {
                        if ( !( regexp.test( o.val() ) ) ) {
                            o.addClass( "ui-state-error" );
                            //updateTips( n );
                            return false;
                        } else {
                            return true;
                        }
                    }
                
                    var bValid = true;
                    
                    allFields.removeClass( "ui-state-error" );
                    bValid = bValid && checkRegexp($('#add-job-name'), /^[a-zA-Z]([0-9a-zA-Z_])+$/i, "Job name may consist of a-z, A-Z, 0-9, underscores, begin with a letter." );
        
                    if ( bValid ) {
                        var file = document.getElementById('add-job-definition').files[0];
                        var reader = new FileReader();
                        var dialog = $(this);
                        reader.onload = function(e) {
                            var definition = e.target.result;
                            var params = JSON.stringify({
                                project: projectName,
                                job:  $('#add-job-name').val(),
                                definition: definition
                            }) + "\n\n";
                            $.post('/api/addJob/', params, function(data) {});
                            dialog.dialog( "close" );
                        };
                        reader.readAsText(file);
                    }
                },
                Cancel: function() {
                    $( this ).dialog( "close" );
                }
            },
            close: function() {
                allFields.val( "" ).removeClass( "ui-state-error" );
            }
        });
    };
    
    
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
                        var projNameBlock = $('<div class="project-name"></div>');
                        projNameBlock.text(projectName);
                        projectBlock.append(projNameBlock);
                        
                        // Project deleter.
                        var projDeleteButton = $('<button>Delete</button>').button();
                        projNameBlock.append(projDeleteButton);
                        projDeleteButton.data('project', projectName);
                        projDeleteButton.click( function(){
                            var buttonProject = $(this).data('project');
                            $( "#delete-project-confirm" ).dialog({
                                resizable: false,
                                height:200,
                                modal: true,
                                buttons: {
                                    "Delete project": function() {
                                        $( this ).dialog( "close" );
                                        $('#add-project-name').text('Deleting project...');
                                        var projName = buttonProject;
                                        $.getJSON('/api/deleteProject/' + projName + '/', function(data) {
                                            $('#add-project-name').text('Project deleted.');
                                        });
                                    },
                                    Cancel: function() {
                                        $( this ).dialog( "close" );
                                    }
                                }
                            });
                        } );
                        
                        // Button to add job
                        var jobAddButton = $('<button>Add job</button>').button();
                        projNameBlock.append(jobAddButton);
                        jobAddButton.data('project', projectName);
                        jobAddButton.click( function(){ addJob( $(this).data('project') ); });
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
