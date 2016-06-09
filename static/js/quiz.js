$(function() {

    var changed = false;

    $('.question-input').change(function() {
        changed = true;
    });

    $('#save-button').click(function() {
        var data = $.base64.encode($('#form-quiz').serialize())

        $('#busy').show();
        $('#save-button').prop('disabled', true);

        $.post('save', data, function(data) {
            $('#busy').hide();
            $('#save-button').prop('disabled', false);

            if(data == 'ok') {
                $('#js-message').text('Antwoorden zijn opgeslagen').slideDown().delay(1000).slideUp();
                changed = false;
            } else {
                alert('Er is iets misgegaan bij het opslaan, bewaar je antwoorden lokaal voordat je deze tab afsluit');
            }

        });

        return false;
    });

    window.onbeforeunload = function() {
        if(changed) {
            return 'Er zijn niet opgeslagen wijzigingen. Weet je zeker dat je de pagina wilt verlaten?';
        }
    }

    // Hints
    $('.hint').replaceWith(function() {
        return '<div><a href="#" class="hintlink" onclick="$(this).next().slideToggle(); return false;">Bekijk hint</a>'+$(this).hide()[0].outerHTML+'</div>';
    });

    $('#difficulty').change(function(e) {
        var option = $(this).find(':selected').val();


        $('.hintlink').toggle(option == 'normal');
        $('.hint').toggle(option == 'easy');


        window.localStorage.setItem('difficulty', option);
    });

    // Set the selected property
    if(window.localStorage['difficulty']) {
        var difficulty = window.localStorage['difficulty'];
    } else {
        var difficulty = 'normal';
    }

    $('#difficulty option').filter(function() {
        return $(this).val() == difficulty;
    }).prop('selected', true);
    $('#difficulty').trigger('change');

});