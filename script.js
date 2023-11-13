function showPage(pageId){
    var allPages = document.querySelectorAll('.content');
    allPages.forEach(function(page){
        page.style.display='none';
    });

    var selectedPage = document.getElementById(pageId);
    if (selectedPage){
        selectedPage.style.display='block';
    }
}