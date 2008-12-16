// config:
// ~~~~~~~
// interface:
//  the method used to get lists of files
//   ajax.py: a python script
//   apache : use the apache file listing (requires indexes to be enabled)
//
// root:
//  where the books are stored
//
// comment_add_url:
//  where to post comments, null to disable
//
interface = "apache";
root = "./books";
comment_add_url = null;

// {{{ fix javascript deficiencies
function getHTTPObject() { 
	if (window.XMLHttpRequest){
		return new XMLHttpRequest();
	}
	else if(window.ActiveXObject){
		return new ActiveXObject("Microsoft.XMLHTTP");
	}
}

String.prototype.trim = function() {
	return this.replace(/^\s+|\s+$/g,"");
}

Array.prototype.sortInPlace = function() {
	this.sort();
	return this;
}

function selectedValue(selector) {
	return selector.options[selector.selectedIndex].value;
}

function sjax(url) {
	http_request = getHTTPObject();
	http_request.open('GET', url, false);
	http_request.send(null);

	if(http_request.status == 200) {
		return http_request.responseText;
	}
	else {
		alert("Error fetching stuff :(");
	}
}
// }}}
// {{{ interfaces
if(interface == "ajax.py") {
	function getBooks() {
		return sjax("ajax.py?func=get_books").trim().split("\n").sortInPlace();
	}
	function getChapters(book) {
		return sjax("ajax.py?func=get_chaps&book="+book).trim().split("\n").sortInPlace();
	}
	function getPages(book, chap) {
		return sjax("ajax.py?func=get_pages&book="+book+"&chap="+chap).trim().split("\n").sortInPlace();
	}
}
else if(interface == "apache") {
	function getBooks() {
		books = Array();
		books_html = sjax(root+"/");
		books_lines = books_html.split("\n");
		for(i=0; i<books_lines.length; i++) {
			var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
			var m = re.exec(books_lines[i]);
			if(m != null) {
				books.push(m[1]);
			}
		}
		return books.sortInPlace();
	}
	function getChapters(book) {
		chaps = Array();
		chaps_html = sjax(root+"/"+book+"/");
		chaps_lines = chaps_html.split("\n");
		for(i=0; i<chaps_lines.length; i++) {
			var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
			var m = re.exec(chaps_lines[i]);
			if(m != null) {
				chaps.push(m[1]);
			}
		}
		return chaps.sortInPlace();
	}
	function getPages(book, chap) {
		pages = Array();
		pages_html = sjax(root+"/"+book+"/"+chap+"/");
		pages_lines = pages_html.split("\n");
		for(i=0; i<pages_lines.length; i++) {
			var re = new RegExp("<A HREF=\"([^/\"]+(jpg|png|gif))\">", "i");
			var m = re.exec(pages_lines[i]);
			if(m != null) {
				pages.push(m[1]);
			}
		}
		return pages.sortInPlace();
	}
	function getAnnotations(book, chap) {
		annotations = Array();
		annotations_html = sjax(root+"/"+book+"/"+chap+"/");
		annotations_lines = annotations_html.split("\n");
		for(i=0; i<annotations_lines.length; i++) {
			var re = new RegExp("<A HREF=\"([^/\"]+(txt))\">", "i");
			var m = re.exec(annotations_lines[i]);
			if(m != null) {
				annotations[m[1]] = m[1];
			}
		}
		return annotations.sortInPlace();
	}
}
// }}}
// {{{ interactive stuff
// current state
loadBook = "";
loadBookIndex = 0;
loadChap = 0;
loadPage = 0;
loadedHash = "";
knownAnnotations = Array();
loadedNotes = Array();
visibleNotes = Array();

// {{{ main waterfall
function init() {
	hash = document.location.hash;
	if(hash.length > 0) {
		parts = hash.split("--");
		if(parts.length == 3) {
			loadBook = parts[0].substring(1);
			loadChap = parts[1];
			loadPage = parts[2];
		}
	}
	initBookSelector();
	setInterval("checkHash();", 500);
}
function checkHash() {
	if(document.location.hash != loadedHash) {
		init();
	}
}
function initBookSelector() {
	bookSelector = document.getElementById("book");
	books = getBooks();
	bookSelector.options.length = 0;
	for(i=0; books[i]; i++) {bookSelector.options[i] = new Option(books[i], books[i]);}
	for(i=0; i<bookSelector.options.length; i++) {if(bookSelector.options[i].value == loadBook) loadBookIndex=i;};
	bookSelector.selectedIndex = loadBookIndex;
	loadBook = "";
	initChapSelector();
}
function initChapSelector() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	chaps = getChapters(selectedValue(bookSelector));
	chapSelector.options.length = 0;
	for(i=0; chaps[i]; i++) {chapSelector.options[i] = new Option(chaps[i], chaps[i]);}
	chapSelector.selectedIndex = loadChap;
	loadChap = 0;
	initPageSelector();
}
function initPageSelector() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	pages = getPages(selectedValue(bookSelector), selectedValue(chapSelector));
	pageSelector.options.length = 0;
	for(i=0; pages[i]; i++) {pageSelector.options[i] = new Option(i+1, pages[i]);}
	pageSelector.selectedIndex = loadPage;
	loadPage = 0;
	knownAnnotations = getAnnotations(selectedValue(bookSelector), selectedValue(chapSelector));
	initDisplay();
}
function initDisplay() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	xdisplay = document.getElementById("display");
	xdisplay.src = root + "/" + selectedValue(bookSelector) + "/" +
	               selectedValue(chapSelector) + "/" + selectedValue(pageSelector);
	window.scroll(0, 0);
	initAnnotations();
	initPreload();
}
function initPreload() {
	bookSelector = document.getElementById("book");
	pageSelector = document.getElementById("page");
	chapSelector = document.getElementById("chap");
	pages = pageSelector.options.length;
	chaps = chapSelector.options.length;
	if(pageSelector.selectedIndex+1 < pages) {
		nextPage = pageSelector.options[pageSelector.selectedIndex+1].value;
		img = Image(0, 0);
		img.src = root + "/" + selectedValue(bookSelector) + "/" +
		          selectedValue(chapSelector) + "/" + nextPage;
	}
	else if(chapSelector.selectedIndex+1 < chaps) {
		nextChap = chapSelector.options[chapSelector.selectedIndex+1].value;
		nextChapPages = getPages(selectedValue(bookSelector), nextChap);
		nextPage = nextChapPages[0];
		img = Image(0, 0);
		img.src = root + "/" + selectedValue(bookSelector) + "/" +
		          nextChap + "/" + nextPage;
	}
	document.location.hash = selectedValue(bookSelector) + "--" +
	                         chapSelector.selectedIndex + "--" +
	                         pageSelector.selectedIndex;
	loadedHash = document.location.hash;
}

function moveToNextPage() {
	pageSelector = document.getElementById("page");
	chapSelector = document.getElementById("chap");
	pages = pageSelector.options.length;
	chaps = chapSelector.options.length;
	if(pageSelector.selectedIndex+1 < pages) {
		pageSelector.selectedIndex++;
		initDisplay();
	}
	else if(chapSelector.selectedIndex+1 < chaps) {
		chapSelector.selectedIndex++;
		initPageSelector();
	}
}
// }}}
// {{{ annotations
function initAnnotations() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	target_annotation = selectedValue(pageSelector).replace(/(jpg|png|gif)$/, "txt");

	clearNotes();
	loadedNotes = Array();
	comments = document.getElementById("comments");

	if(knownAnnotations[target_annotation]) {
		comments.innerHTML = "Loading comments...";
		annotation_data = sjax(root + "/" + selectedValue(bookSelector) + "/" +
		                        selectedValue(chapSelector) + "/" + target_annotation)
		lines = annotation_data.split("\n");
		comments.innerHTML = "";
		for(i=0; lines[i]; i++) {
			parts = lines[i].split(":", 2);
			if(parts[0] == "comment") {
				parts = lines[i].split(":", 4);
				ip = parts[1];
				name = parts[2];
				comment = parts[3];
				comments.innerHTML += "<p>"+escape(name)+": "+escape(comment);
			}
			else if(parts[0] == "note") {
				parts = lines[i].split(":", 8);
				ip = parts[1];
				name = parts[2];
				comment = parts[7];

				div = document.createElement("div");
				div.left   = parts[3];
				div.top    = parts[4];
				div.width  = parts[5];
				div.height = parts[6];
				div.appendChild(document.createTextNode(comment));
				loadedNotes.push(div);
			}
			else {
				comments.innerHTML += lines[i];
			}
		}
		drawNotes();
	}
	else {
		comments.innerHTML = "No Comments";
	}
	if(comment_add_url) {
		comments.innerHTML += ""+
		"<p><textarea id='comment_text'></textarea>"+
		"<br><input type='button' onclick='submitComment();' value='Comments are WIP'>";
	}
//	comments.innerHTML += ""+
//	"<p><a href='javascript: refreshAnnotations();'>Refresh Comments</a>";
}

function submitComment() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	target = selectedValue(bookSelector) + "/" + selectedValue(chapSelector) +
	         "/" + selectedValue(pageSelector);
	comment = document.getElementById("comment_text").value;
	addComment(target, comment);
	refreshAnnotations();
}
function addComment(target, comment) {
	sjax(comment_add_url+"?target="+encodeURI(target)+"&comment="+encodeURI(comment));
}
function refreshAnnotations() {
	knownAnnotations = getAnnotations(selectedValue(bookSelector), selectedValue(chapSelector));
	initAnnotatons();
}

function clearNotes() {
	return false;
	comments = document.getElementById("comments");
	for(i=0; comments.children[i]; i++) {
		comments.removeChild();
	}
}
function drawNotes() {
	comments = document.getElementById("comments");
	for(i=0; loadedNotes[i]; i++) {
		comments.appendChild(loadedNotes[i]);
	}
}
// }}}
// {{{ scaling
function setScaled(scaled) {
	display = document.getElementById("display");
	if(scaled) display.style.width="100%";
	else display.style.width="";
}
function setScale(scale) {
	display = document.getElementById("display");
	display.style.width=scale;
}
// }}}
// }}}
