$(document).ready(function() {

  $('.product-square p').click(function() {

    $('.product-description').each(function() {
      $(this).removeClass('show');
    });

    /*
    $(this).removeClass('collapse');
    */
  
  });

});
