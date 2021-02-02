let proxy = "None";
let proxyIp = "None";

let settingsApplied = false;
let settings = {}

chrome.webRequest.onBeforeRequest.addListener(function(details) {

    if (settingsApplied)
        return {
            cancel: true
        };
    settingsApplied = true;
    var segs = details.url.split('/');
    var data = segs.pop();

    settings = JSON.parse(atob(data));

    console.log(settings);

    if (settings.proxy) {
        proxy = settings.proxy;
        setupProxy(proxy);
    }

    if (settings.other) {
        return;
    }

    if (settings.url) {
        return {
            redirectUrl: settings.url
        };
    }

    return {
        cancel: true
    };
}, {
    urls: ["*://configure.bnb/*"]
}, ["blocking"]);

function setupProxy(proxy) {
    var segs = proxy.split(':');

    if (segs.length != 2 && segs.length != 4) {
        console.log("Invalid proxy...");
        return;
    }

    proxyIp = segs[0];

    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                host: segs[0],
                port: parseInt(segs[1])
            }
        }
    };

    chrome.proxy.settings.set({
            value: config,
            scope: 'regular'
        },
        function() {});

    if (segs.length == 2)
        return;

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {
            return {
                authCredentials: {
                    username: segs[2],
                    password: segs[3]
                }
            };
        }, {
            urls: ["<all_urls>"]
        }, ['blocking']
    );
};

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if (request.getSetting && request.getSetting == "proxy") {
            sendResponse({
                proxy: proxyIp
            });
        }
        sendResponse(null);
    }
);