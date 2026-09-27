/*==========================================================
University of Haripur Portal
JavaScript
==========================================================*/


/*==========================================================
BUTTONS
==========================================================*/

const studentBtn = document.getElementById("studentBtn");
const teacherBtn = document.getElementById("teacherBtn");
const adminBtn = document.getElementById("adminBtn");


/*==========================================================
REDIRECT
==========================================================*/

studentBtn.addEventListener("click", () => {

    window.location.href = "../login_page/student-login.html";

});


teacherBtn.addEventListener("click", () => {

    window.location.href = "../login_page/teacher-login.html";

});


adminBtn.addEventListener("click", () => {

    window.location.href = "../login_page/admin-login.html";

});


/*==========================================================
KEYBOARD ACCESSIBILITY
==========================================================*/

document.addEventListener("keydown", (event) => {

    switch (event.key) {

        case "1":
            studentBtn.click();
            break;

        case "2":
            teacherBtn.click();
            break;

        case "3":
            adminBtn.click();
            break;

    }

});


/*==========================================================
BUTTON RIPPLE EFFECT
==========================================================*/

const buttons = document.querySelectorAll(".role-btn");

buttons.forEach((button) => {

    button.addEventListener("click", function (e) {

        const ripple = document.createElement("span");

        const size = Math.max(this.clientWidth, this.clientHeight);

        ripple.style.width = ripple.style.height = `${size}px`;

        ripple.style.left = `${e.offsetX - size / 2}px`;

        ripple.style.top = `${e.offsetY - size / 2}px`;

        ripple.classList.add("ripple");

        this.appendChild(ripple);

        setTimeout(() => {

            ripple.remove();

        }, 600);

    });

});


/*==========================================================
PAGE LOADED
==========================================================*/

window.addEventListener("load", () => {

    document.body.classList.add("loaded");

});


/*==========================================================
CONSOLE MESSAGE
==========================================================*/

console.log(
    "%cUniversity of Haripur Portal",
    "color:#14B8A6;font-size:18px;font-weight:bold;"
);

console.log(
    "%cDeveloped with ❤️ using HTML, CSS & JavaScript",
    "color:#94A3B8;font-size:13px;"
);