/**
* Created by Liujiang on 2016/8/25.
*/


//  监听键盘ctrl键，用于批量修改主机上线下线状态
    window.globalCtrlKeyStatus = false;
    window.onkeydown = function (event) {
        if(event && event.keyCode == 17){
            window.globalCtrlKeyStatus = true;
        }
    };
    window.onkeyup = function (event) {
        if(event && event.keyCode == 17){
            window.globalCtrlKeyStatus = false;
        }
    };
//  select元素的value和text的映射表
    var HOST_STATUS = {
        "1":"在线",
        "0":"下线"
    };
//  编辑模式全局标识符
    var EDIT_MODE = false;
//  编辑模式按钮动作
    $("#edit").click(function () {
        if(EDIT_MODE){
            EDIT_MODE = false;
            $(this).removeClass("btn-danger");
            $(this).addClass("btn-success");
            $(this).html('<span class="glyphicon glyphicon-edit" aria-hidden="true"></span>&nbsp;进入编辑模式');
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if($(this).prop("checked")){
                    var tr = $(this).parent().parent();
                    rowOutEditing(tr);
                }
             });
        }else{
            EDIT_MODE = true;
            $(this).removeClass("btn-success");
            $(this).addClass("btn-danger");
            $(this).html('<span class="glyphicon glyphicon-off" aria-hidden="true"></span>&nbsp;退出编辑模式');
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if($(this).prop("checked")){
                    var tr = $(this).parent().parent();
                    rowInEditing(tr);
                }
             });
        }
    });
//        全选按钮动作
    $("#all").click(function () {
        if(EDIT_MODE){
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if(!$(this).prop("checked")){
                    $(this).prop("checked",true);
                    var tr = $(this).parent().parent();
                    rowInEditing(tr);
                }
             });
        }else{
            $('input[type="checkbox"]').prop("checked",true);
        }
    });
//      取消按钮动作
    $("#cancel").click(function () {
        if(EDIT_MODE){
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if($(this).prop("checked")){
                    $(this).prop("checked",false);
                    var tr = $(this).parent().parent();
                    rowOutEditing(tr);
                }
             });
        }else{
            $('input[type="checkbox"]').prop("checked",false);
        }
    });
//        反选按钮动作
    $("#reverse").click(function () {
        if(EDIT_MODE){
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if(!$(this).prop("checked")){
                    $(this).prop("checked",true);
                    var tr = $(this).parent().parent();
                    rowInEditing(tr);
                }else{
                    $(this).prop("checked",false);
                    var tr = $(this).parent().parent();
                    rowOutEditing(tr);
                }
             });
        }else{
            var checkboxes = $('input[type="checkbox"]');
            checkboxes.each(function () {
                if($(this).prop("checked")){
                    $(this).prop("checked",false);
                }else{
                    $(this).prop("checked",true);
                }
            });
        }
    });
//        单行进入编辑模式
    function rowInEditing(ths) {
        $(ths).children().each(function () {
            if($(this).attr("editEnable")){
                if($(this).attr("eleType")=="select"){
                    var select_value = $(this).attr("value");
                    var source_address = $(this).attr("source");
                    var select_element = createSelect(select_value,source_address);
                    $(this).html(select_element);
                }else{
                    var text = $(this).text();
                    var html = "<input type='text' style='width:100%;' value='"+text+"'/>";
                    $(this).html(html);
                }
            }

        });
    }
//        单行退出编辑模式
    function rowOutEditing(ths) {
        $(ths).children().each(function () {
            if($(this).attr("editEnable")) {
                if($(this).children().first().attr("type") == "select"){
                    var value = $(this).find("select option:selected").val();
                    for(var key in HOST_STATUS){
                        if(HOST_STATUS[key] == value){
                            $(this).attr("value",key);
                        }
                    }
                    $(this).html(value);
                }else{
                var html = $(this).find("input").val();
                $(this).html(html);
                }

            }
        });
    }
//  实现单行进入和退出编辑！
    $(function () {
        $('table').delegate('input[type="checkbox"]',"click",function () {
            if(EDIT_MODE){
                if($(this).prop("checked")){
                    rowInEditing($(this).parent().parent());
                }else{
                    rowOutEditing($(this).parent().parent());
                }
            }
        });
    });
//  增加主机条目
    $("#add").click(function () {
        var tr = $("table tbody tr").last().clone();
        tr.appendTo("table tbody");
        var number = $("tbody tr").length;
        var page_number = $("nav ul li").length;
        if(number > 10*(page_number-2)){
            $("nav ul li").last().removeClass("disabled");
            var page_th = Math.round(number/10)+1;
            tr.addClass("hide");
            $("nav ul li").eq(-1).before('<li><a href="#">'+page_th+'</a></li>');
        }
        showPage();
    });
    // 删除该行主机条目
    $(function () {
            $('table').delegate('span[class="glyphicon glyphicon-minus-sign"]',"click",function () {
                $(this).parent().parent().remove();
                var number = $("tbody tr").length;
                var page_number = $("nav ul li").length;
                jumpToPage($('nav ul li[class="active"]'));
                if(number == 10*(page_number-3) && number >=10){
                    if($("nav ul li").last().prev().hasClass("active")){
                        var page = $("nav ul li").last().prev().index();
                        page -= 1;
                        $("nav ul li").eq(page).addClass("active");
                        jumpToPage($("nav ul li").eq(page));
                    }
                    if($("nav ul li").last().prev().prev().hasClass("active")){
                        $("nav ul li").last().addClass("disabled");
                        if($("nav ul li").first().next().hasClass("active")){
                            $("nav ul li").first().addClass("disabled");
                        }
                    }
                    $("nav ul li").last().prev().remove();
                }
                showPage();
            });
        });
//  创建select元素
    function createSelect(value, source) {
        var html_start="<select type='select' style='width:100%;' onchange='multiChoose(this);'>";
        var temp = "";
        for(var key in window[source]){
            if(key == value){
                temp= temp + "<option " + "selected='selected'"+">" + window[source][key] + "</option>";
            }else{
                temp= temp + "<option>" + window[source][key] + "</option>";
            }
        }
        var html_end="</select>";
        var select = html_start + temp + html_end;
        return select;
    }
//  当按下CTRL键的时候实现多选
    function multiChoose(ths) {
        if(window.globalCtrlKeyStatus){
            var value = $(ths).val();
            var trs = $(ths).parent().parent().nextAll();
            trs.each(function () {
                if($(this).children().first().find("input").prop("checked")){
                    $(this).children().eq(3).find("select").val(value);
                }
            });
        }
    }
    // 点击页面选择按钮
    $(function(){
        $("nav ul").delegate("li:not(:first):not(:last)","click",function () {
            if($(this).find("a").text() == 1){
                $(this).prev().addClass("disabled");
                }else{
                     $(this).parent().children().first().removeClass("disabled");
                }
            if($("nav ul li").index(this) == ($("nav ul li").length -2)){
                $(this).parent().children().last().addClass("disabled");
            }else{
                $(this).parent().children().last().removeClass("disabled");

            }
            jumpToPage(this);
            showPage();
        });
    });

    // 向左移动页面的箭头
    $(function(){
        $("nav ul").delegate("li:first","click",function () {
            if($("nav ul li").length == 3){
                return false;
            }
            var current_tr = $('nav ul li[class="active"]');
            if($(current_tr).find("a").text() != "1"){
                var target_page = $(current_tr).prev();
                jumpToPage(target_page);
            }
            if($(target_page).find("a").text() == "1"){
                $(this).parent().children().first().addClass("disabled");
            }
            $(this).parent().children().last().removeClass("disabled");
            showPage();
        });
    });

// 向右移动页面的箭头
    $(function(){
        $("nav ul").delegate("li:last","click",function () {
            if($("nav ul li").length == 3){
                return false;
            }
            if($(this).hasClass("disabled")){
                return false;
            }
            var current_tr = $('nav ul li[class="active"]');
            var target_page = $(current_tr).next();
            jumpToPage(target_page);
            if($("nav ul li").index(current_tr) == ($("nav ul li").length -3)){
                $(this).parent().children().last().addClass("disabled");
            }else{
                $(this).parent().children().last().removeClass("disabled");
            }
            $(this).parent().children().first().removeClass("disabled");
            showPage();
        });
    });
    // 跳转到指定页面
    function jumpToPage(ths) {
        $(ths).addClass("active");
        $(ths).siblings().removeClass("active");
        var page_th = parseInt($(ths).find("a").text());
        var page_start = (page_th-1) * 10;
        var page_end = page_th *10 -1;
        var trs = $("tbody tr");
        trs.each(function () {
            if($(this).index()>= page_start && $(this).index()<= page_end){
                $(this).removeClass("hide");
            }else{
                $(this).addClass("hide");
            }
        });
        
    }
    // 显示页面信息
    function showPage(){
        var current_page =  $('nav ul li[class="active"]').find("a").text();
        var total_page = $("nav ul li").length -2;
        var total_number = $("tbody tr").length;
        var content = '第 ' + current_page + '/' + total_page + ' 页&nbsp;共 ' + total_number + ' 条记录';
        $("#counter span").html(content);
    }
