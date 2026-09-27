/* Student assignment data binding and inline-response submission. */
(function () {
  "use strict";
  const API = window.ACOS_CONFIG.API_BASE_URL;
  let realAssignments = [];
  const token = () => localStorage.getItem("access_token");

  function getFileUrl(path) {
    if (!path) return null;
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    const cleanPath = path.replace(/^[/\\]+/, "").replace(/\\/g, "/");
    return `${API}/${cleanPath}`;
  }

  function map(item) {
    const due = new Date(item.due_date);
    const submission = item.submission;
    const overdue = !submission && due < new Date();
    return {
      id: item.assignment_id,
      title: item.title,
      category: item.description || item.assignment_type || "Assignment",
      course: item.course_code,
      courseName: item.course_title,
      dueDate: due.toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      status: submission ? "submitted" : (overdue ? "overdue" : "pending"),
      statusText: submission ? (submission.submission_status || "Submitted") : (overdue ? "Overdue" : "Pending"),
      progress: submission ? "Submitted" : "Not submitted",
      grade: (submission && submission.teacher_marks !== null && submission.teacher_marks !== undefined) ? `${submission.teacher_marks} Marks` : "—",
      teacherFeedback: submission ? submission.teacher_feedback : null,
      attachmentPath: getFileUrl(item.attachment_path),
      attachmentName: item.attachment_name || (item.attachment_path ? "Reference Material" : null),
      submissionFileName: submission ? submission.file_name : null,
      submissionFilePath: submission ? getFileUrl(submission.file_path) : null,
      submissionAttempt: submission ? submission.submission_attempt : 0,
      icon: "fa-file-lines",
      iconBg: "#eff6ff",
      iconColor: "#2563eb"
    };
  }

  async function load() {
    try {
      const response = await fetch(`${API}/student/assignments`, { headers: { Authorization: `Bearer ${token()}` } });
      if (!response.ok) return;
      const data = await response.json();
      realAssignments = data.assignments || [];
      assignments = realAssignments.map(map);
      
      const select = document.getElementById("courseFilter");
      if (select) {
        select.innerHTML = '<option value="all">All Courses</option>';
        [...new Set(assignments.map(a => a.course))].forEach(code => select.add(new Option(code, code)));
      }
      
      const countTotal = document.getElementById("countTotal");
      const countSubmitted = document.getElementById("countSubmitted");
      const countPending = document.getElementById("countPending");
      const countOverdue = document.getElementById("countOverdue");
      
      if (countTotal) countTotal.textContent = assignments.length;
      if (countSubmitted) countSubmitted.textContent = assignments.filter(a => a.status === "submitted").length;
      if (countPending) countPending.textContent = assignments.filter(a => a.status === "pending").length;
      if (countOverdue) countOverdue.textContent = assignments.filter(a => a.status === "overdue").length;
      
      renderAssignmentsTable();
      renderDeadlines();
      renderRecentSubmissions();
    } catch (e) {
      console.error("Error loading student assignments:", e);
    }
  }

  window.openUploadModal = function (preferredId) {
    if (!realAssignments || realAssignments.length === 0) {
      modalTitle.innerText = "Submit Assignment";
      modalBody.innerHTML = '<p style="color:var(--text-muted); padding:10px;">No assignments currently active.</p>';
      modal.style.display = "flex";
      return;
    }

    modalTitle.innerText = preferredId ? "Submit Assignment / Re-attempt" : "Submit Assignment";
    const choices = realAssignments.map(a => {
      const isSelected = preferredId && String(a.assignment_id) === String(preferredId) ? "selected" : "";
      const isAlreadySub = a.submission ? " (Submitted - Re-attempt)" : "";
      return `<option value="${a.assignment_id}" ${isSelected}>${a.course_code} — ${a.title}${isAlreadySub}</option>`;
    }).join("");

    const targetAssig = preferredId ? realAssignments.find(a => String(a.assignment_id) === String(preferredId)) : realAssignments[0];
    const prevNotes = targetAssig && targetAssig.submission && targetAssig.submission.response_text ? targetAssig.submission.response_text : "";
    const refMaterial = targetAssig && targetAssig.attachment_path ? `
      <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:8px 12px; margin-bottom:12px; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong style="color:#166534;"><i class="fa-solid fa-file-arrow-down"></i> Teacher Reference Material:</strong>
          <span style="color:#15803d; margin-left:4px;">${targetAssig.attachment_name || 'Download Assignment Spec'}</span>
        </div>
        <a href="${getFileUrl(targetAssig.attachment_path)}" target="_blank" download class="filter-btn" style="font-size:11px; padding:3px 8px; background:#ffffff; color:var(--primary-blue);"><i class="fa-solid fa-download"></i> Download</a>
      </div>
    ` : '';

    modalBody.innerHTML = `
      <form id="realSubmissionForm">
        ${refMaterial}
        <div class="form-group">
          <label>Select Assignment</label>
          <select id="submissionAssignment" required>${choices}</select>
        </div>
        <div class="form-group" style="margin-top:10px;">
          <label>Answer / Solution Notes (Optional)</label>
          <textarea id="submissionResponse" rows="4" placeholder="Write your solution, explanation, or code notes...">${prevNotes}</textarea>
        </div>
        <div class="form-group" style="margin-top:10px;">
          <label>Upload Solution File (PDF, DOCX, ZIP, Code)</label>
          <input id="submissionFile" type="file" accept=".pdf,.docx,.doc,.zip,.txt,.py,.java,.cpp,.js">
          <span style="font-size:11px; color:var(--text-muted); margin-top:2px;">You can upload a replacement or updated document.</span>
        </div>
        <button type="submit" class="primary-btn" style="width:100%; justify-content:center; margin-top:15px;">
          <i class="fa-solid fa-paper-plane"></i> Submit to Instructor
        </button>
      </form>
    `;
    modal.style.display = "flex";
    document.getElementById("realSubmissionForm")?.addEventListener("submit", submit);
  };

  window.openUploadModalFor = function (assignmentId) {
    window.openUploadModal(assignmentId);
  };

  async function submit(event) {
    event.preventDefault();
    const id = document.getElementById("submissionAssignment").value;
    const file = document.getElementById("submissionFile").files[0];
    const notes = document.getElementById("submissionResponse").value;
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
    }

    try {
      let response;
      if (file) {
        const formData = new FormData();
        formData.append("attachment", file);
        if (notes) formData.append("response_text", notes);
        response = await fetch(`${API}/student/assignments/${id}/submissions/file`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token()}` },
          body: formData
        });
      } else {
        response = await fetch(`${API}/student/assignments/${id}/submissions`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token()}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ response_text: notes })
        });
      }

      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || "Submission failed. Please try again.");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit to Instructor';
        }
        return;
      }

      alert("Assignment submitted successfully!");
      closeModal();
      await load();
    } catch (err) {
      console.error(err);
      alert("An error occurred while submitting. Please check your network connection.");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit to Instructor';
      }
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    assignments = [];
    load().catch(() => {});
    if (typeof initCharts === "function") initCharts();
  });
})();

