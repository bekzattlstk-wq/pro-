// Общие мелкие помощники интерфейса PRO Монтаж.
(function () {
    'use strict';

    // Автоматически скрываем всплывающие сообщения через 6 секунд
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-autohide]').forEach(function (el) {
            setTimeout(function () { el.remove(); }, 6000);
        });
    });
})();
