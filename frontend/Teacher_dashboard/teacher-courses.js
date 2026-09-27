/* Real course data binding for My Courses. */
(function () {
  "use strict";

  const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function courseIcon(index) {
    const colors = ["var(--primary)", "var(--success)", "var(--warning)", "var(--purple)"];
    const icons = ["fa-code", "fa-book-open", "fa-flask", "fa-graduation-cap"];
    return { color: colors[index % colors.length], icon: icons[index % icons.length] };
  }

  function groupedScheduleMarkup(schedules) {
    const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    const groups = new Map();
    schedules.forEach((item) => {
      const key = [item.academic_year, item.semester, item.section, item.start_time, item.end_time, item.room_location, item.class_type].join("|");
      if (!groups.has(key)) groups.set(key, { ...item, days: [] });
      groups.get(key).days.push(item.day_of_week);
    });
    return [...groups.values()].sort((a, b) => `${b.academic_year}:${b.semester}`.localeCompare(`${a.academic_year}:${a.semester}`) || a.start_time.localeCompare(b.start_time)).map((item) => {
      const days = [...new Set(item.days)].sort((a, b) => dayOrder.indexOf(a) - dayOrder.indexOf(b)).map((day) => day.slice(0, 3)).join(" · ");
      return `<article class="schedule-session"><p class="schedule-term">${escapeHtml(item.academic_year)} · Semester ${escapeHtml(item.semester)} · Section ${escapeHtml(item.section)}</p><p class="schedule-time">${escapeHtml(days)} <span>·</span> ${displayTime(item.start_time)}–${displayTime(item.end_time)}</p><p class="schedule-room">${escapeHtml(item.room_location)} <span>· ${escapeHtml(item.class_type)}</span></p></article>`;
    }).join("");
  }

  function renderCourses(courses) {
    const tbody = document.querySelector("#coursesTable tbody");
    if (!tbody) return;

    if (!courses.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No assigned courses match the selected records.</td></tr>';
      return;
    }

    tbody.innerHTML = courses.map((course, index) => {
      const visual = courseIcon(index);
      const sections = course.sections.map((item) => item.section).join(", ") || "—";
      const schedules = course.schedules || [];
      let scheduleText = schedules.length
        ? schedules.map((item) => `<span style="display:block; margin-bottom:3px;"><small>${escapeHtml(item.academic_year)} · Sem ${escapeHtml(item.semester)} · Sec ${escapeHtml(item.section)}</small><br>${item.day_of_week.slice(0, 3)} ${displayTime(item.start_time)}-${displayTime(item.end_time)}<br>${escapeHtml(item.room_location)}</span>`).join("")
        : "Not configured<br><span>No timetable data available</span>";
      const program = course.department.department_short_name || course.department.department_code || "—";
      scheduleText = schedules.length
        ? `<div class="schedule-list">${groupedScheduleMarkup(schedules)}</div>`
        : '<div class="schedule-empty">Not configured<br><span>No timetable data available</span></div>';
      const status = course.status === "Active" ? "badge-active" : "badge-inactive";

      return `
        <tr>
          <td>
            <div class="course-cell">
              <div class="course-icon-bg" style="background-color: ${visual.color};">
                <i class="fa-solid ${visual.icon}"></i>
              </div>
              <div class="course-info">
                <h4>${escapeHtml(course.course_title)}</h4>
                <p>${escapeHtml(course.course_type)} · ${escapeHtml(course.credit_hours)} credit hours</p>
              </div>
            </div>
          </td>
          <td><strong>${escapeHtml(course.course_code)}</strong></td>
          <td>${escapeHtml(program)}</td>
          <td>${escapeHtml(sections)}</td>
          <td>${escapeHtml(course.enrolled_student_count)}</td>
          <td>
            <div class="schedule-info">${scheduleText}</div>
          </td>
          <td>
            <div class="action-btn-group">
              <button class="icon-btn-sm" title="View Course" onclick="viewCourseDetails('${escapeHtml(course.course_code)}')"><i class="fa-regular fa-eye"></i></button>
              <button class="icon-btn-sm" title="Options" onclick="openCourseOptions('${escapeHtml(course.course_code)}')"><i class="fa-solid fa-ellipsis-vertical"></i></button>
            </div>
          </td>
        </tr>`;
    }).join("");
  }

  function updateMetrics(metrics, courseCount) {
    document.querySelectorAll(".stat-card").forEach((card) => {
      const label = card.querySelector("p")?.textContent.trim();
      const value = card.querySelector("h3");
      if (!value) return;
      if (label === "Total Courses") value.textContent = String(metrics.course_count);
      if (label === "Total Students") value.textContent = String(metrics.unique_enrolled_student_count);
    });

    const footer = document.querySelector("#coursesTable")?.closest(".card")?.querySelector(".table-footer > span");
    if (footer) footer.textContent = `Showing ${courseCount} assigned course${courseCount === 1 ? "" : "s"}`;
  }

  async function loadCourses() {
    const accessToken = localStorage.getItem("access_token");
    const tbody = document.querySelector("#coursesTable tbody");
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">Loading assigned courses...</td></tr>';
    if (!accessToken) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--danger);">Please sign in to load assigned courses.</td></tr>';
      return;
    }

    const scheduleResponse = await fetch(`${API_BASE_URL}/teacher/schedule`, {
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" }
    });
    if (!scheduleResponse.ok) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--danger);">Unable to load the current timetable.</td></tr>';
      return;
    }
    const scheduleData = scheduleResponse.ok ? await scheduleResponse.json() : { schedules: [] };
    const currentYear = scheduleData.filters?.academic_year;
    const response = await fetch(`${API_BASE_URL}/teacher/courses${currentYear ? `?academic_year=${encodeURIComponent(currentYear)}` : ""}`, {
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" }
    });
    if (!response.ok) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--danger);">Unable to load assigned courses.</td></tr>';
      return;
    }
    const data = await response.json();
    const schedulesByCourse = (scheduleData.schedules || []).reduce((groups, schedule) => {
      const key = `${schedule.course_id}:${schedule.academic_year}:${schedule.semester}:${schedule.section}`;
      (groups[key] ||= []).push(schedule);
      return groups;
    }, {});
    const currentCourseIds = new Set((scheduleData.schedules || []).map((schedule) => schedule.course_id));
    const courses = (data.courses || []).filter((course) => currentCourseIds.has(course.course_id)).map((course) => ({
      ...course,
      schedules: Object.entries(schedulesByCourse)
        .filter(([key]) => key.split(":")[0] === String(course.course_id))
        .flatMap(([, items]) => items)
    }));
    renderCourses(courses);
    updateMetrics(data.metrics || {}, courses.length);
  }

  function displayTime(value) {
    const [hour, minute] = String(value || "").split(":").map(Number);
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) return "";
    return `${hour % 12 || 12}:${String(minute).padStart(2, "0")} ${hour >= 12 ? "PM" : "AM"}`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadCourses().catch(() => {
      // Session validation and redirect behavior remain owned by teacher-auth.js.
    });
  });
})();
