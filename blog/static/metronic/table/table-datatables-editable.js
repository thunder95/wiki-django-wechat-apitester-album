var TableDatatablesEditable = function () {

    var handleTable = function () {

        function restoreRow(oTable, nRow) {
            var aData = oTable.fnGetData(nRow);
            var jqTds = $('>td', nRow);

            for (var i = 0, iLen = jqTds.length; i < iLen; i++) {
                oTable.fnUpdate(aData[i], nRow, i, false);
            }

            oTable.fnUpdate('<a class="edit" href="javascript:;" title="编辑"><i class="icon-edit"></i></a>', nRow, 6, false);

            oTable.fnUpdate('<a class="delete" href="javascript:;" title="删除"><i class="icon-trash"></i></a>', nRow, 7, false);
            oTable.fnDraw();
        }

        function editRow(oTable, nRow) {
            var aData = oTable.fnGetData(nRow);
            var jqTds = $('>td', nRow);
            jqTds[0].innerHTML = aData[0];
            jqTds[1].innerHTML = '<input type="text" class="form-control input-small" value="' + aData[1] + '">';
            jqTds[2].innerHTML = '<input type="text" class="form-control input-small" value="' + aData[2] + '">';
            jqTds[3].innerHTML = '<input type="text" class="form-control input-small" value="' + aData[3] + '">';
            jqTds[4].innerHTML = '<input type="text" class="form-control input-small" value="' + aData[4] + '">';
            jqTds[5].innerHTML = aData[5]; //取当前时间
            jqTds[6].innerHTML = '<a class="edit" href="javascript:;" title="保存"><i class="icon-edit"></i></a>';
            jqTds[7].innerHTML = '<a class="delete" href="javascript:;" title="删除"><i class="icon-trash"></i></a>';
        }

        //新插入行
        function saveRow(oTable, nRow) {
            var jqInputs = $('input', nRow);
            //oTable.fnUpdate(jqInputs[0].value, nRow, 0, false);
            oTable.fnUpdate(jqInputs[0].value, nRow, 1, false);
            oTable.fnUpdate(jqInputs[1].value, nRow, 2, false);
            oTable.fnUpdate(jqInputs[2].value, nRow, 3, false);
            oTable.fnUpdate(jqInputs[3].value, nRow, 4, false);
            //oTable.fnUpdate(jqInputs[5].value, nRow, 5, false);
            oTable.fnUpdate('<a class="edit" href="javascript:;" title="编辑"><i class="icon-edit"></i></a>', nRow, 6, false);
            oTable.fnDraw();

            return {
                'record_time': jqInputs[0].value, 
                'height': jqInputs[1].value, 
                'weight': jqInputs[2].value, 
                'head': jqInputs[3].value
            }
        }

        function cancelEditRow(oTable, nRow) {
            var jqInputs = $('input', nRow);
            oTable.fnUpdate(jqInputs[0].value, nRow, 0, false);
            oTable.fnUpdate(jqInputs[1].value, nRow, 1, false);
            oTable.fnUpdate(jqInputs[2].value, nRow, 2, false);
            oTable.fnUpdate(jqInputs[3].value, nRow, 3, false);
            oTable.fnUpdate('<a class="edit" href="">Edit</a>', nRow, 4, false);
            oTable.fnDraw();
        }

        var table = $('#sample_editable_1');

        var oTable = table.dataTable({

            // Uncomment below line("dom" parameter) to fix the dropdown overflow issue in the datatable cells. The default datatable layout
            // setup uses scrollable div(table-scrollable) with overflow:auto to enable vertical scroll(see: assets/global/plugins/datatables/plugins/bootstrap/dataTables.bootstrap.js). 
            // So when dropdowns used the scrollable div should be removed. 
            //"dom": "<'row'<'col-md-6 col-sm-12'l><'col-md-6 col-sm-12'f>r>t<'row'<'col-md-5 col-sm-12'i><'col-md-7 col-sm-12'p>>",

            /*
            "lengthMenu": [
                [5, 15, 20, -1],
                [5, 15, 20, "All"] // change per page values here
            ],*/

            // Or you can use remote translation file
            //"language": {
            //   url: '//cdn.datatables.net/plug-ins/3cfcc339e89/i18n/Portuguese.json'
            //},

            // set the initial value
            "pageLength": -1,
            "searching": false,
            "paging":false,
            "ordering":false,
            "info":false,
            "autoWidth": false,
            "serverSide": false,
            //添加自增序号
            /*
            "fnDrawCallback"    : function(){
            　　this.api().column(0).nodes().each(function(cell, i) {
            　　　　cell.innerHTML =  i + 1;
            　　});
            },*/
            /*
            "language": {
                "lengthMenu": " _MENU_ records"
            },
            "columnDefs": [{ // set default column settings
                'orderable': true,
                'targets': [0]
            }, {
                "searchable": true,
                "targets": [0]
            }],
            "order": [
                [0, "asc"]
            ]*/ // set first column as a default sort by asc
        });

        var tableWrapper = $("#sample_editable_1_wrapper");

        var nEditing = null;
        var nNew = false;

        $('#sample_editable_1_new').click(function (e) {
            e.preventDefault();

            if (nNew && nEditing) {
                swal({
                  title: "出错了",
                  text: "之前的行数据未保存,请先保存",
                  type: "error",
                  confirmButtonText: "关闭"
                });
                return false;
                /*
                if (confirm("之前的行数据未保存,您要保存吗?")) {
                    saveRow(oTable, nEditing); // save
                    $(nEditing).find("td:first").html("Untitled");
                    nEditing = null;
                    nNew = false;

                } else {
                    oTable.fnDeleteRow(nEditing); // cancel
                    nEditing = null;
                    nNew = false;
                    
                    return;
                }*/
            }
            var newId = parseInt($('tr:last').children().eq(0).html())+1;

            var aiNew = oTable.fnAddData([newId, '', '', '', '', '', '', '']);
            var nRow = oTable.fnGetNodes(aiNew[0]);
            editRow(oTable, nRow);
            nEditing = nRow;
            nNew = true;
        });

        table.on('click', '.delete', function (e) {
            e.preventDefault();
            swal({
                title: "您确定要执行此删除操作吗？",
                type: "warning",
                showCancelButton: true,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "确定",
                cancelButtonText: "取消",
                closeOnConfirm:false,  
                closeOnCancel:false  
            }).then((result) => {
                if (result) {
                    var nRow = $(this).parents('tr')[0];
                    var td_first = $(this).parent().siblings().eq(0);

                    oTable.fnDeleteRow(nRow);
                    var growth_id = td_first.attr('growth-id');
                    if (growth_id) {
                        delete_growth({'growth_id':growth_id});
                    }
                    
                }
            }) 

            /*
            if (confirm("您确定要删除此行记录吗?") == false) {
                return;
            }*/


        });

        table.on('click', '.cancel', function (e) {
            e.preventDefault();
            if (nNew) {
                oTable.fnDeleteRow(nEditing);
                nEditing = null;
                nNew = false;
            } else {
                restoreRow(oTable, nEditing);
                nEditing = null;
            }
        });

        table.on('click', '.edit', function (e) {
            e.preventDefault();
            nNew = false;
            
            /* Get the row as a parent of the link that was clicked on */
            var nRow = $(this).parents('tr')[0];
            var td_first = $(this).parent().siblings().eq(0)
            var growth_id = td_first.attr('growth-id');
            if (!growth_id) growth_id = '-1'
            var params;
         
            if (nEditing !== null && nEditing != nRow) {
                /* Currently editing - but not this row - restore the old before continuing to edit mode */
                restoreRow(oTable, nEditing);
                editRow(oTable, nRow);
                nEditing = nRow;

            } else if (nEditing == nRow && this.title == "保存") {
                /* Editing this row and want to save it */
                params = saveRow(oTable, nEditing);
                nEditing = null;
                params['growth_id'] = growth_id;
                save_growth(params, td_first);
            } else {
                /* No edit in progress - let's start one */
                editRow(oTable, nRow);
                nEditing = nRow;
            }
            
        });
    }

    return {

        //main function to initiate the module
        init: function () {
            handleTable();
        }

    };

}();

var media_selected = []; //存全量
var id_selected = [];//存id

var media_option = 0; //0成长记录不限, 1置顶只能选一个， 2轮播图只选择12个确定的
var MediaTable = function(){

    var handleTable = function(){
        var table = $('#media-table');
        table.on('click', 'tr', function () {
            var id = $(this).children().eq(0).html();
            var tmp = {'src':'', 'id':id, 'name':$(this).children().eq(1).html()};

            if($(this).find('img').length) {
                tmp.src = $(this).find('img')[0].src;
            } else  {
                if (media_option>0) {
                    /*
                    swal({
                      title: "出错了",
                      text: "此选项不可以设置视频",
                      type: "error",
                      confirmButtonText: "关闭"
                    });*/
                    alert("此选项不可以设置视频");
                    return false;
                }
                tmp.src = $(this).find('video')[0].src;
            }

            //判断数量
            console.log(media_selected.length);
            if (media_option == 2 && media_selected.length > 12) {
                /*
                swal({
                      title: "出错了",
                      text: "轮播图片最多选择12张",
                      type: "error",
                      confirmButtonText: "关闭"
                    });*/
                    alert("轮播图片最多选择12张");
                    return false;
            } else if (media_option < 2 && media_selected.length > 0){
                    alert("只能选择一个");
                    return false;

            } 

            //判断是否存在
            var index = $.inArray(id, id_selected);
     
            if ( index === -1 ) {
                //选中
                $(this).addClass('selected');
                id_selected.push(id);
                media_selected.push( tmp );
            } else {
                //未选中
                $(this).removeClass('selected');
                id_selected.splice( index, 1 );
                media_selected.splice( index, 1 );
            }
            //console.log(id_selected);
            //console.log(media_selected);
            //$(this).toggleClass('selected');
        } );

        var oTable = table.dataTable({
            bLengthChange: false, //改变每页显示数据数量  
            ordering: false,
            processing: true,
            serverSide: true,
            info:false,
            autoWidth: false,
            language: {    
                'emptyTable': '没有数据',    
                'loadingRecords': '加载中...',    
                'processing': '查询中...',    
                'search': '检索:',    
                'zeroRecords': '没有数据',    
                'paginate': {    
                     'first':      '第一页',    
                     'last':       '最后一页',    
                     'next':       '下一页',    
                     'previous':   '上一页',
                 },    
                      
 
            },  
            ajax: {
                url: 'youzi/media',
                type: 'GET'
            },
            columnDefs: [{
                "targets" : 3,//操作按钮目标列
                "data" : null,
                "render" : function(data, type, row) {
                    //var html = "<a href=''></i>" + row[3] + "</a>";
                    var html = '<div class="media-preview"><i class="icon-eye-open"></i><div class="media-hide">'+row[3]+'</div></div>';
                    return html;
                }
            }],
            "rowCallback": function( row, data ) {
                if ( $.inArray(data.DT_RowId, media_selected) !== -1 ) {
                    $(row).addClass('selected');
                }
            }
        });

    }
    return {
        init:function(){
            handleTable();
        }

    }
}();

var EventsTable = function(){

    var handleTable = function(){
        var table = $('#events-table');

        var oTable = table.dataTable({
            bLengthChange: false, //改变每页显示数据数量  
            ordering: false,
            processing: true,
            serverSide: true,
            info:false,
            autoWidth: false,
            language: {    
                'emptyTable': '没有数据',    
                'loadingRecords': '加载中...',    
                'processing': '查询中...',    
                'search': '检索:',    
                'zeroRecords': '没有数据',    
                'paginate': {    
                     'first':      '第一页',    
                     'last':       '最后一页',    
                     'next':       '下一页',    
                     'previous':   '上一页',
                 }
            },  
            ajax: {
                url: 'youzi/events',
                type: 'GET'
            },
            columnDefs: [{
                "targets" : 4,//删除
                "data" : null,
                "render" : function(data, type, row) {
                    //var html = "<a href=''></i>" + row[3] + "</a>";
                    var html = '<i class="icon-trash" events-id="'+row[0]+'"></i>';
                    return html;
                }
            }]
        });


        table.on('click', '.icon-trash', function () {
            var id = $(this).attr('events-id');

            //后台删除
            $.get("youzi/events/delete", { events_id : id },
             function(data){
                console.log(data);
                 //刷新数据
                $('#events-table').DataTable().ajax.reload(null, false); 
            }, 'json');
           
        });

    }
    return {
        init:function(){
            handleTable();
        }

    }
}();
jQuery(document).ready(function() {
    TableDatatablesEditable.init();
    MediaTable.init();
    EventsTable.init();
});