// Do this before you initialize any of your modals
// Prevents modals from autofocusing to allow select2s to work
$.fn.modal.Constructor.prototype.enforceFocus = function() {};

function updateTotal() {
	var labelTotal = 0;
	$(".labelNum").each(function() {
		labelTotal += Number($(this).val());
	});
	var pageTotal = Math.round(labelTotal / 30 * 100) / 100;
	$('#total').text(pageTotal + ' page(s)');
}

function updateTotalTo() {
	var labelTotal = 0;
	var arrayOfLines = $('#counts').val().split('\n');
	$.each(arrayOfLines, function(index, item) {
		labelTotal += Number(item);
	});
	var pageTotal = Math.round(labelTotal / 30 * 100) / 100;
	$('#total').text(pageTotal + ' page(s)');
}

function addLabel(e) {
	if (e.val() == '') {
		return false;
	}
	var currentNumber = Number($('#lastLabel').val()) + 1;
	$('#lastLabel').val(currentNumber);
	$('#labelCount').val( Number($('#labelCount').val()) + 1 );
	var newLabel = '<tr>' +
			'<td>' + e.text().replace(/ *\([^)]*\) */g, '') + '</td>' +
			'<td>' + e.val() + '</td>' +
			'<td>' + e.data('bag') + '</td>' +
			'<td><input name="labelAmount' + currentNumber + '" type="number" class="form-control labelNum" value="' + $('#addAmount').val() + '" min="5" step="5" /></td>' +
			'<td class="text-center">' + 
				'<input name="labelId' + currentNumber + '" type="hidden" value="' + e.data('id') + '" />' +
				'<button type="button" class="btn btn-danger removeLabel"><i class="fa fa-times"></i></button>' +
			'</td>' +
		'</tr>';
			
	$('#labelList').append(newLabel);
	updateTotal();
}

function removeLabel(e) {
	$('#labelCount').val( Number($('#labelCount').val()) - 1 );
	e.parent().parent().fadeOut();
	setTimeout(function() {
		e.parent().parent().remove();
	}, 1000);
}

function start_loader() {
	$('.shade').show();
	$('.loader').show();
	$('.ebsloader').show();
}

$(function () {
  $('.jquery-popover').popover();
});

$(document).on('ready', '.jquery-popover', function() { $(this).popover({
  container: 'body',
}); });

$(document).on('click', '.removeLabel', function() {
	removeLabel($(this));
});

$(document).on('ready', '.mkSelect2', function() { $(this).select2(); });

$('body').on('submit', 'form', function() {
	$this = $(this);
	$('<input />').attr('type', 'hidden').attr('name', 'config-hidden').attr('value', oldConfig).appendTo($this);
	return true;
});

$(document).on('click', '.pin-btn', function(e) {
  e.stopPropagation();
  e.preventDefault();
  var $this = $(this);
  var commentID = $this.data('id');
  var action = $this.data('action');
  var dest = $this.data('url');
  var icon = $this.find('i.fa-thumbtack');
  var bubble = $this.parent('small').parent('span.bubble');

  $.ajax({
    url: dest,
    type: 'POST',
    dataType: 'html',
    data: {'obj_id': commentID},
    success: function(data, status) {
      if (action == 'pin') {
        icon.removeClass('text-light').addClass('text-primary');
        bubble.addClass('bubble-selected');
      } else {
        icon.removeClass('text-primary').addClass('text-light');
        bubble.removeClass('bubble-selected');
      }
      scan();
    },
    error: function(xhr, desc, err) {
      console.log(xhr);
      var cleanResponse = $(xhr.responseText);
      console.log("Details: " + desc + "\nError: " + err);
      $this.attr('title','Error! Something went wrong! &#129302; Message: ' + err + ' (' + xhr.status + ' - ' + cleanResponse);
    }
  });
});

$(document).click(function() {
  $('.jquery-tooltip').tooltip('hide');
});

function makeSwitches() {
	var switches = $('input[data-type="switch"]')
	//switches.parent('div').addClass('custom-switch').addClass('custom-control');
	switches.removeClass('form-control').addClass('form-check-input');	
	switches.wrap("<div class='form-check'></div>");
	switches.parent('div').parent('div').siblings('label').addClass('pt-0');
	//switches.wrap("<div class='custom-control custom-switch'></div>");
}

function activateSelect2() {
	$('.mkSelect2').select2();
	$('select[data-type="select2"]').select2();
	/*$('body').on('DOMNodeInserted', 'select[data-type="select2"]', function () {
		    $(this).select2();
	});*/
	$('select[data-type="select2-tags"]').select2({
		tags: true
	});

	$('.mkSelect2wTags').select2({
		tags: true
	});
}

//$('.select2modal').on('shown.bs.modal', function() {
//  activateSelect2();
//});

$(document).ready(function() {

  activateSelect2();
	makeSwitches();

	$('[data-toggle="popover"]').popover()

	$('[data-toggle="popover"]').click(function(e) {
		e.stopPropagation();
		e.preventDefault();
	});
	
	$('#labelCount').val(0);
	$('#lastLabel').val(0);

	$('#productSelect').select2();
	$('#bagSelect').select2();
	$('#itemSelect').select2();
	$('.select2-tags').select2({
		tags: true,
	});

	$('body').on('submit', 'form', function() {
		var form = $(this);
    var $this = form.find("button[type='submit']");
		var icon = $this.find('i.fas');
		var classes = icon.attr('class');
		console.log(classes);
		$this.attr('disabled', true);
		icon.attr('class', 'fas fa-spinner fa-pulse')
    var form = $this.parent('form');
		setTimeout(function() {
			$this.attr('disabled', false);
			icon.attr('class', classes)
		}, 5000);
	});

	$(document).on('click', '.loadMe', function(e) {
		console.log('LOAD ME');
		e.stopPropigation;
		start_loader();
	});

	$('#counts').on('change keyup', updateTotalTo);

	$('.datatable').DataTable({
		"lengthMenu": [[-1, 10, 25, 50, 100], ["All", 10, 25, 50, 100]]
	});
	
	$('.datatable10-sort-2d').DataTable({
		"lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
		"order": [[2, "desc"]],
	});
	
	$('.datatable10-sort-3d').DataTable({
		"lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
		"order": [[3, "desc"]],
	});
	
	$('.datatable10').DataTable({
		"lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]]
	});
	
	$('#editOrderTable').DataTable({
		"lengthMenu": [[-1, 10, 25, 50, 100], ["All", 10, 25, 50, 100]],
		"colReorder": true
	});
	
	$('.datatable-sort1').DataTable({
		"lengthMenu": [[-1, 10, 25, 50, 100], ["All", 10, 25, 50, 100]],
		"order": [[1, "desc"]],
	});

	$('.datatable-sort0').DataTable({
		"lengthMenu": [[-1, 10, 25, 50, 100], ["All", 10, 25, 50, 100]],
	});

	$('.pay-period-sel').change(function(){
		if ($('#periodStart').val()) {
			var start = $('#periodStart').val();
			var path = $('#periodStart').data('path');
			var end = $('#periodEnd').val();

			window.location = path + '/' + start + '/' + end;
		}
	});

	$('.fieldlist-add').click(function() {
		console.log('add');
		var $this = $(this);
		var fieldlist = $this.parent().parent().prev('.fieldlist');
		var lastcard = fieldlist.find('.fieldlist-card:last');
		console.log(lastcard);
		//var id = lastcard.find('').find('').split('-');
		var newcard = lastcard.slideDown().clone()
		newcard.find("span.select2.select2-container").remove();
		var new_id_num = 1;
		newcard.find("input, select, textarea").each(function() {
			var id = $(this).attr('id');
			var id_list = id.split('-');
			console.log(id_list);
			var orig_id_num = id_list[1];
			id_list[1] = new_id_num;
			var new_id = id_list.join('-');
			console.log(new_id);
			while (($('#' + new_id).length)) {
				new_id_num += 1;
				id_list[1] = new_id_num;
				new_id = id_list.join('-');
				console.log(new_id);
			}
			$(this).attr('name', new_id);
			$(this).attr('id', new_id);
			$(this).removeAttr('data-select2-id');
			$(this).removeAttr('tabindex');
			$(this).removeClass('select2-hidden-accessible');
			$(this).parent().prev('label').attr('for',new_id);
			$(this).prev('label').attr('for', new_id);
		});
		newcard.appendTo(fieldlist);
		// var newcard = fieldlist.find('.fieldlist-card:last');
		newcard.hide().slideDown();
		$('select[data-type="select2"]').select2();

		if (fieldlist.find('.fieldlist-card').length > 0) {
			$('.fieldlist-remove').show();
		}
	});

	$(document).on('click', '.fieldlist-remove', function() {
		var $this = $(this);
		var fieldlist = $this.parent().parent().parent('.fieldlist');
		var card = $this.parent().parent('.fieldlist-card');
		card.slideUp('slow');
    var id = card.find('.child-id').val();
    console.log('ID: ' + id);
    var deleted_fieldlist_ids = $('#deleted_fieldlist_ids');
    console.log(deleted_fieldlist_ids);
    deleted_fieldlist_ids.val( deleted_fieldlist_ids.val() + id + ',');
    card.remove(); 

		console.log(fieldlist.find('.fieldlist-card').length);
		if (fieldlist.find('.fieldlist-card').length < 3) {
			$('.fieldlist-remove').hide();
		} else {
			$('.fieldlist-remove').show();
		}
	});

	$('#sparkle').sparkle({
		color: 'rainbow',
		direction: "both",
		count: 50,
		overlap: 15,
		minSize: 5,
		maxSize: 10
	});

	$('#pdfgen').sparkle({
		color: 'rainbow',
		direction: "both",
		count: 50,
		overlap: 15,
		minSize: 5,
		maxSize: 10
	});

	$(".foreversparkle").sparkle({
		color: 'rainbow',
		direction: "both",
		count: 250,
		overlap: 15,
		minSize: 5,
		maxSize: 10
	});

	$(".foreversparkle")
		.off("mouseover.sparkle")
		.off("mouseout.sparkle")
		.off("focus.sparkle")
		.off("blur.sparkle");
	$(".foreversparkle").trigger("start.sparkle");

	$('select#avatar').change(function() {
		var avatar = $(this).val();
		$('h4#avatarViewer').html(avatar);
	});

	$(document).on('click', '.delete-btn', function() {
		var thisID = $(this).data('id');
		$('#confirmDelete').data('id', thisID);
		$('#deleteModal').modal('toggle');
	});

	$('#confirmDelete').click(function() {
		var thisID = $(this).data('id');
    console.log(thisID);
		$('#delete' + thisID).submit();
	});

	$(document).on('change', '.labelNum', function() {
		updateTotal();
	});

	$(".mkMomentDate").each(function() {
		var $this = $(this);
		$this.val( moment($this.data("moment") + 'Z').format('YYYY-MM-DD') );
	});

	$(".mkMomentTime").each(function() {
		var $this = $(this);
		$this.val( moment($this.data("moment") + 'Z').format('HH:mm') );
	});

	$(".mkMomentTimezone").each(function() {
		var $this = $(this);
		$this.val( moment.tz.guess() );
	});

	$('#addProduct').click(function() {
		addLabel($('#productSelect option:selected'));
	});	

	$("#punchReportSelect").change(function() {
		date = $(this).val();
		window.location.href = "/reports/punch/" + date;
	});

	$("#userWeekSelect").change(function() {
		date = $(this).val();
		user = $(this).data('user');
		window.location.href = "/" + user + "/punch/" + date;
	});

	$("#payWeekSelect").change(function() {
		date = $(this).val();
		window.location.href = "/punch/reports/" + date;
	});

	$(".toggled-div.hidden").slideUp();

	$(".div-toggler").click(function(e) {
		e.preventDefault()
		e.stopPropagation
		var $this = $(this);
		var div = $this.parent().find(".toggled-div");
		console.log("DIV:");
		console.log(div);
		if (div.is(":hidden")) {
			$this.find("i.fas.fa-chevron-down").removeClass('fa-chevron-down').addClass('fa-chevron-up');
			div.slideDown();
		} else {
			$this.find("i.fas.fa-chevron-up").removeClass('fa-chevron-up').addClass('fa-chevron-down');
			div.slideUp();
		}
	});

	$('.jquery-submit').click(function() {
		var formid = $(this).data('target');
		$(formid).submit();
	});

	$(function () {
		$('.jquery-popover').popover({trigger: 'focus'});
	});

	$(function () {
		$('.jquery-tooltip').tooltip()
	});
});
