let menuButton = document.getElementById("menu-button");
let dropdownMenu = document.getElementById("dropdown-menu");
let arrow = document.getElementById("anime1");
let arrow2 = document.getElementById("anime2");
let searchBar = document.getElementById("search-bar");
let boxForCategories = document.getElementById("mini-container-for-categories");
let boxForApprovals = document.getElementById("mini-container-for-approvals");
let categoriesButton = document.getElementById("categories");
let approvalsButton = document.getElementById("approvals");


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
            boxForApprovals.style.display = "none";
            arrow2.style.transform = "rotate(0deg)";
            }

        };

approvalsButton.onclick = function(){
        if(boxForApprovals.style.display === "grid"){
            boxForApprovals.style.display = "none";
            arrow2.style.transform = "rotate(0deg)";

            }
        else{
            boxForApprovals.style.display = "grid";
            arrow2.style.transform = "rotate(90deg)";
            boxForCategories.style.display = "none";
            arrow.style.transform = "rotate(0deg)";
            }

        };

function speak(textToSpeak){
    if (textToSpeak && window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const audio = new SpeechSynthesisUtterance(textToSpeak);
        audio.lang = 'zu-ZA';
        window.speechSynthesis.speak(audio);
    } else {
        console.error("Speech synthesis not available or text is empty.");
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    const popup = document.getElementById('message-popup');
    if (popup) {
        popup.style.display = 'block';
        setTimeout(() => {
            popup.style.display = 'none';
            }, 6000);
        }
    });
