var kts46 = (function($){

    // cfg
    var serverPollInterval = 5000,
        jsonRpcPath = "/json-rpc/",
        projectColumnId = 0,
        jobColumnId = 1,
        doneColumnId = 2,
        totalColumnId = 3,
        statsFinishedColumnId = 4,
        progressColumnId = 5,
        googleTableId = "progress-table-2";
    
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
    
    var deleteProject = function(){
        var projectNameElem = $('#delete-project-name');
        fillWithProjects(projectNameElem);
        
        $("#delete-project-confirm").dialog({
            resizable: false,
            height: 200,
            modal: true,
            buttons: {
                "Delete project": function() {
                    var projectName = projectNameElem.val(),
                        data = JSON.stringify({
                            "method": "deleteProject",
                            "id": "deleteProject_" + projectName,
                            "params": [ projectName ]
                        }) + "\n";
                        closeClb = (function() {$(a).dialog("close");}).bind({a:this});
                    $.post(jsonRpcPath, data, closeClb);
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
    
    var addJob = function() {
        var allFields = $('#add-job-name, #add-job-definition');
        var projectNameElem = $('#add-job-project-name');
        fillWithProjects(projectNameElem);
    
        $("#add-job-form").dialog({
            // autoOpen: false,
            height: 300,
            width: 350,
            modal: true,
            buttons: {
                "Add job": function(){ addJobAction(projectNameElem.val(), allFields, $(this)); },
                Cancel: function() { $(this).dialog("close"); }
            },
            close: function() { allFields.val("").removeClass("ui-state-error"); }
        });
    };
    
    
    var deleteJob = function(project, job) {
        $( "#delete-job-confirm" ).dialog({
            resizable: false,
            height:200,
            modal: true,
            buttons: {
                "Delete job": function() {
                    var dialog = $(this);
                    var params = JSON.stringify({
                        method: "deleteJob",
                        id: "deleteJob_" + project + "_" + job,
                        params: [project, job]
                    }) + "\n";
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
    
    
    var runJob = function(project, job) {
        var params = JSON.stringify({
            method: "runJob",
            id: "runJob_" + project + "_" + job,
            params: [project, job]
        }) + "\n";
        $.post(jsonRpcPath, params, function(data) {});
    };
    
    
    var updateStatus = function() {
        
        var query = new google.visualization.Query("/api/serverStatus2/");
        query.send( function(response){
            var dataTable = response.getDataTable();
            
            // Store table
            $(document).data('simulation-data', dataTable);

            // Add progress column.
            dataTable.addColumn("number", "Progress");
            for (var rowNum = 0, l = dataTable.getNumberOfRows(); rowNum < l; ++rowNum ){
                var total = dataTable.getValue(rowNum, totalColumnId),
                    done = dataTable.getValue(rowNum, doneColumnId), 
                    v =  done / total,
                    f = [done, total].join("/");
                dataTable.setCell(rowNum, progressColumnId, v, f);
            }
            
            // progress formatter.
            var formatterOptions = {
                    width: 120,
                    base: 0,
                    min: 0,
                    max: 1,
                    showValue: true
            };
            var progressFormatter = new google.visualization.BarFormat(formatterOptions);
            progressFormatter.format(dataTable, progressColumnId);

            var view = new google.visualization.DataView(dataTable);
            view.setColumns([projectColumnId, jobColumnId, progressColumnId,
                             statsFinishedColumnId]);

            var table = $(document).data('google-table');
            table.draw(view, {showRowNumber: true, allowHtml: true});
            $('.progress-block .last-update-time').text( 'Last update time: ' + new Date() );
        } );
    };
    
    
    var getSelectedJobs = function() {
        return $(document).data('google-table').getSelection().map( function(it){ return it.row; } );
    };
    
    
    var getProjects = function() {
        return $(document).data('simulation-data').getDistinctValues(projectColumnId);
    };
    
    
    var fillWithProjects = function(target) {
        var projects = getProjects();
        target.empty();
        for (var i=0, l = projects.length; i < l; ++i) {
            target.append(['<option value="', projects[i] ,'">',projects[i],'</option>'].join(""))
        }  
    };
    
    
    /* Runs specified action on all selected projects.
     * :param action: function(projectName, jobName)
     */
    var forSelectedJobs = function(action) { 
        var jobs = getSelectedJobs(),
            table = $(document).data('simulation-data'),
            i, l;
        if (typeof table === "undefined") return;
        for(i = 0, l = jobs.length; i < l; ++i){
            var p = table.getValue(jobs[i], projectColumnId),
                j = table.getValue(jobs[i], jobColumnId);
            action(p, j);
        }
    };
    
    
    var showStatistics = function() {
        var jobs = getSelectedJobs(),
            doc = $(document),
            job, project, path;
        if (jobs.length === 0) return;
        
        job = doc.data('simulation-data').getValue(jobs[0], jobColumnId);
        project = doc.data('simulation-data').getValue(jobs[0], projectColumnId);    
        
        $.getJSON(['/api/jobStatistics', project, job, ''].join('/'), function(data){
            var text = JSON.stringify(data, null, 4); // 4 is amount of spaces.    
            $('#show-stats-dialog .content').text(text);
            $('#show-stats-dialog').dialog({
                modal: true,
                buttons: { Ok: function(){ $(this).dialog("close"); } }
            });
        } );
    };
    
    
    // google table
    google.load('visualization', '1', {packages:['table']});
    google.setOnLoadCallback( function() {
        updateStatus();
        setInterval(updateStatus, serverPollInterval);
    });
    
    // on ready
    $(document).ready(function(){
        $(this).data('google-table', new google.visualization.Table(document.getElementById(googleTableId)));
        
        // Buttons
        $('.jqueryui-button').button();
        $('#simulation-add-project')
            .button({text: false, icons: {primary: "ui-icon-play"}})
            .click(addProject);
        $('#simulation-delete-project')
            .button({text: false, icons: {primary: "ui-icon-trash"}})
            .click(deleteProject);
        $('#simulation-add-job')
            .button({text: false,icons: {primary:"ui-icon-plus"}})
            .click(addJob);
        $('#simulation-start-job')
            .button({text: false,icons: {primary:"ui-icon-play"}})
            .click(forSelectedJobs.bind({}, runJob.bind({}) ));
        $('#simulation-delete-job')
            .button({text: false,icons: {primary:"ui-icon-trash"}})
            .click(forSelectedJobs.bind({}, deleteJob.bind({}) ));
        $('#show-statistics').button().click(showStatistics);
    });
    
    return {
        //"g": getSelectedJobs.bind({}),
        "updateStatus": updateStatus,
        "runJob": runJob
    };
    
})(jQuery);
