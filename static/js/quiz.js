$(function() {

    var changed = false;

    $('.question-input').change(function() {
        changed = true;
    });

    $('#save-button').click(function() {
        var data = $.base64.encode($('#form-quiz').serialize())
        console.log(data);

        $.post('save', data, function(data) {
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
        return '<div><a href="#" onclick="$(this).next().slideToggle(); return false;">Bekijk hint</a>'+$(this).hide()[0].outerHTML+'</div>';
    });
});