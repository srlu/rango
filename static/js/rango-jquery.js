$(document).ready( function() {


	$("#about-btn").click( function(event) {
		alert("You clicked the button using Jquery!");
	});

	$("p").hover( function() {
		$(this).css('color', 'red');
	},
	function() {
		$(this).css('color', 'blue');
	});

	$("#about-btn").addClass('btn btn-primary');

	$('#likes').click(function(){
		var catid;
		catid = $(this).attr("data-catid");
		$.get('/rango/like_category/', {category_id: catid}, function(data) {
			$('#like_count').html(data);
			$('#likes').hide();
		});
		
	});

	$('#suggestion').keyup(function() {
		var query;
		query = $(this).val();
		$.get('/rango/suggest_category/', {suggestion: query}, function(data){
			$('#cats').html(data);
		});
	});

});