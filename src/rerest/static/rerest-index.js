$(function() {
    $('.show-playbook-button').parent().hover(function() {
        $( this ).toggleClass( 'success' );
    });

    $('.show-playbook-button').parent().click(function() {
        var pbid = $( this ).attr('id');
        var show_icon = "#" + pbid + " span.show-playbook-button";

        if ( $(show_icon).hasClass('glyphicon-chevron-down') ) {
            // The code is not being displayed
            $(show_icon).removeClass('glyphicon-chevron-down');
            $(show_icon).addClass('glyphicon-chevron-up');
            show_code(pbid);
        } else {
            // The code is currently on display
            $(show_icon).removeClass('glyphicon-chevron-up');
            $(show_icon).addClass('glyphicon-chevron-down');
            hide_code(pbid);
        }
    });

});

function show_code(pbid) {
    // id of element with link to code URL
    var dl_id_json = "#" + pbid + "-download-json";
    var dl_id_yaml = "#" + pbid + "-download-yaml";
   // table row with the code box we're filling in it
    var code_display_row = $("#" + pbid + "-row");
    // get the target from the element with the code URL
    var dl_url_json = $( dl_id_json ).attr('href');
    var dl_url_yaml = $( dl_id_yaml ).attr('href');

    // load the code, then add a callback to slide-down the box
//    code_display_row.slideToggle();
    $("#" + pbid + "-code-json").load(dl_url_json, function() {
        $("#" + pbid + "-code-yaml").load(dl_url_yaml, function() {
            code_display_row.slideToggle();
        });
    });
}

function hide_code(pbid) {
    // id of the table row we need to hide
    var code_display_row = $("#" + pbid + "-row");
    code_display_row.slideToggle();
}
