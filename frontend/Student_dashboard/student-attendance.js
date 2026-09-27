/* Real attendance rendering for the existing student attendance UI. */
(function () {
  "use strict";
  const API = window.ACOS_CONFIG.API_BASE_URL;
  let historyChart;
  let donutChart;
  const legacyRenderCalendar = window.renderCalendar;
  const token = () => localStorage.getItem("access_token");
  const status = (percentage) => percentage >= 90 ? ["Excellent", "pill-excellent", "#10b981"] : percentage >= 75 ? ["Good", "pill-good", "#2563eb"] : percentage >= 65 ? ["At Risk", "pill-risk", "#f59e0b"] : ["Deficit", "pill-deficit", "#ef4444"];
  const escapeHtml = (value) => String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  function renderTable(courses) {
    const body = document.getElementById("courseTableBody");
    body.innerHTML = courses.length ? courses.map((course) => {
      const [label, css, color] = status(course.percentage);
      return `<tr><td><span class="course-code">${escapeHtml(course.course_code)}</span><span class="course-name">${escapeHtml(course.course_title)}</span></td><td>${escapeHtml(course.teacher)}</td><td>${course.total_classes}</td><td>${course.attended}</td><td style="min-width:100px;"><span style="font-weight:600;font-size:0.8rem;">${course.percentage}%</span><div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${course.percentage}%;background-color:${color};"></div></div></td><td><span class="status-pill ${css}">${label}</span></td><td style="font-weight:600;color:${color};">${course.present} P / ${course.absent} A</td></tr>`;
    }).join("") : '<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--text-muted);">No attendance has been marked for your enrolled courses yet.</td></tr>';
  }
  function renderCharts(summary, recent) {
    if (historyChart) historyChart.destroy();
    if (donutChart) donutChart.destroy();
    const dateGroups = new Map();
    recent.slice().reverse().forEach((record) => { const group = dateGroups.get(record.attendance_date) || { attended: 0, total: 0 }; group.total += 1; if (["Present", "Late"].includes(record.status)) group.attended += 1; dateGroups.set(record.attendance_date, group); });
    const labels = [...dateGroups.keys()].slice(-8);
    const values = labels.map((date) => { const item = dateGroups.get(date); return Math.round(item.attended * 100 / item.total); });
    historyChart = new Chart(document.getElementById("attendanceHistoryChart").getContext("2d"), { type: "line", data: { labels, datasets: [{ label: "Attendance %", data: values, borderColor: "#10b981", backgroundColor: "rgba(16,185,129,.08)", fill: true, tension: .3, pointRadius: 4, pointBackgroundColor: "#10b981" }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100, ticks: { stepSize: 25 } }, x: { grid: { display: false } } } } });
    donutChart = new Chart(document.getElementById("overviewDonutChart").getContext("2d"), { type: "doughnut", data: { labels: ["Present", "Late", "Absent", "Leave"], datasets: [{ data: [summary.present, summary.late, summary.absent, summary.leave], backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#8b5cf6"], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "75%", plugins: { legend: { position: "right", labels: { boxWidth: 10, font: { size: 11 } } } } } });
  }
  function renderCalendar(recent) {
    const marked = new Set(recent.map((record) => record.attendance_date));
    const grid = document.getElementById("calendarGrid");
    if (typeof legacyRenderCalendar === "function") legacyRenderCalendar();
    grid.querySelectorAll(".cal-date").forEach((cell) => { const month = String(currentDate.getMonth() + 1).padStart(2, "0"); const date = `${currentDate.getFullYear()}-${month}-${String(cell.textContent).padStart(2, "0")}`; cell.classList.toggle("active", marked.has(date)); });
  }
  async function load() {
    const response = await fetch(`${API}/student/attendance`, { headers: { Authorization: `Bearer ${token()}` } });
    const data = await response.json();
    if (!response.ok) { alert(data.detail || "Could not load attendance."); return; }
    const overallEl = document.getElementById("overallPercVal");
    if (overallEl) overallEl.textContent = summary.total_classes ? `${summary.percentage}%` : "0%";
    document.getElementById("classesAttendedVal").textContent = summary.attended;
    document.getElementById("classesMissedVal").textContent = summary.absent;
    document.getElementById("attendanceStatusVal").textContent = summary.total_classes ? `${summary.percentage}%` : "No Data";
    const badges = document.querySelectorAll(".stat-card .badge");
    if (badges[0]) badges[0].textContent = summary.total_classes ? (summary.percentage >= 75 ? "Good Standing" : "Needs Improvement") : "No Classes Yet";
    if (badges[1]) badges[1].textContent = `Out of ${summary.total_classes}`;
    if (badges[2]) badges[2].textContent = summary.total_classes ? "Recorded Classes" : "No Classes Marked";
    if (badges[3]) badges[3].textContent = summary.total_classes ? (summary.percentage >= 75 ? "Above Minimum (75%)" : "Below Minimum (75%)") : "Awaiting Attendance";
    renderTable(data.courses);
    renderCharts(summary, data.recent);
    renderCalendar(data.recent);
    window.renderCalendar = () => renderCalendar(data.recent);
  }
  document.addEventListener("DOMContentLoaded", () => load().catch(() => {}));
})();
