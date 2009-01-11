function rename(comic_id, title) {
	original = title;
	replacement = prompt("Rename \""+title+"\" to:", title);
	if(replacement) {
		alert(sjax("/comic/rename", "comic_id="+comic_id+"&title="+replacement));
	}
}
function edit_tags(comic_id, title, tags) {
	new_tags = prompt("New tags for \""+title+"\"", tags);
	if(new_tags) {
		alert(sjax("/comic/set_tags", "comic_id="+comic_id+"&tags="+new_tags));
	}
}
function delete_comic(comic_id, title) {
	if(confirm("Are you sure you want to delete \""+title+"\"?")) {
		alert(sjax("/comic/delete", "comic_id="+comic_id));
	}
}
