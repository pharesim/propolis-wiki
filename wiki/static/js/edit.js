const { Editor } = toastui;

const { tableMergedCell, uml, reference, wikiLink  } = Editor.plugin;

const editor = new Editor({
    el: document.getElementById('editor'),
    previewStyle: 'vertical', // tab, vertical
    height: '500px',
    toolbarItems: [
        ['heading', 'bold', 'italic', 'strike'],
        ['hr', 'quote'],
        ['ul', 'ol', 'indent', 'outdent'],
        ['table', 'image', 'link'],
        ['code', 'codeblock'],],
    initialValue: document.getElementById('editor').innerHTML,
    initialEditType: 'markdown', // wysiwyg
    plugins: [latexPlugin, tableMergedCell, uml, wikiLink],
    extendedAutolinks: true,
    hideModeSwitch: true,
    usageStatistics: false
});

var client = new dhive.Client(["https://api.hive.blog", "https://api.deathwing.me", "https://anyx.io", "https://api.openhive.network"]);

var btn = document.getElementById('submit');
function enableSubmit() {
    btn.disabled = true;
    if(title_input_error == 0 && topics_input_error == 0 && reason_input_error == 0 && exists_error == 0) {
        btn.disabled = false;
    }
}

// validate topics
var topics_input_error = 0;
var topics_input = document.getElementById('topics');
var topics_space_warning = document.getElementById('topics_space_warning');
function checkTopics() {
    let value = topics_input.value;
    if([',',';'].some(v => value.includes(v))) {
        topics_space_warning.style.display = 'block';
        topics_input_error = 1;
    } else {
        topics_space_warning.style.display = 'none';
        topics_input_error = 0;
    }
    enableSubmit();
}
topics_input.onkeyup = function() { checkTopics() };

// validate title
var title_input_error = 0;
var title_input = document.getElementById('title');
var title_empty_warning = document.getElementById('title_empty_warning');   
function checkTitle() {
    let value = title_input.value.trim();
    if(value == '') {
        title_empty_warning.style.display = 'block';
        title_input_error = 1;
    } else {
        title_empty_warning.style.display = 'none';
        title_input_error = 0;
    }
    let permlink = value.replace(/\W+/g, '-').toLowerCase().replace(/-+$/,'');
    checkExists(permlink); 
}
title_input.onkeyup = function() { checkTitle(); }; 

// validate reason input
var reason_input_error = 0;
if(where == 'edit') {
    var reason_input = document.getElementById('reason');
    var reason_empty_warning = document.getElementById('reason_empty_warning');
    function checkReason() {
        let value = reason_input.value.trim();
        if(value == '') {
            reason_empty_warning.style.display = 'block';
            reason_input_error = 1;
        } else {
            reason_empty_warning.style.display = 'none';
            reason_input_error = 0;
        }
        enableSubmit();
    }
    checkReason();
    reason_input.onkeyup = function() { checkReason(); };
}

// check if article exists
var exists_error = 0;
function checkExists(permlink) {
    exists_error = 0;
    document.getElementById("title_exists_warning").style.display = 'none';
    if(where == 'create') {
        client.database.call('get_content', [wiki_user, permlink]).then(result => {
            document.getElementById("title_exists_warning").style.display = 'block';
            document.getElementById("existing_article").innerHTML = '<a href="/wiki/'+result.title+'">/wiki/'+result.title+'</a>';
            exists_error = 1;
            enableSubmit();
        });
    }

    enableSubmit();
}

function patchBody(permlink,newBody,title,topics,reason) {
    client.database.call('get_content', [wiki_user, permlink]).then(result => {
        var dmp = new diff_match_patch();
        var diff = dmp.diff_main(result.body, newBody);
        dmp.diff_cleanupSemantic(diff);
        patch = dmp.patch_make(result.body, diff);
        patch_body = dmp.patch_toText(patch);
        if (patch_body.length < result.body.length) { 
            new_body = patch_body;
        } else {
            new_body = newBody;
        }

        broadcastEdit(title, new_body, permlink, topics, reason);
    });
}

function broadcastEdit(title,body,permlink,topics,reason) {
    const keychain = window.hive_keychain;
    keychain.requestBroadcast(
        wiki_user,
        [[
            'comment',
            {
                author: wiki_user,
                title: title,
                body: body,
                parent_author: '',
                parent_permlink: 'wiki',
                permlink: permlink,
                json_metadata: "{\"tags\": "+topics+",\"format\": \"markdown+html\",\"app\": \""+wiki_user+"/"+version_number+"\",\"appdata\": {\"user\": \""+username+"\", \"reason\": \""+reason+"\"}}"
            }
        ]],
        'Posting',
        (response) => {
            if(response.success == true) {
                alert("Edit successful, waiting for blockchain sync. If your changes aren't visible right away, try reloading the page after a few seconds.");
                setTimeout(() => { window.location.replace("/wiki/"+permlink) }, 2000);
            } else {
                btn.style.display = 'block';
                document.getElementById("loading").style.display = 'none';
            }
        }
    );
}

btn.addEventListener('click', function() {
    btn.style.display = 'none';
    document.getElementById("loading").style.display = 'block';
    
    if(!confirm('Do you want to save the article to the blockchain?')) {
        btn.style.display = 'block';
        document.getElementById("loading").style.display = 'none';
        return false;
    }
    var title = title_input.value.trim();
    var topics = topics_input.value.trim().split(' ');
    if(!topics.includes('wiki')) {
        topics.unshift('wiki');
    }
    var permlink = title.replace(/\W+/g, '-').toLowerCase().replace(/-+$/,'');

    
    var t = "[";
    topics.forEach(function(topic) {
        t += "\""+topic.toLowerCase()+"\",";
    });
    t = t.replace(/,+$/,'');
    t += "]";
    topics = t;

    let reason = 'Initial post';

    const extractCodeBlocks = (body) => {
        const codeBlocks = [...body.matchAll(/```([^`]+)```/g)];

        body = body.replaceAll(/```([^`]+)```/g, '``````');
        return [body,codeBlocks];
    }

    const restoreCodeBlocks = (body, codeBlocks) => {
        for (const codeBlock of codeBlocks) {
            body = body.replace('``````', codeBlock[0]);
        }
        return body;
    }

    const capitalizeFirstLetter = (string) => {
        return string.charAt(0).toUpperCase() + string.slice(1)
    }

    const replaceInternalLinks = (body) => {
        body = body.replaceAll('](/wiki/','](/@'+wiki_user+'/').replaceAll('<a href="/wiki/','<a href="/@'+wiki_user+'/').replaceAll('<ref>|Reference: ','<ref>').replaceAll('<ref>','<ref>|Reference: ');
        body = body.replaceAll(/\[\[([^\]]+)\]\]/g, (match, p1, offset, string, groups) => {
            let link = p1;
            const hasFragment = link.includes('|')
            const linkFragment = hasFragment ? '#' + link.split('|')[1].replaceAll(' ','') : ''
            if (hasFragment) {
                link = link.split('|')[0]
            }
            return `[${link}](/@${wiki_user}/${link.split(' ').map(capitalizeFirstLetter).join('-')}${linkFragment})`
        })

        return body
    }

    // prepare post for display on all Hive front-ends
    let body,codeBlocks;

    // remove code blocks from body first, they should not be modified
    [body,codeBlocks] = extractCodeBlocks(editor.getMarkdown());

    body = replaceInternalLinks(body);

    // restore the unmodified code blocks
    body = restoreCodeBlocks(body, codeBlocks);

    if(where == 'edit') {
        let reason = document.getElementById('reason').value;
        body = patchBody(permlink, body, title, topics, reason);
    } else { 
        broadcastEdit(title, body, permlink, topics, reason);
    }
});

checkTopics();
checkTitle();