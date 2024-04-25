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
    hideModeSwitch: false,
});

var btn = document.getElementById('submit');
function enableSubmit() {
    btn.disabled = true;
    if(title_input_error == 0 && topics_input_error == 0 && exists_error == 0) {
        btn.disabled = false;
    }
    console.log(title_input_error);
    console.log(topics_input_error);
    console.log(exists_error);
    console.log(btn.disabled);
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
        var client = new dhive.Client(["https://api.hive.blog", "https://api.hivekings.com", "https://anyx.io", "https://api.openhive.network"]);
    
        client.database.call('get_content', [wiki_user, permlink]).then(result => {
            document.getElementById("title_exists_warning").style.display = 'block';
            document.getElementById("existing_article").innerHTML = '<a href="/wiki/'+result.title+'">/wiki/'+result.title+'</a>';
            exists_error = 1;
            enableSubmit();
        });
    }

    enableSubmit();
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
    topics.unshift('Wiki')
    var permlink = title.replace(/\W+/g, '-').toLowerCase().replace(/-+$/,'');

    const keychain = window.hive_keychain;
    var t = "[";
    topics.forEach(function(topic) {
        t += "\""+topic.toLowerCase()+"\",";
    });
    t = t.replace(/,+$/,'');
    t += "]";
    keychain.requestBroadcast(
        wiki_user,
        [[
            'comment',
            {
                author: wiki_user,
                title: title,
                body: editor.getMarkdown(),
                parent_author: '',
                parent_permlink: 'wiki',
                permlink: permlink,
                json_metadata: "{\"tags\": "+t+",\"format\": \"markdown\",\"app\": \"test239119/0.1\",\"appdata\": {\"user\": \""+username+"\"}}"
            }
        ]],
        'Posting',
        (response) => {
            console.log(response);
            if(response.success == true) {
                window.location.replace("/wiki/"+permlink);
            } else {
                btn.style.display = 'block';
                document.getElementById("loading").style.display = 'none';
            }
        }
    );
});

checkTopics();
checkTitle();