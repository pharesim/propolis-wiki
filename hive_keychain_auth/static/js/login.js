var btn = document.getElementById('loginBtn');

document.getElementById('login_form').addEventListener('submit', function(event) {
    event.preventDefault();
    if (!window.hive_keychain) {
        showKeychainError();
        return;
    }

    btn.style.display = 'none';
    document.getElementById('loginLoading').style.display = 'inline-block';
    
    const username = document.getElementById('username').value;
    if (username) {
        const signedMessageObj = { type: 'login', address: username, page: window.location.href };
        const messageObj = { signed_message: signedMessageObj, timestamp: parseInt(new Date().getTime() / 1000, 10) };
        const keychain = window.hive_keychain;
        keychain.requestSignBuffer(username, JSON.stringify(messageObj), "Posting", function(response) {
            if (response.success) {
                let redirect_url = document.getElementById('redirect_url').value;
                fetch('/verify-login', {
             
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(response),
                })
                .then(response => response.json())
                .then(data => {
                    window.location.replace('/'+redirect_url);
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showLoginButton();
                });
            } else {
                alert("Login failed");
                showLoginButton();
            }
        });
    } else {
        alert('Please provide a username');
        showLoginButton();
    }
});

function showLoginButton() {
    btn.style.display = 'inline-block';
    document.getElementById('loginLoading').style.display = 'none';
}

function showKeychainError() {
    var element = document.getElementById('keychainError');
    element.style.display = 'block';
    return;
}