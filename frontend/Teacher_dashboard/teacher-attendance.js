/* Real, JWT-scoped attendance binding for the existing teacher attendance UI. */
(function () {
  "use strict";
  const API = window.ACOS_CONFIG.API_BASE_URL;
  let classes = [];
  let roster = [];
  let activeFilter = "all";
  const token = () => localStorage.getItem("access_token");
  const headers = () => ({ Authorization: `Bearer ${token()}` });
  const escapeHtml = (value) => String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  const statusMap = { P: "Present", A: "Absent", L: "Late", E: "Leave" };
  const statusCode = (value) => ({ Present: "P", Absent: "A", Late: "L", Leave: "E" }[value] || "");

  function selectedClass() { return classes.find((item) => String(item.schedule_id) === document.getElementById("timeFilterSelect").value); }
  function visibleRoster() {
    const search = document.getElementById("studentSearchInput").value.trim().toLowerCase();
    return roster.filter((student) => (!search || student.name.toLowerCase().includes(search) || student.roll_number.toLowerCase().includes(search)) && (activeFilter === "all" || statusCode(student.status) === activeFilter));
  }
  function setMessage(message) { document.getElementById("showingText").textContent = message; }
  function render() {
    const body = document.getElementById("attendanceTableBody");
    const data = visibleRoster();
    body.innerHTML = data.length ? data.map((student, index) => {
      const code = statusCode(student.status);
      return `<tr class="student-row"><td>${index + 1}</td><td><strong>${escapeHtml(student.roll_number)}</strong></td><td>${escapeHtml(student.name)}</td><td><div class="status-options-group">${["P", "A", "L", "E"].map((value) => `<span class="status-radio-btn ${value.toLowerCase()}-btn ${code === value ? "selected" : ""}" onclick="setStudentStatus(${student.student_id}, '${value}')">${value}</span>`).join("")}</div></td><td><div class="remarks-input-wrap"><input type="text" class="remarks-input" value="${escapeHtml(student.remarks || "")}" placeholder="—" onchange="updateRemark(${student.student_id}, this.value)"></div></td></tr>`;
    }).join("") : '<tr><td colspan="5" style="text-align:center; padding:24px; color:var(--text-muted);">No currently enrolled students for this class.</td></tr>';
    document.getElementById("totalStudentsCount").textContent = roster.length;
    setMessage(`Showing ${data.length} of ${roster.length} students`);
    const counts = { P: 0, A: 0, L: 0, E: 0 };
    roster.forEach((student) => { const code = statusCode(student.status); if (code) counts[code] += 1; });
    const total = roster.length || 1;
    ["P", "A", "L", "E"].forEach((code) => { document.getElementById(`count${code}`).textContent = counts[code]; document.getElementById(`percent${code}`).textContent = `${((counts[code] / total) * 100).toFixed(1)}%`; });
  }
  function resetSelect(select, items, value, label) { select.innerHTML = items.map((item) => `<option value="${escapeHtml(value(item))}">${escapeHtml(label(item))}</option>`).join(""); }
  function syncClassSelectors() {
    const course = document.getElementById("courseFilterSelect");
    const section = document.getElementById("sectionFilterSelect");
    const time = document.getElementById("timeFilterSelect");
    const chosenCourse = course.value;
    const courseClasses = classes.filter((item) => String(item.course_id) === chosenCourse);
    const sections = [...new Map(courseClasses.map((item) => [`${item.academic_year}|${item.semester}|${item.section}`, item])).values()];
    resetSelect(section, sections, (item) => `${item.academic_year}|${item.semester}|${item.section}`, (item) => `Section ${item.section} — Semester ${item.semester} (${item.academic_year})`);
    const [year, semester, selectedSection] = section.value.split("|");
    const times = courseClasses.filter((item) => item.academic_year === year && String(item.semester) === semester && item.section === selectedSection);
    resetSelect(time, times, (item) => item.schedule_id, (item) => `${item.day_of_week} ${item.start_time} - ${item.end_time}`);
  }
  async function loadRoster() {
    const chosen = selectedClass();
    if (!chosen) { roster = []; render(); return; }
    const date = document.getElementById("attendanceDatePicker").value;
    const response = await fetch(`${API}/teacher/attendance/roster?schedule_id=${chosen.schedule_id}&attendance_date=${encodeURIComponent(date)}`, { headers: headers() });
    const data = await response.json();
    if (!response.ok) { roster = []; render(); alert(data.detail || "Could not load attendance roster."); return; }
    roster = data.roster;
    render();
  }
  async function loadClasses() {
    const response = await fetch(`${API}/teacher/attendance/courses`, { headers: headers() });
    const data = await response.json();
    if (!response.ok) { alert(data.detail || "Could not load your classes."); return; }
    classes = data.classes || [];
    const courseSelect = document.getElementById("courseFilterSelect");
    const courses = [...new Map(classes.map((item) => [item.course_id, item])).values()];
    resetSelect(courseSelect, courses, (item) => item.course_id, (item) => `${item.course_code} ${item.course_title} (Semester ${item.semester})`);
    const countEl = document.getElementById("overviewCoursesCount");
    if (countEl) countEl.textContent = courses.length;
    syncClassSelectors();
    await loadRoster();
  }

  // Attendance History Functions
  window.openAttendanceHistoryModal = async function () {
    const modal = document.getElementById("attendanceHistoryModal");
    if (!modal) return;
    modal.classList.add("active");
    const tbody = document.getElementById("attendanceHistoryTableBody");
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="margin-right:6px;"></i>Loading attendance history...</td></tr>';

    try {
      const response = await fetch(`${API}/teacher/attendance`, { headers: headers() });
      const data = await response.json();
      if (!response.ok) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--danger);">${escapeHtml(data.detail || "Failed to load history.")}</td></tr>`;
        return;
      }
      const records = data.records || [];
      if (!records.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--text-muted);">No attendance records found yet.</td></tr>';
        return;
      }
      tbody.innerHTML = records.map((r) => {
        const badgeColor = r.status === "Present" ? "var(--success)" : r.status === "Absent" ? "var(--danger)" : r.status === "Late" ? "var(--warning)" : "var(--info)";
        return `<tr>
          <td><strong>${escapeHtml(r.attendance_date)}</strong></td>
          <td>${escapeHtml(r.course_code)}</td>
          <td><strong>${escapeHtml(r.roll_number)}</strong></td>
          <td>${escapeHtml(r.student_name)}</td>
          <td><span style="font-weight:700; color:${badgeColor};">${escapeHtml(r.status)}</span></td>
          <td>${escapeHtml(r.remarks || "—")}</td>
        </tr>`;
      }).join("");
    } catch (err) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--danger);">Error fetching history data.</td></tr>';
    }
  };

  window.closeAttendanceHistoryModal = function () {
    const modal = document.getElementById("attendanceHistoryModal");
    if (modal) modal.classList.remove("active");
  };

  window.handleFilterChange = async function () { syncClassSelectors(); await loadRoster(); };
  window.setStudentStatus = function (studentId, code) { const student = roster.find((item) => item.student_id === studentId); if (student) { student.status = statusMap[code]; render(); } };
  window.updateRemark = function (studentId, value) { const student = roster.find((item) => item.student_id === studentId); if (student) student.remarks = value; };
  window.markAllStatus = function (code) { roster.forEach((student) => { student.status = statusMap[code]; }); render(); };
  window.clearAllStatus = function () { roster.forEach((student) => { student.status = ""; student.remarks = ""; }); render(); };
  window.filterStudents = render;
  window.filterByStatus = function (code) { activeFilter = code; document.querySelectorAll(".filter-pill").forEach((pill) => pill.classList.toggle("active", pill.textContent.trim().toLowerCase().includes(code === "all" ? "all" : ({ P: "present", A: "absent", L: "late", E: "leave" }[code])))); render(); };
  window.saveAttendance = async function () {
    if (!roster.length || roster.some((student) => !student.status)) { alert("Please mark a status for every enrolled student before saving."); return; }
    const chosen = selectedClass();
    const response = await fetch(`${API}/teacher/attendance`, { method: "POST", headers: { ...headers(), "Content-Type": "application/json" }, body: JSON.stringify({ schedule_id: chosen.schedule_id, attendance_date: document.getElementById("attendanceDatePicker").value, records: roster.map((student) => ({ student_id: student.student_id, status: student.status, remarks: student.remarks || null })) }) });
    const data = await response.json();
    if (!response.ok) { alert(data.detail || "Attendance could not be saved."); return; }
    alert(`Attendance saved for ${data.records_saved} students.`);
    await loadRoster();
  };
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("attendanceDatePicker").value = new Date().toISOString().slice(0, 10);
    document.getElementById("courseFilterSelect").addEventListener("change", () => window.handleFilterChange());
    document.getElementById("sectionFilterSelect").addEventListener("change", () => window.handleFilterChange());
    document.getElementById("timeFilterSelect").addEventListener("change", loadRoster);
    loadClasses().catch(() => { roster = []; render(); });
  });
})();
