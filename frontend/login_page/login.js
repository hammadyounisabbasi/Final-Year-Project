/*
==========================================================
  Zero-Trust Autonomous Campus Ecosystem
  Universal Login
  Student + Teacher + Admin
==========================================================
*/
document.addEventListener("DOMContentLoaded", () => {
    /*==========================================================
      API CONFIGURATION
    ==========================================================*/
    const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;
    /*==========================================================
      DETECT CURRENT ROLE
    ==========================================================*/
    const body = document.body;
    let currentRole = null;
    if (body.classList.contains("student-theme")) {
        currentRole = "student";
    }
    else if (body.classList.contains("teacher-theme")) {
        currentRole = "teacher";
    }
    else if (body.classList.contains("admin-theme")) {
        currentRole = "admin";
    }
    /*==========================================================
      ROLE CONFIGURATION
    ==========================================================*/
    const ROLE_CONFIG = {
        student: {
            profileEndpoint: "/student/profile",
            redirect: "../Student_dashboard/stu_dashboard.html"
        },
        teacher: {
            profileEndpoint: "/teacher/profile",
            redirect: "../Teacher_dashboard/tea-dashboard.html"
        },
        admin: {
            profileEndpoint: "/admin/profile",
            redirect: "../Admin_dashboard/dashboard.html"
        }
    };
    /*==========================================================
      VALIDATE ROLE
    ==========================================================*/
    if (!currentRole || !ROLE_CONFIG[currentRole]) {
        console.error("Unable to determine login role.");
        return;
    }
    const roleConfig = ROLE_CONFIG[currentRole];
    /*==========================================================
      ELEMENTS
    ==========================================================*/
    const loginForm = document.getElementById("loginForm");
    const rollNumber = document.getElementById("rollNumber");
    const password = document.getElementById("password");
    const loginBtn = document.getElementById("loginBtn");
    const eyeBtn = document.getElementById("togglePassword");
    const eyeIcon = eyeBtn?.querySelector("i");
    /*==========================================================
      SHOW / HIDE PASSWORD
    ==========================================================*/
    if (eyeBtn) {
        eyeBtn.addEventListener("click", () => {
            if (password.type === "password") {
                password.type = "text";
                eyeIcon.classList.remove("fa-eye");
                eyeIcon.classList.add("fa-eye-slash");
            }
            else {
                password.type = "password";
                eyeIcon.classList.remove("fa-eye-slash");
                eyeIcon.classList.add("fa-eye");
            }
        });
    }
    /*==========================================================
      ENTER KEY LOGIN
    ==========================================================*/
    document.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            if (
                document.activeElement === password ||
                document.activeElement === rollNumber
            ) {
                loginForm.requestSubmit();
            }
        }
    });
    /*==========================================================
      LOGIN
    ==========================================================*/
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        /*======================================================
          CLEAR PREVIOUS ERROR STATE
        ======================================================*/
        clearError();
        const identifier = rollNumber.value.trim();
        const pass = password.value.trim();
        /*======================================================
          EMPTY VALIDATION
        ======================================================*/
        if (identifier === "") {
            showError(
                currentRole === "student"
                    ? "Please enter your Roll Number / ID."
                    : "Please enter your Username / ID."
            );
            shake(rollNumber);
            rollNumber.focus();
            return;
        }
        if (pass === "") {
            showError("Please enter your Password.");
            shake(password);
            password.focus();
            return;
        }
        /*======================================================
          LOADING STATE
        ======================================================*/
        loginBtn.disabled = true;
        loginBtn.innerHTML = `
            <i class="fa-solid fa-spinner fa-spin"></i>
            Signing In...
        `;
        try {
            /*==================================================
              STEP 1
              AUTHENTICATE AGAINST FASTAPI
            ==================================================*/
            const loginResponse = await fetch(
                `${API_BASE_URL}/auth/login`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        identifier: identifier,
                        password: pass
                    })
                }
            );
            /*==================================================
              READ RESPONSE
            ==================================================*/
            let loginData = {};
            try {
                loginData = await loginResponse.json();
            }
            catch {
                loginData = {};
            }
            /*==================================================
              LOGIN FAILED
            ==================================================*/
            if (!loginResponse.ok) {
                /*
                ------------------------------------------------
                Backend returns:
                {
                    "detail": "Invalid username/email or password"
                }
                ------------------------------------------------
                */
                let message =
                    loginData.detail ||
                    "Invalid username/email or password.";
                /*
                ------------------------------------------------
                Convert technical/backend errors into a
                user-friendly login message.
                ------------------------------------------------
                */
                if (
                    loginResponse.status === 401 ||
                    loginResponse.status === 403
                ) {
                    message =
                        "Invalid username/email or password.";
                }
                else if (
                    loginResponse.status === 422
                ) {
                    message =
                        "Please check your login information.";
                }
                else if (
                    loginResponse.status >= 500
                ) {
                    message =
                        "Server error. Please try again later.";
                }
                throw new Error(message);
            }
            /*==================================================
              VERIFY TOKEN
            ==================================================*/
            if (!loginData.access_token) {
                throw new Error(
                    "Login succeeded but no access token was returned."
                );
            }
            /*==================================================
              SAVE TOKEN
            ==================================================*/
            localStorage.setItem(
                "access_token",
                loginData.access_token
            );
            localStorage.setItem(
                "token_type",
                loginData.token_type || "bearer"
            );
            /*==================================================
              STEP 2
              GET REAL ROLE PROFILE
            ==================================================*/
            const profileResponse = await fetch(
                `${API_BASE_URL}${roleConfig.profileEndpoint}`,
                {
                    method: "GET",
                    headers: {
                        "Authorization":
                            `Bearer ${loginData.access_token}`,
                        "Accept":
                            "application/json"
                    }
                }
            );
            let profileData = {};
            try {
                profileData = await profileResponse.json();
            }
            catch {
                profileData = {};
            }
            /*==================================================
              PROFILE FAILED
            ==================================================*/
            if (!profileResponse.ok) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("token_type");
                throw new Error(
                    profileData.detail ||
                    "Unable to load your profile."
                );
            }
            /*==================================================
              ROLE VALIDATION
            ==================================================*/
            if (
                profileData.role &&
                profileData.role !== currentRole
            ) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("token_type");
                throw new Error(
                    `This account is not registered as a ${currentRole}.`
                );
            }
            /*==================================================
              SAVE REAL PROFILE DATA
            ==================================================*/
            localStorage.setItem(
                `${currentRole}_profile`,
                JSON.stringify(profileData)
            );
            /*==================================================
              SAVE LOGIN ROLE
            ==================================================*/
            localStorage.setItem(
                "user_role",
                currentRole
            );
            /*==================================================
              SUCCESS UI
            ==================================================*/
            loginBtn.innerHTML = `
                <i class="fa-solid fa-circle-check"></i>
                Login Successful
            `;
            /*==================================================
              REDIRECT
            ==================================================*/
            setTimeout(() => {
                window.location.href =
                    roleConfig.redirect;
            }, 700);
        }
        catch (error) {
            console.error(
                `${currentRole} Login Error:`,
                error
            );
            /*==================================================
              RESET BUTTON
            ==================================================*/
            loginBtn.disabled = false;
            loginBtn.innerHTML = `
                <i class="fa-solid fa-arrow-right-to-bracket"></i>
                Sign In as ${capitalize(currentRole)}
            `;
            /*==================================================
              SHOW USER-FRIENDLY ERROR
            ==================================================*/
            const isNetworkError =
                error instanceof TypeError &&
                /fetch|network/i.test(error.message || "");
            showError(
                isNetworkError
                    ? `Cannot reach the API at ${API_BASE_URL}. Check that the backend is running and this site is allowed by CORS.`
                    : (error.message || "Login failed. Please try again.")
            );
            /*==================================================
              SHAKE BOTH FIELDS
            ==================================================*/
            shake(rollNumber);
            shake(password);
        }
    });
    /*==========================================================
      SHOW ERROR
    ==========================================================*/
    function showError(message) {
        clearError();
        const errorBox = document.createElement("div");
        errorBox.id = "loginError";
        errorBox.className = "login-error";
        errorBox.innerHTML = `
            <i class="fa-solid fa-circle-exclamation"></i>
            <span>${escapeHTML(message)}</span>
        `;
        loginForm.prepend(errorBox);
        /*
        --------------------------------------------------------
        Highlight input fields
        --------------------------------------------------------
        */
        rollNumber.classList.add("input-error");
        password.classList.add("input-error");
        /*
        --------------------------------------------------------
        Auto remove after 4 seconds
        --------------------------------------------------------
        */
        setTimeout(() => {
            if (errorBox) {
                errorBox.classList.add("hide");
            }
            rollNumber.classList.remove("input-error");
            password.classList.remove("input-error");
        }, 4000);
    }
    /*==========================================================
      CLEAR ERROR
    ==========================================================*/
    function clearError() {
        const existingError =
            document.getElementById("loginError");
        if (existingError) {
            existingError.remove();
        }
        rollNumber.classList.remove("input-error");
        password.classList.remove("input-error");
    }
    /*==========================================================
      SHAKE EFFECT
    ==========================================================*/
    function shake(element) {
        if (!element || !element.parentElement) {
            return;
        }
        element.parentElement.animate(
            [
                { transform: "translateX(0)" },
                { transform: "translateX(-8px)" },
                { transform: "translateX(8px)" },
                { transform: "translateX(-6px)" },
                { transform: "translateX(6px)" },
                { transform: "translateX(0)" }
            ],
            {
                duration: 400
            }
        );
    }
    /*==========================================================
      ESCAPE HTML
    ==========================================================*/
    function escapeHTML(value) {
        const div = document.createElement("div");
        div.textContent = value;
        return div.innerHTML;
    }
    /*==========================================================
      CAPITALIZE
    ==========================================================*/
    function capitalize(value) {
        if (!value) {
            return "";
        }
        return value.charAt(0).toUpperCase() +
               value.slice(1);
    }
});
