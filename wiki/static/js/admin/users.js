var add_user_submit_btn = document.getElementById('add_user_submit');
add_user_submit_btn.addEventListener('click', function() {
    if(confirm('Do you want to add the user with the set userlevel?')) {
        add_user_submit_btn.style.display = 'none';
        document.getElementById('add_user_submit_loading').style.display = 'inline-block';
        window.location.replace("/admin/user/add/"+document.getElementById('new_user_username').value+"/"+document.getElementById('new_user_userlevel').value);
    }
});

function deleteUser(username) {
    document.getElementById('delete_user_'+username).style.display = 'none';
    document.getElementById('delete_user_'+username+'_loading').style.display = 'inline-block';
    if(confirm('Do you want to delete the user?')) {
        window.location.replace("/admin/user/delete/"+username);
    }
}