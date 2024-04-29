const { Editor } = toastui;

const { colorSyntax, tableMergedCell, uml, reference  } = Editor.plugin;

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
    plugins: [latexPlugin, colorSyntax, tableMergedCell, uml],
    extendedAutolinks: true,
    hideModeSwitch: true,
});

var client = new dhive.Client(["https://api.hive.blog", "https://api.hivekings.com", "https://anyx.io", "https://api.openhive.network"]);

var btn = document.getElementById('submit');
function enableSubmit() {
    btn.disabled = true;
    if(title_input_error == 0 && topics_input_error == 0 && exists_error == 0) {
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

function patchBody(permlink,newBody,t) {
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
        broadcastEdit(result.title, new_body, permlink, t);
    });
}

function broadcastEdit(title,body,permlink,t) {
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
                json_metadata: "{\"tags\": "+t+",\"format\": \"markdown\",\"app\": \""+wiki_user+"/"+version_number+"\",\"appdata\": {\"user\": \""+username+"\"}}"
            }
        ]],
        'Posting',
        (response) => {
            console.log(body);
            console.log(response);
            if(response.success == true) {
                window.location.replace("/wiki/"+permlink);
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
    
    let body = editor.getMarkdown().replaceAll('](/wiki/','](/@'+wiki_user+'/').replaceAll('<a href="/wiki/','<a href="/@'+wiki_user+'/').replaceAll('<ref>|Reference: ','<ref>').replaceAll('<ref>','<ref>|Reference: ');
    if(where == 'edit') {
        body = patchBody(permlink, body, t);
    } else { 
        broadcastEdit(title, body, permlink, t);
    }
});

checkTopics();
checkTitle();