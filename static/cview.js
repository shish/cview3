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
var list_interface = "apache";
var root = "./books";
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

	if(http_request.status === 200) {
		return http_request.responseText;
	}
	else {
		alert("Error fetching stuff :(");
	}
}
// }}}
// {{{ interfaces
var getBooks, getChapters, getPages;

if(list_interface === "ajax.py") {
	getBooks = function() {
		return sjax("ajax.py?func=get_books").trim().split("\n").sortInPlace();
	};
	getChapters = function(book) {
		return sjax("ajax.py?func=get_chaps&book="+book).trim().split("\n").sortInPlace();
	};
	getPages = function(book, chap) {
		return sjax("ajax.py?func=get_pages&book="+book+"&chap="+chap).trim().split("\n").sortInPlace();
	};
}
else if(list_interface === "apache") {
	getBooks = function() {
		var books = [];
		var books_html = sjax(root+"/");
		var books_lines = books_html.split("\n");
		var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
		var i;
		for(i in books_lines) {
			var m = re.exec(books_lines[i]);
			if(m !== null && m[1] !== "..") {
				books.push(m[1]);
			}
		}
		return books.sortInPlace();
	};
	getChapters = function(book) {
		var chaps = [];
		var chaps_html = sjax(root+"/"+book+"/");
		var chaps_lines = chaps_html.split("\n");
		var re = RegExp("<A HREF=\"([^/\"]+)/\">", "i");
		var i;
		for(i in chaps_lines) {
			var m = re.exec(chaps_lines[i]);
			if(m !== null && m[1] !== "..") {
				chaps.push(m[1]);
			}
		}
		return chaps.sortInPlace();
	};
	getPages = function(book, chap) {
		var pages = [];
		var pages_html = sjax(root+"/"+book+"/"+chap+"/");
		var pages_lines = pages_html.split("\n");
		var re = new RegExp("<A HREF=\"([^/\"]+(jpg|png|gif))\">", "i");
		var i;
		for(i in pages_lines) {
			var m = re.exec(pages_lines[i]);
			if(m !== null) {
				pages.push(m[1]);
			}
		}
		return pages.sortInPlace();
	};
	/*
	getAnnotations = function(book, chap) {
		var annotations = [];
		var annotations_html = sjax(root+"/"+book+"/"+chap+"/");
		var annotations_lines = annotations_html.split("\n");
		var re = new RegExp("<A HREF=\"([^/\"]+(txt))\">", "i");
		var i;
		for(i=0; i<annotations_lines.length; i++) {
			var m = re.exec(annotations_lines[i]);
			if(m !== null) {
				annotations[m[1]] = m[1];
			}
		}
		return annotations.sortInPlace();
	};
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
//knownAnnotations = []

// {{{ main waterfall
function init() {
	var hash = document.location.hash;
	if(hash.length > 0) {
		var parts = hash.split("--");
		if(parts.length === 3) {
			loadBook = parts[0].substring(1);
			loadChap = parts[1];
			loadPage = parts[2];
		}
	}
	initBookSelector();
	setInterval(function() {
		if(document.location.hash !== loadedHash) {
			init();
		}
	}, 500);
}
function initBookSelector() {
	var bookSelector = document.getElementById("book");
	var books = getBooks();
	var i;
	bookSelector.options.length = 0;
	for(i=0; books[i]; i++) {
		bookSelector.options[i] = new Option(books[i].replace(/_/g," "), books[i]);
	}
	for(i=0; i<bookSelector.options.length; i++) {
		if(bookSelector.options[i].value === loadBook) {loadBookIndex=i;}
	}
	bookSelector.selectedIndex = loadBookIndex;
	loadBook = "";
	initChapSelector();
}
function initChapSelector() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var chaps = getChapters(selectedValue(bookSelector));
	var i;
	chapSelector.options.length = 0;
	for(i=0; chaps[i]; i++) {
		chapSelector.options[i] = new Option(chaps[i].replace(/_/g," "), chaps[i]);
	}
	chapSelector.selectedIndex = loadChap;
	loadChap = 0;
	initPageSelector();
}
function initPageSelector() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var pages = getPages(selectedValue(bookSelector), selectedValue(chapSelector));
	var i;
	pageSelector.options.length = 0;
	for(i=0; pages[i]; i++) {pageSelector.options[i] = new Option(i+1, pages[i]);}
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
	xdisplay.src = root + "/" + selectedValue(bookSelector) + "/" +
	               selectedValue(chapSelector) + "/" + selectedValue(pageSelector);
	//window.scroll(0, xdisplay.offsetTop);
	window.scroll(0, 0);
	//initAnnotations();
	initPreload();
}
function initPreload() {
	var bookSelector = document.getElementById("book");
	var pageSelector = document.getElementById("page");
	var chapSelector = document.getElementById("chap");
	var pages = pageSelector.options.length;
	var chaps = chapSelector.options.length;
	var nextPage, img;
//	buffering_div = document.getElementById("buffering");
//	buffering_div.style.visibility = "visible";
	if(pageSelector.selectedIndex+1 < pages) {
		nextPage = pageSelector.options[pageSelector.selectedIndex+1].value;
		img = new Image(0, 0);
		img.src = root + "/" + selectedValue(bookSelector) + "/" +
		          selectedValue(chapSelector) + "/" + nextPage;
	}
	else if(chapSelector.selectedIndex+1 < chaps) {
		var nextChap = chapSelector.options[chapSelector.selectedIndex+1].value;
		var nextChapPages = getPages(selectedValue(bookSelector), nextChap);
		nextPage = nextChapPages[0];
		img = new Image(0, 0);
		img.src = root + "/" + selectedValue(bookSelector) + "/" +
		          nextChap + "/" + nextPage;
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
	var target_annotation = selectedValue(pageSelector).replace(/(jpg|png|gif)$/, "txt");
	var i, div;

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
		for(i=0; lines[i]; i++) {
			var parts = lines[i].split(":", 2);
			var name, comment;
			if(parts[0] === "comment") {
				parts = lines[i].split(":", 4);
				name = parts[1];
				comment = parts[2];

				var p = document.createElement("p");
				p.innerHTML = escape(name)+": "+comment;
				commentDiv.appendChild(p);
			}
			else if(parts[0] === "note") {
				parts = lines[i].split(":", 8);
				var ip = parts[1];
				name = parts[2];
				comment = parts[6];

				var xdisplay = document.getElementById("display");

				div = document.createElement("div");
				div.style.position = "absolute";
				div.style.left    = xdisplay.offsetLeft + parseInt(parts[3], 10);
				div.style.top     = xdisplay.offsetTop + parseInt(parts[4], 10);
				div.style.width   = parts[5];
				div.setAttribute("class", "note");
				div.appendChild(document.createTextNode(comment));

				commentDiv.appendChild(div);
			}
			else if(parts[0] === "x") {
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
		div = document.createElement("div");
		div.innerHTML = "<center><textarea id='comment_text'></textarea>"+
		"<br><input type='button' onclick='submitComment();' value='Comments are WIP'></center>";
		commentDiv.appendChild(div);
	}
//	commentDiv.innerHTML += ""+
//	"<p><a href='javascript: refreshAnnotations();'>Refresh Comments</a>";
}

function submitComment() {
	var bookSelector = document.getElementById("book");
	var chapSelector = document.getElementById("chap");
	var pageSelector = document.getElementById("page");
	var target = selectedValue(bookSelector) + "/" + selectedValue(chapSelector) +
	         "/" + selectedValue(pageSelector);
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
function setScaled(scaled) {
	var xdisplay = document.getElementById("display");
	if(scaled) {
		xdisplay.style.width="100%";
	}
	else {
		xdisplay.style.width="";
	}
}
function setScale(scale) {
	var xdisplay = document.getElementById("display");
	xdisplay.style.width = scale;
}
// }}}
// keyboard {{{
document.onkeydown = key_pressed;
function key_pressed(e) {
	var keycode = 0;
	if(navigator.appName === "Microsoft Internet Explorer") {
		if(!e) {
			e = window.event;
		}
		if(e.keyCode) {
			keycode = e.keyCode;
			if((keycode === 39) || (keycode === 37)) {
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

	if(keycode === 39) {
		moveToNextPage();
		return false;
	}
	else if (keycode === 37) {
		moveToPrevPage();
		return false;
	}
}
// }}}
