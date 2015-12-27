function get_data_from_row(tablerow) {

    var username = $(tablerow).find(':input.oldusername').val();
    var newusername = $(tablerow).find(':input.username').val();
    var useractive = $(tablerow).find(':input.useractive').is(':checked');

    var userroles = $(tablerow).find(':input.rolebox');
    var roles_tuples = [];

    $(tablerow).find(':input.rolebox').each(function (i, elem) {
        var tuple = [$(elem).is(':checked'), $(elem).val()];
        roles_tuples.push(tuple);
    });
    return {oldusername : username,
        newusername : newusername,
        useractive: useractive,
        roles: roles_tuples}
}

$(document).on('click', 'a.deleteuser', function() {
    var tablerow = $(this).closest('tr');
    var data = get_data_from_row(tablerow);
    $.post(globalusermanagementpath + '/deleteuser/' + data['oldusername'],
        {
            username: data['oldusername']
        }, function(msg) {
            if (msg['error'] != null) {
                alert(msg);
            } else {
                $(tablerow).remove();
            }
        });
});

$(document).on('click', 'a.abortuser', function() {
    event.preventDefault();
    var tablerow = $(this).closest('tr');
    $(tablerow).remove();
});

$(document).on('click', 'a.savenewuser', function () {
    event.preventDefault();
    var tablerow = $(this).closest('tr');
    var data = get_data_from_row(tablerow);

    $.post(globalusermanagementpath + '/adduser/' + data['oldusername'],
        {
            username: data['newusername'],
            useractive: data['useractive'],
            roles: JSON.stringify(data['roles'])
        },
        function (data, status) {
            if (data['error'] != null) {
                alert('Fehler');
            } else {
                $(tablerow).find('input').prop('disabled', 'true');

                $(tablerow).find('a.abortuser').remove();
                $(tablerow).find('a.savenewuser').replaceWith('Reload to alter new entry');
            }
        });


});

$(document).ready(function() {

    if ( typeof globalusermanagementpath === 'undefined') {
        console.warn('Global usermanagement path is not defined. This wont work')
    }


    $("a.editbutton").on('click', function() {
        event.preventDefault();
        var tablerow = $(this).closest('tr');
        if ($(this).html().indexOf('fa-pencil') >= 0) {
            $(this).html('<i class="fa fa-floppy-o"></i>');
            $(tablerow).find(':input').each(function (i, elem) {
                $(elem).attr('disabled', false);
            });
        } else {

            var data = get_data_from_row(tablerow);
            $.post(globalusermanagementpath + '/updateuser/' + data['oldusername'],
                {
                    username: data['newusername'],
                    useractive: data['useractive'],
                    roles: JSON.stringify(data['roles'])
                },
                function (data, status) {
                    if (data['error'] != null) {
                        alert('Fehler');
                    }
                });

            $(this).html('<i class="fa fa-pencil"></i>');
            $(tablerow).find(':input').each(function (i, elem) {
                $(elem).attr('disabled', true);
            });
        }
    });

    $("a.adduser").on('click', function() {
        event.preventDefault();
        var table = $(this).closest('table');
        var tablerow = $(this).closest('tr');

        var rolelist = $(table).find('ul:first');
        var cln_role = $(rolelist).clone(true);
        $(cln_role).find('input:checkbox').removeAttr('checked').removeAttr('disabled');

        var row = $('<tr>');
        row.append($('<td>').append($('<input>')
            .attr('type', 'hidden')
            .attr('class', 'oldusername')
            .attr('value', 'newuser'))
            .append($('<input>')
                .attr('type', 'text')
                .attr('class', 'username')
                .attr('placeholder', 'New username')))
            .append($('<td>').append(cln_role))
            .append($("<td>").append($('<input>')
                .attr('type', 'checkbox')
                .attr('class', 'useractive')
                .attr('checked', 'true')))
            .append($("<td>").append($('<a>')
                .attr('href', '#')
                .attr('class', 'savenewuser')
                .append($('<i>')
                    .attr('class', 'fa fa-check'))))
            .append($("<td>").append($('<a>')
                .attr('href', '#')
                .attr('class', 'abortuser')
                .append($('<i>')
                    .attr('class', 'fa fa-times'))));

        $(tablerow).before(row);
    });
});