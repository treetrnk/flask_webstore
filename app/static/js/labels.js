$(document).ready(function() {
	$('#products').select2();

	$('#filterSelect').change(function() {
		var selected = $(this).val();
    var destination = $(this).data('url');
		window.location = destination + "?filter=" + selected;
	});

	$('#datatable-labels').dataTable( {
		"columnDefs": [
			{"orderable": false, "targets": [3,4,5,6]},
		],
		"lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
		"processing": true,
		"serverSide": true,
		"ajax": {
			"url": "/inventory/get-labels",
			"type": 'POST',
		},
	});

});
