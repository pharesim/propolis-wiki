const version_number = '0.3.1';

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

function latexPlugin() {
    const toHTMLRenderers = {
        latex(node) {
            const generator = new latexjs.HtmlGenerator({ hyphenate: false });
            var body = latexjs.parse(node.literal, { generator: generator }).domFragment();

            // remove annotations and .katex-html
            const remove = body.querySelectorAll("annotation, .katex-html");
            remove.forEach(function(element){
                element.parentNode.removeChild(element);
            });
            var div = document.createElement('div');
            div.appendChild(body.cloneNode(true));
            body = div.innerHTML;
            
            return [
                { type: 'openTag', tagName: 'div', outerNewLine: true },
                { type: 'html', content: body },
                { type: 'closeTag', tagName: 'div', outerNewLine: true }
            ];
        },
    }

    return { toHTMLRenderers }
}

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
