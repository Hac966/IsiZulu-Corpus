let menuButton = document.getElementById("menu-button");
let dropdownMenu = document.getElementById("dropdown-menu");
let arrow = document.getElementById("anime1");
let searchBar = document.getElementById("search-bar");
let boxForCategories = document.getElementById("mini-container-for-categories");
let categoriesButton = document.getElementById("categories");


    menuButton.onclick = function(){
        if (menuButton.innerHTML === "☰"){
            dropdownMenu.style.display = "grid";
            menuButton.innerHTML = "X";
        }
        else {
            dropdownMenu.style.display = "none";
            boxForCategories.style.display = "none";
            arrow.style.transform = "rotate(0deg)";
            menuButton.innerHTML = "☰";
        }
            };




categoriesButton.onclick = function(){
        if(boxForCategories.style.display === "grid"){
            boxForCategories.style.display = "none";
            arrow.style.transform = "rotate(0deg)";

            }
        else{
            boxForCategories.style.display = "grid";
            arrow.style.transform = "rotate(90deg)";
            }

        };






