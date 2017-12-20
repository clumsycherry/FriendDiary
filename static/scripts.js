$(document).ready(function(){
    $('.fName').click(function(){
        window.location.href = Flask.url_for("search") + '/' + this.innerHTML;
    });

    function formSubmitter(formTag, messageTag){
        document.getElementById(messageTag).innerHTML = "Entering new information...";
    }
});