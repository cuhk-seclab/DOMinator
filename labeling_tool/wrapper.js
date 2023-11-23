// alert('In Wrapper');

function loadScript(scriptName, callback) {
    var scriptEl = document.createElement('script');
    scriptEl.setAttribute('id', scriptName);
    scriptEl.src = chrome.extension.getURL(scriptName);
    scriptEl.addEventListener('load', callback, false);
    document.head.appendChild(scriptEl);
};

function removeScript(scriptName) {
    var scr = document.getElementById('allinone.js')
    document.head.removeChild(scr);
}

var scr = document.getElementById('allinone.js');
if (scr) {
    // already script is loaded ...
    removeScript('allinone.js');
    loadScript('allinone.js', null);
} else {
    loadScript('allinone.js', null);
}
