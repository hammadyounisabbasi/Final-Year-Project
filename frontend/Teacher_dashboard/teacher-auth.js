/* Teacher dashboard session and profile binding. */
(function () {
  "use strict";

  const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;
  const LOGIN_PAGE = "../login_page/teacher-login.html";

  function clearTeacherSession() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("teacher_profile");
    localStorage.removeItem("user_role");
  }

  function redirectToLogin() {
    clearTeacherSession();
    window.location.replace(LOGIN_PAGE);
  }

  function bindProfile(profile) {
    const fullName = [profile.designation, profile.first_name, profile.last_name]
      .filter(Boolean)
      .join(" ");

    document.querySelectorAll(".sidebar-user h4").forEach((element) => {
      element.textContent = fullName;
    });

    document.querySelectorAll(".user-profile-pill span").forEach((element) => {
      element.textContent = fullName;
    });

    document.querySelectorAll(".user-profile-pill .profile-meta small").forEach((element) => {
      element.textContent = profile.designation || "Teacher";
    });

    document.querySelectorAll(".sidebar-user .user-info p").forEach((element) => {
      const designation = profile.designation || "Teacher";
      const department = profile.department?.department_name || "";
      element.replaceChildren(
        document.createTextNode(designation),
        document.createElement("br"),
        document.createTextNode(department)
      );
    });

    if (profile.profile_photo) {
      document.querySelectorAll(".sidebar-user img, .user-profile-pill img").forEach((image) => {
        image.src = profile.profile_photo;
        image.alt = fullName;
      });
    }

    document.querySelectorAll("h1").forEach((heading) => {
      if (heading.textContent.includes("Good Morning")) {
        heading.textContent = `Good Morning, ${fullName} 👋`;
      }
    });
  }

  async function loadAuthenticatedTeacher() {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
      redirectToLogin();
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/teacher/profile`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json"
        }
      });

      if (!response.ok) {
        redirectToLogin();
        return;
      }

      const profile = await response.json();
      localStorage.setItem("teacher_profile", JSON.stringify(profile));
      localStorage.setItem("user_role", "teacher");
      bindProfile(profile);
    } catch {
      redirectToLogin();
    }
  }

  function bindLogout() {
    document.querySelectorAll('[onclick*="logout.html"]').forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        redirectToLogin();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindLogout();
    loadAuthenticatedTeacher();
  });
})();
