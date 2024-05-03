function applyListeners(permlink) {
    let header = document.getElementById("header_"+permlink);
    let body = document.getElementById("body_"+permlink);
    let collapse = document.getElementById("collapse_"+permlink);
    let reply = document.getElementById("reply_"+permlink);
    let reply_collapse = document.getElementById("reply_collapse_"+permlink);
    let link = document.getElementById("reply_link_"+permlink);
    let short = document.getElementById("short_"+permlink);
    let send = document.getElementById("reply_send_"+permlink);

    body.style.display = "none";      
    collapse.style.display = "none";
    reply.style.display = "none";

    header.addEventListener('click',function(){
        body.style.display = "block";
        collapse.style.display = "block";
        short.style.display = "none";
    });

    collapse.addEventListener('click',function(){
        body.style.display = "none";
        short.style.display = "block";
        collapse.style.display = "none";
    });

    link.addEventListener('click', function(e){
        reply.style.display = 'block';
        link.style.display = 'none';
        e.preventDefault();
    });

    reply_collapse.addEventListener('click', function(){
        reply.style.display = 'none';
        link.style.display = 'block';
    });

    send.addEventListener('click', function(){
        alert('send the reply');
    });
}