const version_number = '0.5.11';

// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function () {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeline', 'timelineEnd', 'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());

function formatPostLink(permlink) {
    split = permlink.split("-")
    if(split.length > 1) {
        permlink = '';
        for (let i = 0; i < split.length; i++) {
            permlink += formatPostLinkSegment(split[i]);
            if(i+1 < split.length) {
                permlink += '-';
            }
        }
    } else {
        permlink = formatPostLinkSegment(permlink);
    }
    return permlink;
}

function formatPostLinkSegment(val) {
    let keeplow = ['Disambiguation','disambiguation'];
    if(val[1] == val[0].toLowerCase()) {
        if(!keeplow.includes(val)) {
            return val[0].toUpperCase()+val.substring(1,-1);
        }
    } else {
        if(keeplow.includes(val)) {
            return val[0].lower()+val.substring(1,-1);
        }
    }
    return val;
}

document.getElementById('submitSearch').addEventListener('click', function(){
    search = encodeURIComponent(document.getElementById('searchInput').value);
    window.location.replace("/search/"+search);
});

document.getElementById('searchInput').addEventListener('keyup', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('submitSearch').click();
    }
});
