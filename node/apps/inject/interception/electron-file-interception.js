const { protocol } = require('electron');

app.whenReady().then(() => {
    protocol.interceptFileProtocol('file', (request, callback) => {
        if (request.url.endsWith('some-module.js')) {
            callback({ path: '/path/to/your/custom-module.js' });
        } else {
            callback(request);
        }
    });
});
