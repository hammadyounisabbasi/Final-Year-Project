/*
===========================================================
  Zero-Trust Autonomous Campus Ecosystem
  Shared Student Topbar Hydration Utility
  
  This script reads the logged-in student's real profile from
  localStorage (stored by login.js after /student/profile call)
  and injects it into the topbar on every Student Dashboard page.
  
  Usage: include <script src="../shared/student-topbar.js"></script>
  at the END of every Student Dashboard HTML page's <body>.
  
  Required topbar IDs (optional - falls back to class selectors):
    id="topbarUserName"    → student's full name
    id="topbarUserRole"    → program + semester
    id="topbarUserAvatar"  → avatar img src
    id="topbarRollNumber"  → roll number (if present)
===========================================================
*/

(function () {
    const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;

    function injectProfileIntoTopbar(profile) {
        if (!profile) return;

        const fullName = (profile.first_name || "") + " " + (profile.last_name || "");
        const displayName = profile.name || fullName.trim() || profile.full_name || "Student";
        const program = profile.program || "BS Computer Science";
        const semester = profile.semester || profile.current_semester || "";
        const rollNumber = profile.roll_number || profile.roll_no || "";
        const photo = profile.profile_photo || "";

        // Role/program label
        const roleLabel = semester ? `${program} — Semester ${semester}` : program;

        // Try IDs first, then class selectors
        const nameEl = document.getElementById("topbarUserName") || document.getElementById("profileName") || document.querySelector(".user-name");
        const roleEl = document.getElementById("topbarUserRole") || document.getElementById("profileProgram") || document.querySelector(".user-role");
        const avatarEl = document.getElementById("topbarUserAvatar") || document.querySelector(".user-avatar");
        const rollEl = document.getElementById("topbarRollNumber");

        if (nameEl) nameEl.textContent = displayName;
        if (roleEl) roleEl.textContent = roleLabel;
        if (rollEl) rollEl.textContent = rollNumber;
        if (avatarEl && photo) {
            avatarEl.src = photo;
            avatarEl.alt = displayName;
        }

        // Also update sidebar student info blocks (common pattern in dashboards)
        document.querySelectorAll(".sidebar-student-name, .profile-name, #sidebarStudentName").forEach(el => {
            el.textContent = displayName;
        });
        document.querySelectorAll(".sidebar-student-roll, #sidebarStudentRoll").forEach(el => {
            el.textContent = rollNumber;
        });

        console.log("[StudentTopbar] Injected:", displayName, rollNumber, roleLabel);
    }

    async function loadAndInjectProfile() {
        // 1. Try localStorage cached profile first (fastest - set by login.js)
        const cachedProfile = localStorage.getItem("student_profile");
        if (cachedProfile) {
            try {
                const profile = JSON.parse(cachedProfile);
                injectProfileIntoTopbar(profile);
                return; // Done immediately
            } catch (e) {
                console.warn("[StudentTopbar] Cached profile parse error:", e);
            }
        }

        // 2. No cache - try fetching from backend
        const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
        if (!token) {
            // No token - redirect to login
            window.location.href = "../login_page/student-login.html";
            return;
        }

        try {
            const resp = await fetch(`${API_BASE_URL}/student/profile`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Accept": "application/json"
                }
            });

            if (!resp.ok) {
                if (resp.status === 401 || resp.status === 403) {
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("student_profile");
                    window.location.href = "../login_page/student-login.html";
                    return;
                }
                throw new Error(`HTTP ${resp.status}`);
            }

            const profile = await resp.json();
            // Cache it for other pages
            localStorage.setItem("student_profile", JSON.stringify(profile));
            injectProfileIntoTopbar(profile);

        } catch (err) {
            console.error("[StudentTopbar] Failed to load profile:", err);
        }
    }

    // Run as soon as DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", loadAndInjectProfile);
    } else {
        loadAndInjectProfile();
    }

    // Expose globally so pages can call it manually if needed
    window.StudentTopbar = { reload: loadAndInjectProfile };
})();
