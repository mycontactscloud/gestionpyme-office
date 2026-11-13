// SPDX-License-Identifier: MPL-2.0
// Copyright Software GestiónPYME, 2026.
// Finish the editor's normal close action in a standalone browser window.
(function () {
    'use strict';
    if (window.top !== window || window.ThisIsAMobileApp) return;

    var closing = false;
    var attempts = 0;
    var timer;

    function attach() {
        var map = window.app && window.app.map;
        if (!map || typeof map.on !== 'function') return false;
        map.on('postMessage', function (event) {
            if (event.msgId !== 'UI_Close' || closing ||
                (map._disableDefaultAction && map._disableDefaultAction.UI_Close)) return;
            closing = true;
            // Let closeapp finish removing the document and closing its socket first.
            window.setTimeout(function () {
                window.close();
                window.setTimeout(function () {
                    // A tab opened manually may not be script-closable. Keep it useful.
                    var es = (document.documentElement.lang || navigator.language || 'en').toLowerCase().indexOf('es') === 0;
                    var main = document.createElement('main');
                    var title = document.createElement('h1');
                    title.textContent = brandProductName;
                    var message = document.createElement('p');
                    message.textContent = es
                        ? 'El documento se ha cerrado. Cierra esta pestaña y vuelve a la aplicación para guardar la ficha del documento.'
                        : 'The document has closed. Close this tab and return to the application to save the document record.';
                    main.appendChild(title);
                    main.appendChild(message);
                    document.body.replaceChildren(main);
                }, 200);
            }, 0);
        });
        return true;
    }

    if (!attach()) {
        timer = window.setInterval(function () {
            if (attach() || ++attempts >= 240) window.clearInterval(timer);
        }, 250);
    }
}());
