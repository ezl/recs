function animate_button_form(toggle_sel, cancel_sel, form_sel ){
    $(toggle_sel +','+cancel_sel).click(function(e) {
        e.preventDefault();
        $(toggle_sel+':visible').parent().animate(
          { opacity:'toggle' },
          { 
            duration: 150,
            easing: 'linear',
            complete: function(){
              $(form_sel).animate(
                {
                  height: 'toggle'
                },
                {
                  duration: 200,
                  easing:'linear'
                }
              );
            }
          });
        $(form_sel+':visible').animate(
            {
              height: 'toggle'
            },
            {
              duration: 100,
              easing: 'linear',
              complete: function(){
                $(toggle_sel).parent().animate(
                  {
                    opacity: 'toggle'
                  },
                  {
                    duration: 200,
                    easing: 'linear'
                  });
                }
            });
    });
}