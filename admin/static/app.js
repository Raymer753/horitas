/* Horitas Admin — Client-side interactivity */

document.addEventListener('DOMContentLoaded', function () {

    // Confirm delete for audio files
    document.querySelectorAll('.confirm-delete').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            var name = this.getAttribute('data-name');
            if (!confirm('¿Eliminar "' + name + '"?')) {
                e.preventDefault();
            }
        });
    });

});

// Delete a phrase (called from phrases page)
function deletePhrase(hourKey) {
    if (confirm('¿Eliminar la frase para la hora ' + hourKey + '?')) {
        document.getElementById('delete-hour-key').value = hourKey;
        document.getElementById('delete-form').submit();
    }
}
