/* Real schedule rendering for the authenticated teacher. */
(function () {
  "use strict";

  const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function displayTime(value) {
    const [hour, minute] = value.split(":").map(Number);
    const suffix = hour >= 12 ? "PM" : "AM";
    const twelveHour = hour % 12 || 12;
    return `${twelveHour}:${String(minute).padStart(2, "0")} ${suffix}`;
  }

  function mondayOfCurrentWeek() {
    const current = new Date();
    const day = current.getDay() || 7;
    current.setDate(current.getDate() - day + 1);
    current.setHours(0, 0, 0, 0);
    return current;
  }

  function renderTimetable(schedules) {
    const table = document.querySelector(".timetable");
    if (!table) return;

    const weekStart = mondayOfCurrentWeek();
    const range = document.querySelector("#currentWeekRange");
    if (range) {
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);
      const formatDate = (date) => `${String(date.getDate()).padStart(2, "0")} ${date.toLocaleString("en-US", { month: "short" })} ${date.getFullYear()}`;
      range.textContent = `${formatDate(weekStart)} - ${formatDate(weekEnd)}`;
    }
    const headerCells = DAYS.map((_, index) => {
      const date = new Date(weekStart);
      date.setDate(weekStart.getDate() + index);
      return `<th>${DAY_SHORT[index]}<br><small>${String(date.getDate()).padStart(2, "0")} ${date.toLocaleString("en-US", { month: "short" })}</small></th>`;
    }).join("");
    table.querySelector("thead").innerHTML = `<tr><th class="time-col">Time</th>${headerCells}</tr>`;

    const slots = [...new Set(schedules.map((item) => `${item.start_time}|${item.end_time}`))]
      .sort((left, right) => left.localeCompare(right));
    const body = table.querySelector("tbody");
    if (!slots.length) {
      body.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">No timetable entries have been created.</td></tr>';
      return;
    }

    body.innerHTML = slots.map((slot, rowIndex) => {
      const [startTime, endTime] = slot.split("|");
      const cells = DAYS.map((day) => {
        const item = schedules.find((schedule) =>
          schedule.day_of_week === day &&
          schedule.start_time === startTime &&
          schedule.end_time === endTime
        );
        if (!item) return "<td></td>";
        const colorClass = ["block-blue", "block-green", "block-orange", "block-purple"][rowIndex % 4];
        return `<td><div class="schedule-block ${colorClass}" data-schedule-id="${item.schedule_id}">
          <strong>${escapeHtml(item.course_code)}</strong>
          <span>${escapeHtml(item.course_title)}</span>
          <small>${escapeHtml(item.room_location)}</small>
        </div></td>`;
      }).join("");
      return `<tr><td class="time-cell">${displayTime(startTime)}<br>${displayTime(endTime)}</td>${cells}</tr>`;
    }).join("");

    body.querySelectorAll(".schedule-block").forEach((block) => {
      const schedule = schedules.find((item) => String(item.schedule_id) === block.dataset.scheduleId);
      block.addEventListener("click", () => {
        window.openClassModal(
          `${schedule.course_code} ${schedule.course_title}`,
          `${displayTime(schedule.start_time)} - ${displayTime(schedule.end_time)}`,
          schedule.room_location
        );
      });
    });
  }

  function renderScheduleTable(schedules) {
    const tbody = document.querySelector("#scheduledClassesTable tbody");
    if (!tbody) return;
    if (!schedules.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No scheduled classes found.</td></tr>';
      return;
    }

    tbody.innerHTML = schedules.map((item, index) => {
      const color = ["var(--primary)", "var(--success)", "var(--warning)", "var(--purple)"][index % 4];
      return `<tr>
        <td><div class="course-title-cell"><div class="course-indicator" style="background-color:${color};"></div><div>
          <strong>${escapeHtml(item.course_code)} ${escapeHtml(item.course_title)}</strong><span>${escapeHtml(item.academic_year)} · Semester ${item.semester}</span>
        </div></div></td>
        <td><strong>${escapeHtml(item.section)}</strong></td>
        <td>${escapeHtml(item.class_type)}</td>
        <td><strong>${escapeHtml(item.day_of_week)}</strong><br><small style="color:var(--text-muted)">${displayTime(item.start_time)} - ${displayTime(item.end_time)}</small></td>
        <td>${escapeHtml(item.room_location)}</td>
        <td>${item.enrolled_student_count}</td>
        <td><button class="icon-btn-sm schedule-view" data-schedule-id="${item.schedule_id}" title="View Details"><i class="fa-regular fa-eye"></i></button></td>
      </tr>`;
    }).join("");

    tbody.querySelectorAll(".schedule-view").forEach((button) => {
      const schedule = schedules.find((item) => String(item.schedule_id) === button.dataset.scheduleId);
      button.addEventListener("click", () => {
        window.openClassModal(
          `${schedule.course_code} ${schedule.course_title}`,
          `${displayTime(schedule.start_time)} - ${displayTime(schedule.end_time)}`,
          schedule.room_location
        );
      });
    });
  }

  function renderUpcomingClasses(schedules) {
    const list = document.querySelector(".upcoming-list");
    if (!list) return;
    const today = DAYS[(new Date().getDay() + 6) % 7];
    const todaySchedules = schedules.filter((item) => item.day_of_week === today);
    if (!todaySchedules.length) {
      list.innerHTML = '<p style="padding:12px; color:var(--text-muted); font-size:0.8rem;">No scheduled classes today.</p>';
      return;
    }
    list.innerHTML = todaySchedules.map((item, index) => `<div class="upcoming-item ${["", "green", "orange", "purple"][index % 4]}">
      <div class="upcoming-left"><h4>${escapeHtml(item.course_title)} (${escapeHtml(item.course_code)})</h4>
        <p>Section ${escapeHtml(item.section)} | ${escapeHtml(item.class_type)} &bull; ${escapeHtml(item.room_location)}</p></div>
      <div class="upcoming-time">${displayTime(item.start_time)}<br><small style="color:var(--text-muted); font-weight:normal;">${displayTime(item.end_time)}</small></div>
    </div>`).join("");
  }

  function updateMetrics(metrics) {
    document.querySelectorAll(".stat-card").forEach((card) => {
      const label = card.querySelector("p")?.textContent.trim();
      const value = card.querySelector("h3");
      if (!value) return;
      if (label === "Classes This Week") value.textContent = metrics.classes_per_week;
      if (label === "Students This Week") value.textContent = metrics.unique_enrolled_students;
      if (label === "Teaching Hours") {
        const hours = Math.floor(metrics.teaching_minutes / 60);
        value.textContent = `${hours}h ${metrics.teaching_minutes % 60}m`;
      }
      if (label === "Rooms/Labs") value.textContent = metrics.room_count;
      if (label === "Cancelled Classes") value.textContent = "0";
    });
  }

  function populateTermFilter(schedules) {
    const select = document.querySelector("#scheduleTermFilter");
    if (!select) return;
    const terms = [...new Map(schedules.map((item) => {
      const key = `${item.academic_year}:${item.semester}`;
      return [key, { key, label: `${item.academic_year} · Semester ${item.semester}` }];
    })).values()].sort((left, right) => right.key.localeCompare(left.key));
    const previous = select.value;
    select.innerHTML = terms.length
      ? terms.map((term) => `<option value="${escapeHtml(term.key)}">${escapeHtml(term.label)}</option>`).join("")
      : '<option value="">No academic term</option>';
    if (terms.some((term) => term.key === previous)) select.value = previous;
    if (terms.length && !select.value) select.value = terms[0].key;
  }

  async function loadSchedule() {
    const accessToken = localStorage.getItem("access_token");
    const tableBody = document.querySelector("#scheduledClassesTable tbody");
    const timetableBody = document.querySelector(".timetable tbody");
    if (tableBody) tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">Loading scheduled classes...</td></tr>';
    if (timetableBody) timetableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">Loading timetable...</td></tr>';
    if (!accessToken) {
      if (tableBody) tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--danger);">Please sign in to load scheduled classes.</td></tr>';
      if (timetableBody) timetableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--danger);">Please sign in to load timetable.</td></tr>';
      return;
    }
    const response = await fetch(`${API_BASE_URL}/teacher/schedule`, {
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" }
    });
    if (!response.ok) {
      if (tableBody) tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--danger);">Unable to load scheduled classes.</td></tr>';
      if (timetableBody) timetableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--danger);">Unable to load timetable.</td></tr>';
      return;
    }
    const data = await response.json();
    const schedules = data.schedules || [];
    populateTermFilter(schedules);
    const termFilter = document.querySelector("#scheduleTermFilter");
    const renderSelectedTerm = () => {
      const selectedTerm = termFilter?.value;
      const visibleSchedules = selectedTerm
        ? schedules.filter((item) => `${item.academic_year}:${item.semester}` === selectedTerm)
        : schedules;
      renderTimetable(visibleSchedules);
      renderUpcomingClasses(visibleSchedules);
      updateMetrics((data.term_metrics || {})[selectedTerm] || data.metrics || {});
    };
    if (termFilter) termFilter.onchange = renderSelectedTerm;
    renderSelectedTerm();
    renderScheduleTable(schedules);
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadSchedule().catch(() => {
      // teacher-auth.js owns session validation and redirect behavior.
    });
  });
  const refresh = () => loadSchedule().catch(error => console.error('Timetable refresh failed', error));
  window.addEventListener('storage', event => { if (event.key === 'timetable-updated') refresh(); });
  window.addEventListener('focus', refresh);
  setInterval(() => { if (!document.hidden) refresh(); }, 30000);
})();
