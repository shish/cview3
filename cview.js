// config
// interface: the method used to get lists of files
//   ajax.py: a python script
//   apache : use the apache file listing (requires indexes to be enabled)
interface = "apache";
root = "./books";

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
			var re = new RegExp('<A HREF="([^/"]+)/">');
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
			var re = new RegExp('<A HREF="([^/"]+)/">');
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
			var re = new RegExp(/<A HREF="([^/"]+(jpg|png|gif))">/i);
			var m = re.exec(pages_lines[i]);
			if(m != null) {
				pages.push(m[1]);
			}
		}
		return pages.sortInPlace();
	}
}
// }}}
// {{{ interactive stuff
function initBookSelector() {
	bookSelector = document.getElementById("book");
	books = getBooks();
	bookSelector.options.length = 0;
	for(i=0; books[i]; i++) {bookSelector.options[i] = new Option(books[i], books[i]);}
	bookSelector.selectedIndex = 0;
	initChapSelector();
}
function initChapSelector() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	chaps = getChapters(selectedValue(bookSelector));
	chapSelector.options.length = 0;
	for(i=0; chaps[i]; i++) {chapSelector.options[i] = new Option(chaps[i], chaps[i]);}
	chapSelector.selectedIndex = 0;
	initPageSelector();
}
function initPageSelector() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	pages = getPages(selectedValue(bookSelector), selectedValue(chapSelector));
	pageSelector.options.length = 0;
	for(i=0; pages[i]; i++) {pageSelector.options[i] = new Option(i+1, pages[i]);}
	pageSelector.selectedIndex = 0;
	initDisplay();
}
function initDisplay() {
	bookSelector = document.getElementById("book");
	chapSelector = document.getElementById("chap");
	pageSelector = document.getElementById("page");
	display = document.getElementById("display");
	display.src = root + "/" + selectedValue(bookSelector) + "/" + selectedValue(chapSelector) + "/" + selectedValue(pageSelector);
	window.scroll(0, 0);
	initPreload();
}
function initPreload() {
	pageSelector = document.getElementById("page");
	pages = pageSelector.options.length;
	if(pageSelector.selectedIndex+1 < pages) {
		nextPage = pageSelector.options[pageSelector.selectedIndex+1].value;
		img = Image();
		img.src = root + "/" + selectedValue(bookSelector) + "/" + selectedValue(chapSelector) + "/" + nextPage;
	}
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
