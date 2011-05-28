function is_local_active() {
	return (
		window.localStorage &&
		localStorage.active == "true" &&
		check_for_updates()
	);
}
function activate_local() {
	if(window.localStorage) {
		localStorage.active = "true";
		$("#paginator")[0].style.display = "none";
		$("#uploader")[0].style.display = "none";
		$("#comiclist")[0].style.display = "none";
		$("#livelist")[0].style.display = "table";
		//$("#livelist").tablesorter();
		if(localStorage.tags) {
			//$("#tag_search").autocomplete(
			//	JSON.parse(localStorage.tags)
			//);
		}
		if(!localStorage.comics) {update_local();}
		add_alert("local mode active");
	}
	else {
		add_alert("local mode not supported");
	}
}
function deactivate_local() {
	localStorage.active = null;
	localStorage.comics = null;
	localStorage.tags = null;
	localStorage.updated = null;
	alert("Refresh the page to go back to normal mode");
}
function check_for_updates() {
	if(localStorage.updated && localStorage.updated > (new Date() + 60)) {
		update_local();
	}
	else {
		add_alert("already up to date");
	}
	return true;
}
function update_local() {
	add_alert("downloading data");
	localStorage.updated = +new Date();
	$.get(
		"/api/all_comics", {},
		function(data) {
			localStorage.comics = data;
			add_alert("comic data downloaded");
		}
	);
	$.get(
		"/api/all_tags", {},
		function(data) {
			localStorage.tags = data;
			//$("#tag_search").autocomplete(
			//	JSON.parse(localStorage.tags)
			//);
			add_alert("tag data downloaded");
		}
	);
}
function live_search(val) {
	var comics = JSON.parse(localStorage.comics);
	var vals = val.toLowerCase().split(" ");
	var match = true;
	var cc = null;
	var cct = null;

	if(val.length < 2) {
		$("#livelistbody")[0].innerHTML =
			"<tr><td colspan='5'><center>Enter at least 2 letters to search for</center></td></tr>";
		return;
	}
	else {
		$("#livelistbody")[0].innerHTML = "";
	}

	for(var c in comics) {
		cc = comics[c];
		if(!cc["tags"]) continue;
		cct = cc["tags"].toLowerCase();

		if(!cct.match(val.toLowerCase())) continue;

		$("#livelistbody")[0].innerHTML += "<tr>"+
			"<td><a href='javascript: show_comicbox(\""+cc["disk_title"]+"\");'>"+cc["title"]+"</a></td>"+
			"<td>"+cc["pages"]+"</td>"+
			"<td><img src='/static/"+cc["language"]+".png' width='20' height='14'> "+cc["tags"]+"</td>"+
			"<td>"+cc["posted"]+"</td>"+
			"<td><a href='/comic/download/"+cc["id"]+"/"+cc["disk_title"]+".cbz'>download</a></td>"+
			"</tr>";
	}
}

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
 * Comic Box
 */
function show_comicbox(comic) {
	document.location.hash = "#"+comic+"--0--0";
	loadBook = comic;
	loadChap = "0";
	loadPage = "0";
	initBookSelector();

	$("#comicshade")[0].style.display = "block";
	$("#comicbox")[0].style.display = "block";
}
function close_comicbox() {
	document.location.hash = "";
	$("#comicshade")[0].style.display = "none";
	$("#comicbox")[0].style.display = "none";
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
	if(!is_local_active()) {
		if(text) window.location = "/comic/list?search="+text;
		else if(window.localStorage) {activate_local();}
	}
}
