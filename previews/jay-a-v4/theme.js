(function(){
  try{
    var params = new URLSearchParams(window.location.search);
    var theme = params.get('theme');
    if(theme === 'light') document.body.setAttribute('data-theme','light');
  }catch(e){}
})();
