const { colorSyntax, tableMergedCell, uml  } = toastui.Editor.plugin;

var viewer = {}
function createViewer(element) {
    viewer[element] = toastui.Editor.factory({
        el: document.getElementById(element),
        initialValue: document.getElementById(element).innerHTML,
        viewer: true,
        plugins: [latexPlugin, tableMergedCell, uml],
        extendedAutolinks: true
    });
}

function reverseChildren(parent) {
    for (var i = 1; i < parent.childNodes.length; i++){
        parent.insertBefore(parent.childNodes[i], parent.firstChild);
    }
}

function applyListeners(permlink) {
    let header = document.getElementById("header_"+permlink);
    let body = document.getElementById("body_"+permlink);
    let collapse = document.getElementById("collapse_"+permlink);
    let reply = document.getElementById("reply_"+permlink);
    let reply_collapse = document.getElementById("reply_collapse_"+permlink);
    let reply_link = document.getElementById("reply_link_"+permlink);
    let short = document.getElementById("short_"+permlink);
    let send = document.getElementById("reply_send_"+permlink);

    body.style.display = "none";      
    collapse.style.display = "none";
    reply.style.display = "none";

    header.addEventListener('click',function(){
        body.style.display = "block";
        collapse.style.display = "inline-block";
        short.style.display = "none";
    });

    collapse.addEventListener('click',function(e){
        body.style.display = "none";
        short.style.display = "block";
        collapse.style.display = "none";
        e.preventDefault();
    });

    reply_link.addEventListener('click', function(e){
        reply.style.display = 'inline-block';
        reply_link.style.display = 'none';
        e.preventDefault();
    });

    reply_collapse.addEventListener('click', function(){
        reply.style.display = 'none';
        reply_link.style.display = 'inline-block';
    });

    send.addEventListener('click', function(){
        alert('send the reply');
    });
}