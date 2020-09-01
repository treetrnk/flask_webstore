function toggle_submit(action='') {
  var submit_btn = $('#submit-button')
  
  function disable() {
      submit_btn.removeAttr('disabled');
      submit_btn.removeClass('disabled');
  }

  function enable() {
      submit_btn.attr('disabled', 'disabled');
      submit_btn.addClass('disabled', 'disabled');
  }
  
  if (action == 'disable') {
    disable();
  } else if (action == 'enable') {
    enable();
  } else if (submit_btn.hasClass('disabled')) {
    enable();
  } else {
    disable();
  }

}

$(document).ready(function() {

  $('.payment-option-btn').click(function() {
    
    var $this = $(this);
    var target = $($this.data('target'));    

    $('.payment-option-btn').each(function() {
      $(this).removeClass('active');
    });
    $this.addClass('active');

    $('.payment-option-div').each(function() {
      $(this).slideUp();
      //$(this).hide();
    });
    //target.show();
    target.slideDown();

  });

  toggle_submit('disable');
  fetch("/cart/create-payment", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(purchases)
  })
  .then(function(result) {
    return result.json();
  })
  .then(function(data) {
    var elements = stripe.elements();

    var style = {
      base: {
        color: "#32325d",
        fontFamily: 'Arial, sans-serif',
        fontSmoothing: "antialiased",
        fontSize: "16px",
        "::placeholder": {
          color: "#32325d"
        }
      },
      invalid: {
        fontFamily: 'Arial, sans-serif',
        color: "#fa755a",
        iconColor: "#fa755a"
      }
    };

    var card = elements.create("card", {style, style});
    // Stripe injects an iframe into the DOM
    card.mount("#card-element");

    card.on("change", function (event) {
      // Disable the Pay button if there are no card details in the Element
      toggle_submit(event.empty ? 'disable' : 'enable');
      $('#card-error').text(event.error ? event.error.message : '');
    });

    var form = $('#payment-form');
    form.submit(function(event) {
      event.preventDefault();
      payWithCard(stripe, card, data.clientSecret);
    });
  });

  // Calls stripe.confirmCardPayment
  // If the card requires authentication Stripe shows a pop-up modal to
  // prompt the user to enter authentication details without leaving your page.
  var payWithCard = function(stripe, card, clientSecret) {
    loading(true);
    stripe
      .confirmCardPayment(clientSecret, {
        payment_method: {
          card: card
        }
      })
      .then(function(result) {
        if (result.error) {
          // Show error to your customer
          showError(result.error.message);
        } else {
          // The payment succeeded!
          orderComplete(result.paymentIntent.id);
        }
      });
  };

  /* ------- UI helpers ------- */

  // Shows a success message when the payment is complete
  var orderComplete = function(paymentIntentId) {
    loading(false);
    $('.result-message').text('Payment Successful!');
    toggle_submit('disable');
    $('#confirm-form input[name="payment_id"]').val(paymentIntentId);
    $('#confirm-form').submit();
  };

  // Show the customer the error from Stripe if their card fails to charge
  var showError = function(errorMsgText) {
    loading(false);
    var errorMsg = $('#card-error');
    errorMsg.textContent = errorMsgText;
    setTimeout(function() {
      errorMsg.textContent = '';
    }, 4000);
  };

  // Show a spinner on payment submission
  var loading = function(isLoading) {
    if (isLoading) {
      // Disable the button and show a spinner
      toggle_submit('disable');
      $('#spinner').removeClass('fa-spinner');
      $('#spinner').removeClass('fa-spin');
      $('#spinner').addClass('fa-check-circle');
      $('#button-text').addClass('hidden');
    } else {
      // Enable the button and show a button text
      toggle_submit('enable');
      $('#spinner').addClass('fa-spinner');
      $('#spinner').addClass('fa-spin');
      $('#spinner').removeClass('fa-check-circle');
      $('#spinner').addClass('hidden');
      $('#button-text').removeClass('hidden');
    }
  };
});
