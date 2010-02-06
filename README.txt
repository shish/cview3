                _____________   ____.__              ________  
                \_   ___ \   \ /   /|__| ______  _  _\_____  \ 
                /    \  \/\   Y   / |  |/ __ \ \/ \/ / _(__  < 
                \     \____\     /  |  \  ___/\     / /       \
                 \______  / \___/   |__|\___  >\/\_/ /______  /
                        \/                  \/              \/ 
                             An AJAX Comic Viewer

 * Create a folder on your server with these files in it
 * Create a "books" folder
 * Within "books", a folder for each book (eg "books/My_Story")
 * Within that, a folder for each chapter (eg "books/My_Story/001")
 * In that folder, put each page of the chapter

The end result should be

 cview3
  |- index.html
  |- static
  |   \- ...
  \- books
      |- My_Book
      |   |- 01
      |   |   |- page001.jpg
      |   |   |- page002.jpg
      |   |   |- page003.jpg
      |   |   \- page004.jpg
      |   \- 02
      |       |- page005.jpg
      |       |- page006.jpg
      |       |- page007.jpg
      |       \- page008.jpg
      \- Another_Book
          |- 01
          |   |- 001.jpg
          |   |- 002.jpg
          |   |- 003.jpg
          |   \- 004.jpg
          \- 02
              |- 005.jpg
              |- 006.jpg
              |- 007.jpg
              \- 008.jpg

