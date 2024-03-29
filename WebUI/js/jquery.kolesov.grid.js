/*
License:
Copyright 2010 Anthony Kolesov

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

*/

(function($){
  
  /*
   * Columns info: name, type
   * Row format: {_id: somevalue, <columnname>:<columnvalue>* }
   */
  
  $.fn.grid = function(){
    if (arguments.length === 0) {
      throw "Method name must be provided!";
    }
    
    var methodName = arguments[0];
    
    var $t = $(this);
   
    if (methodName === 'initialize') {
      var columns = arguments[1].columns;
      
      $t.each(function(){
        var thead = $('<thead></thead>');
        var header = $('<tr></tr>');
        thead.append(header);
        $.each(columns, function(i,n){
          var cell = $('<th></th>');
          header.append(cell);
          cell.text(n.name);
        });
        
        var tbody = $('<tbody></tbody>');
        tbody.data('rows', {});
        /*var trow = $('<tr></tr>');
        tbody.append(trow);
        $.each(columns, function(i,n){
          var cell = $('<td></td>');
          trow.append(cell);
          cell.text(i);
        });*/
        $(this).append(thead).append(tbody);
      });
    } else if (methodName === 'setRows') {
        var body = $('tbody', t);
        var rowsData = body.data('rows');
        
        if (arguments.length == 1) {
            throw "Rows to set must be provided."; 
        }
        var rows = arguments[1];
        
        // Remove current rows that aren't in new table.
        for (var curRowId in rowsData) {
            if (rowsData.hasOwnProperty(curRowId)) {
                
            }
        }
        
        for (var i = 0, l = rows.length; i < l; ++i ) {
            var row = rows[i];
            if (rowsData[row['_id']]) {
                
            }
        }
    }
    
    return this;
  };
  
  
})(jQuery);
