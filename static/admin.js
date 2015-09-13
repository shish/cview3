/*
 * Alert Box
 */
function clear_alerts() {
	$("#alerts")[0].innerHTML = "";
	$("#alertbox")[0].style.display = "none";
}
function add_alert(text) {
	$("#alertbox")[0].style.display = "block";
	$("#alerts")[0].innerHTML += "<div class='alert'>"+text+"</div>";
}

/*
 * AJAX
 */
function rename(comic_id, title) {
	original = title;
	replacement = prompt("Rename \""+title+"\" to:", title);
	if(replacement) {
		$.post(
			"/comic/rename", {"comic_id": comic_id, "title": replacement},
			function(data) {add_alert(data);}
		);
	}
}
function edit_tags(comic_id, title, tags) {
	new_tags = prompt("New tags for \""+title+"\"", tags);
	if(new_tags) {
		$.post(
			"/comic/set_tags", {"comic_id": comic_id, "tags": new_tags},
			function(data) {add_alert(data);}
		);
	}
}
function edit_language(comic_id, title, language) {
	new_language = prompt("New language for \""+title+"\"", language);
	if(new_language) {
		$.post(
			"/comic/set_language", {"comic_id": comic_id, "language": new_language},
			function(data) {add_alert(data);}
		);
	}
}
function vote(comic_id, rating) {
	$.post(
		"/comic/rate", {"comic_id": comic_id, "rating": rating},
		function(data) {add_alert(data);}
	);
}
function delete_comic(comic_id, title) {
	if(confirm("Are you sure you want to delete \""+title+"\"?")) {
		$.post(
			"/comic/delete", {"comic_id": comic_id},
			function(data) {add_alert(data);}
		);
	}
}
function search_prompt() {
	text = prompt("Enter a tag to search for");
	if(text) window.location = "/comic/list?search="+text;
	else if(window.localStorage) {activate_local();}
}
