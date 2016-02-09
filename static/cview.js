// config:
// ~~~~~~~
// list_interface:
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
var image_domain = "//rule34c-images.paheal.net";
var list_interface = "apache";
var root = "/books";
var comment_add_url = "/comment/add";

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
};

Array.prototype.sortInPlace = function() {
	this.sort();
	return this;
};

function selectedValue(selector) {
	return selector.options[selector.selectedIndex].value;
}

function sjax(url, postdata) {
	var http_request = getHTTPObject();

	if(postdata) {
		http_request.open('POST', url, false);
		http_request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		http_request.setRequestHeader("Content-length", postdata.length);
		http_request.setRequestHeader("Connection", "close");
		http_request.send(postdata);
	}
	else {
		http_request.open('GET', url, false);
		http_request.send(postdata);
	}

	if(http_request.status == 200) {
		return http_request.responseText;
	}
	else {
		alert("Error fetching stuff :(");
	}
}
// }}}
// {{{ list_interfaces
if(list_interface == "ajax.py") {
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
else if(list_interface == "apache") {
	function getBooks() {
		var books = Array();
		var books_html = sjax(root+"/");
		var books_lines = books_html.split("\n");
		for(var i=0; i<books_lines.length; i++) {
			var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
			var m = re.exec(books_lines[i]);
			if(m != null && m[1] != "..") {
				books.push(m[1]);
			}
		}
		return books.sortInPlace();
	}
	function getChapters(book) {
		var chaps = Array();
		var chaps_html = sjax(root+"/"+book+"/");
		var chaps_lines = chaps_html.split("\n");
		for(var i=0; i<chaps_lines.length; i++) {
			var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
			var m = re.exec(chaps_lines[i]);
			if(m != null && m[1] != "..") {
				chaps.push(m[1]);
			}
		}
		return chaps.sortInPlace();
	}
	function getPages(book, chap) {
		var pages = Array();
		var pages_html = sjax(root+"/"+book+"/"+chap+"/");
		var pages_lines = pages_html.split("\n");
		for(var i=0; i<pages_lines.length; i++) {
			var re = new RegExp("<A HREF=\"([^/\"]+(jpg|jpeg|png|gif))\">", "i");
			var m = re.exec(pages_lines[i]);
			if(m != null) {
				pages.push(m[1]);
			}
		}
		return pages.sortInPlace();
	}
	/*
	function getAnnotations(book, chap) {
		var annotations = Array();
		var annotations_html = sjax(root+"/"+book+"/"+chap+"/");
		var annotations_lines = annotations_html.split("\n");
		for(var i=0; i<annotations_lines.length; i++) {
			var re = new RegExp("<A HREF=\"([^/\"]+(txt))\">", "i");
			var m = re.exec(annotations_lines[i]);
			if(m != null) {
				annotations[m[1]] = m[1];
			}
		}
		return annotations.sortInPlace();
	}
	*/
}
// }}}
// {{{ interactive stuff
// current state
var loadBook = "";
var loadBookIndex = 0;
var loadChap = 0;
var loadPage = 0;
var loadedHash = "";
//knownAnnotations = Array();

// {{{ main waterfall
function init() {
	var hash = document.location.hash;
	if(hash.length > 0) {
		var parts = hash.split("--");
		if(parts.length == 3) {
			loadBook = parts[0].substring(1);
			loadChap = parts[1];
			loadPage = parts[2];
		}
	}
	initBookSelector();
	setInterval(function() {
		if(document.location.hash != loadedHash) {
			init();
		}
	}, 500);
}
function initBookSelector() {
	var bookSelector = document.getElementById("book");
	var books = getBooks();
	bookSelector.options.length = 0;
	for(var i=0; books[i]; i++) {bookSelector.options[i] = new Option(books[i].replace(/_/g," "), books[i]);}
	for(var i=0; i<bookSelector.options.length; i++) {if(bookSelector.options[i].value == loadBook) loadBookIndex=i;}
	bookSelector.selectedIndex = loadBookIndex;
	loadBook = "";
	initChapSelector();
}
function initChapSelector() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var chaps = getChapters(selectedValue(bookSelector));
	chapSelector.options.length = 0;
	for(var i=0; chaps[i]; i++) {chapSelector.options[i] = new Option(chaps[i].replace(/_/g," "), chaps[i]);}
	chapSelector.selectedIndex = loadChap;
	loadChap = 0;
	initPageSelector();
}
function initPageSelector() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var pages = getPages(selectedValue(bookSelector), selectedValue(chapSelector));
	pageSelector.options.length = 0;
	for(var i=0; pages[i]; i++) {pageSelector.options[i] = new Option(i+1, pages[i]);}
	pageSelector.selectedIndex = loadPage;
	loadPage = 0;
	//knownAnnotations = getAnnotations(selectedValue(bookSelector), selectedValue(chapSelector));
	initDisplay();
}
function initDisplay() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var xdisplay = document.getElementById("display");
	xdisplay.src = pagePath(
		selectedValue(bookSelector),
	    selectedValue(chapSelector),
		selectedValue(pageSelector)
	);
	//window.scroll(0, xdisplay.offsetTop);
	window.scrollTo(0, 0);
	//initAnnotations();
	initPreload();
}
function pagePath(book, chap, page) {
	return image_domain + root + "/" + book + "/" + chap + "/" + page;
}
function initPreload() {
	function preload(book, chap, page) {
		var img = document.createElement("img");
		img.setAttribute("src", pagePath(book, chap, page));
	}

	var bookSelector = document.getElementById("book");
	var pageSelector = document.getElementById("page");
	var chapSelector = document.getElementById("chap");
	var pages = pageSelector.options.length;
	var chaps = chapSelector.options.length;
//	var buffering_div = document.getElementById("buffering");
//	buffering_div.style.visibility = "visible";
	if(pageSelector.selectedIndex+1 < pages) {
		var nextPage = pageSelector.options[pageSelector.selectedIndex+1].value;
		preload(
			selectedValue(bookSelector),
			selectedValue(chapSelector),
			nextPage
		);
	}
	else if(chapSelector.selectedIndex+1 < chaps) {
		var nextChap = chapSelector.options[chapSelector.selectedIndex+1].value;
		var nextPage = getPages(selectedValue(bookSelector), nextChap)[0];
		preload(
			selectedValue(bookSelector),
			nextChap,
			nextPage
		);
	}
//	img.onload = function() {
//		buffering_div.style.visibility = "hidden";
//	}
	document.location.hash = selectedValue(bookSelector) + "--" +
	                         chapSelector.selectedIndex + "--" +
	                         pageSelector.selectedIndex;
	loadedHash = document.location.hash;
}

function moveToNextPage() {
	var pageSelector = document.getElementById("page");
	var chapSelector = document.getElementById("chap");
	var pages = pageSelector.options.length;
	var chaps = chapSelector.options.length;
	if(pageSelector.selectedIndex+1 < pages) {
		pageSelector.selectedIndex++;
		initDisplay();
	}
	else if(chapSelector.selectedIndex+1 < chaps) {
		chapSelector.selectedIndex++;
		initPageSelector();
	}
}
function moveToPrevPage() {
	var pageSelector = document.getElementById("page");
	if(pageSelector.selectedIndex > 0) {
		pageSelector.selectedIndex--;
		initDisplay();
	}
}
// }}}
// {{{ annotations
function initAnnotations() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var target_annotation = selectedValue(pageSelector).replace(/(jpg|jpeg|png|gif)$/, "txt");;

	var commentDiv = document.getElementById("comments");

	while(commentDiv.childNodes[0]) {
		commentDiv.removeChild(commentDiv.childNodes[0]);
	}

	commentDiv.innerHTML = "Loading Comments...";
//	annotation_data = sjax(root + "/" + selectedValue(bookSelector) + "/" +
//							selectedValue(chapSelector) + "/" + target_annotation)
	var annotation_data = sjax("/comment/get?page="+
			selectedValue(bookSelector) + "/" +
			selectedValue(chapSelector) + "/" +
			selectedValue(pageSelector));
	if(annotation_data) {
		var lines = annotation_data.split("\n");
		commentDiv.innerHTML = "";
		for(var i=0; lines[i]; i++) {
			var parts = lines[i].split(":", 2);
			if(parts[0] == "comment") {
				parts = lines[i].split(":", 4);
				var name = parts[1];
				var comment = parts[2];

				p = document.createElement("p");
				p.innerHTML = escape(name)+": "+comment;
				commentDiv.appendChild(p);
			}
			else if(parts[0] == "note") {
				parts = lines[i].split(":", 8);
				var ip = parts[1];
				var name = parts[2];
				var comment = parts[6];

				var xdisplay = document.getElementById("display");

				var div = document.createElement("newDiv");
				div.style.position = "absolute";
				div.style.left    = xdisplay.offsetLeft + parseInt(parts[3]);
				div.style.top     = xdisplay.offsetTop + parseInt(parts[4]);
				div.style.width   = parts[5];
				div.setAttribute("class", "note");
				div.appendChild(document.createTextNode(comment));

				commentDiv.appendChild(div);
			}
			else if(parts[0] == "x") {
				// ignore
			}
			else {
				commentDiv.innerHTML += lines[i];
			}
		}
	}
	else {
		commentDiv.innerHTML = "No Comments";
	}
	if(comment_add_url) {
		var newDiv = document.createElement("div");
		newDiv.innerHTML = "<center>"+
			"<textarea id='comment_text'></textarea>"+
			"<br><input type='button' onclick='submitComment();' value='Comments are WIP'>"+
			"</center>";
		commentDiv.appendChild(newDiv);
	}
//	commentDiv.innerHTML += ""+
//	"<p><a href='javascript: refreshAnnotations();'>Refresh Comments</a>";
}

function submitComment() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var target = selectedValue(bookSelector) + "/" +
		         selectedValue(chapSelector) + "/" +
		         selectedValue(pageSelector);
	var comment = document.getElementById("comment_text").value;
	addComment(target, comment);
	refreshAnnotations();
}
function addComment(target, comment) {
	sjax(comment_add_url, "target="+encodeURI(target)+"&comment="+encodeURI(comment));
}
function refreshAnnotations() {
	// knownAnnotations = getAnnotations(selectedValue(bookSelector), selectedValue(chapSelector));
	initAnnotations();
}
// }}}
// {{{ scaling
function setScale(scale) {
	var xdisplay = document.getElementById("display");
	xdisplay.style.width=scale;
}
// }}}
// keyboard {{{
document.onkeydown = function(e) {
	var keycode = null;
	if(navigator.appName == "Microsoft Internet Explorer") {
		if(!e) e = window.event;
		if(e.keyCode) {
			keycode = e.keyCode;
			if((keycode == 39) || (keycode == 37)) {
				window.event.keyCode = 0;
			}
		}
		else {
			keycode = e.which;
		}
	}
	else {
		if(e.which) {
			keycode = e.which;
		} else {
			keycode = e.keyCode;
		}
	}

	if(keycode == 39) {
		moveToNextPage();
		return false;
	}
	else if (keycode == 37) {
		moveToPrevPage();
		return false;
	}
};
// }}}
