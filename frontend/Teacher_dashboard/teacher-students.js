/* Real roster binding for the authenticated teacher. */
(function () {
  "use strict";

  const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;

  function replaceOptions(select, options, allLabel) {
    select.innerHTML = `<option value="ALL">${allLabel}</option>`;
    options.forEach(({ value, label }) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      select.appendChild(option);
    });
  }

  function configureFilters(data) {
    replaceOptions(
      document.getElementById("courseFilter"),
      data.available_courses.map((course) => ({
        value: String(course.course_id),
        label: `${course.course_code} ${course.course_title}`
      })),
      "All Courses"
    );

    const sections = [...new Set(
      data.students.flatMap((student) => student.enrollments.map(
        (enrollment) => enrollment.section || "Unassigned"
      ))
    )].sort();
    replaceOptions(
      document.getElementById("sectionFilter"),
      sections.map((section) => ({ value: section, label: `Section ${section}` })),
      "All Sections"
    );

    const statuses = [...new Set(data.students.map((student) => student.status))].sort();
    replaceOptions(
      document.getElementById("statusFilter"),
      statuses.map((status) => ({ value: status, label: status })),
      "All Status"
    );
  }

  function toDashboardStudent(student) {
    return {
      ...student,
      roll: student.roll_number,
      section: student.student_section || "Unassigned",
      semester: `Semester ${student.student_semester}`,
      gpa: student.cgpa === null ? "—" : Number(student.cgpa).toFixed(2),
      attendance: "Not recorded"
    };
  }

  async function loadStudents() {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) return;

    const response = await fetch(`${API_BASE_URL}/teacher/students`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json"
      }
    });
    if (!response.ok) return;

    const data = await response.json();
    configureFilters(data);
    window.setTeacherStudents(
      data.students.map(toDashboardStudent),
      data.metrics
    );
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadStudents().catch(() => {
      // teacher-auth.js owns session validation and redirect behavior.
    });
  });
})();
