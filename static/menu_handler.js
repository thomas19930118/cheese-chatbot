// Create the new menu item
window.parent.document.querySelector('#MainMenu').addEventListener('click', function(e) {
    if (e.target.innerText === 'Reload Cheese Data') {
        window.location.search = '?menu_reload_data=true';
    }
}); 