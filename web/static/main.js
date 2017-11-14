function checkDup(){
    var db_name = $("#name").val();
    if(!db_name){$("#dbcreatebutton").prop('disabled', true); return;};
    $.getJSON( "check/"+db_name,function(){

    }).done(function(data) {
        if(data.dbexist===true){
            $("#dbcreatebutton").prop('disabled', true);
            $("#duplabel").removeClass('invisible');
        }else{
            $("#dbcreatebutton").prop('disabled', false);
            $("#duplabel").addClass('invisible');
        }
    });
    
}

$(function() {
    var timer;
    $("#name").on('keyup',function() {
        timer && clearTimeout(timer);
        timer = setTimeout(checkDup, 300);
    });
});
