function chev() {
    $('.show-playbook-button').parent().hover(function() {
        $( this ).toggleClass( 'success' );
    });

   $('.show-playbook-button').parent().click(function() {
        var pbid = $( this ).attr('id');
        var show_icon = '#' + pbid + ' span.show-playbook-button';

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

};

function hide_code(pbid) {
    // id of the table row we need to hide
    var code_display_row = $('#' + pbid + '-row');
    code_display_row.slideToggle();
}
