$(function(){
  $(".socialMContainer ul li").fadeOut(100);
  $(".socialMContainer ul li").slideUp(500).delay(100).slideDown(500);
});
$(function(){

});

$(function(){
  $(".socialMContainer ul li").hover(function() {
    $(this).fadeOut(100);
    $(this).fadeIn(200);
  })
});

$(function(){
  $(".menuContainer ul li").on(
  {
      mouseenter: function()
      {
          $(this).animate({"left" : "+=10px"}, 500);
      },
      mouseleave: function()
      {
          $(this).animate({"left" : "-=10px"}, 500);
      }
  });
});
