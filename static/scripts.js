$(document).ready(function(){
    $('.fName').click(function(){
        window.location.href = Flask.url_for("search") + '/' + this.innerHTML;
    });
});