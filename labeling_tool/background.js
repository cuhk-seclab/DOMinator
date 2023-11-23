// Called when the user clicks on the browser action.
chrome.browserAction.onClicked.addListener(function (tab) {
    // chrome.tabs.executeScript({code: 'alert(chrome.extension.getURL("allinone.js"));'} );
    chrome.tabs.executeScript({code: 'var divEl1 = document.getElementById("extensionpath");\n' +
            'if( divEl1 ) {\n' +
            '    document.head.removeChild(divEl1);\n' +
            '}'} );
    chrome.tabs.executeScript( { code: 'var divEl = document.createElement(\'div\');\n' +
            'divEl.setAttribute(\'id\', \'extensionpath\');\n' +
            'var basePath = chrome.extension.getURL(\'allinone.js\');\n' +
            'basePath = basePath.slice(0, - "allinone.js".length );\n' +
            'divEl.setAttribute(\'path\', basePath);\n' +
            'document.head.appendChild(divEl);' });
    chrome.tabs.executeScript( { file: 'wrapper.js' } );
});