// Powered by BNB
let bnbNotification = document.createElement("div");
bnbNotification.id = "bnb-ext-notification";
bnbNotification.innerHTML = `
<table style="border-collapse: collapse; border: none;">
<p><span class='strong'>Using Proxy : </span> <span id='bnb-current-proxy'>unknown</span></p>
<br><p><span class='strong'>External IP   : </span> <span id='bnb-current-ip'>checking...</span></p>
`;
document.body.appendChild(bnbNotification);

chrome.runtime.sendMessage({
    getSetting: "proxy"
}, function(response) {
    if (response.proxy) {
        document.getElementById('bnb-current-proxy').innerText = response.proxy;
    }
});


// Get IP Address
var request = new XMLHttpRequest();
request.onreadystatechange = function() {
    if (request.readyState === 4 && request.status === 200) {
        document.getElementById('bnb-current-ip').innerText  = request.responseText;
    }
};
request.open("GET", "https://api.ipify.org/", true);
request.send(null);