/* Real assignment data binding, deletion, review, and AI grading assistance for the authenticated teacher. */
(function () {
  "use strict";
  const API_BASE_URL = window.ACOS_CONFIG.API_BASE_URL;
  let courses = [];
  let currentRawAssignments = [];
  let activeAssignmentData = null;
  let activeSubmissionsList = [];
  let currentReviewSubmission = null;
  let currentAIEvaluation = null;

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderAIMessage(markdown) {
    const escaped = escapeHtml(String(markdown || ""));
    const lines = escaped.split(/\r?\n/);
    let html = "";
    let listType = null;

    const closeList = () => {
      if (listType) {
        html += `</${listType}>`;
        listType = null;
      }
    };

    lines.forEach((line) => {
      const heading = line.match(/^#{1,3}\s+(.+)$/);
      const bullet = line.match(/^\s*[-*]\s+(.+)$/);
      const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/);

      if (heading) {
        closeList();
        html += `<div style="margin:10px 0 4px; font-weight:800; color:#075985; font-size:0.8rem;">${heading[1]}</div>`;
      } else if (bullet || numbered) {
        const wantedList = numbered ? "ol" : "ul";
        if (listType !== wantedList) {
          closeList();
          listType = wantedList;
          html += `<${listType} style="margin:5px 0 8px; padding-left:20px;">`;
        }
        html += `<li style="margin:3px 0;">${bullet ? bullet[1] : numbered[1]}</li>`;
      } else {
        closeList();
        html += line.trim() ? `<div style="margin:3px 0;">${line}</div>` : '<div style="height:5px;"></div>';
      }
    });
    closeList();

    return html
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/__(.+?)__/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code style=\"background:#e0f2fe; padding:1px 4px; border-radius:3px;\">$1</code>");
  }

  function responseErrorMessage(response, data) {
    if (data && data.detail) {
      return Array.isArray(data.detail)
        ? data.detail.map(error => error.msg || "Invalid request").join("; ")
        : data.detail;
    }
    return `AI request failed (${response.status} ${response.statusText || "error"})`;
  }

  function setOptions(id, items, label) {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = label ? `<option value="ALL">${label}</option>` : "";
    items.forEach(({ value, text }) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      select.appendChild(option);
    });
  }

  function formatAssignment(item) {
    const due = new Date(item.due_date);
    return {
      id: item.assignment_id,
      courseId: item.course_id,
      course: item.course_code,
      courseName: item.course_title,
      section: item.section,
      dueDate: due.toLocaleDateString("en-CA"),
      dueTime: due.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      submittedCount: item.submitted_count,
      totalStudents: item.enrolled_student_count,
      status: item.status,
      type: item.assignment_type,
      attachmentPath: item.attachment_path,
      description: item.description,
      totalMarks: item.total_marks
    };
  }

  function configureForm(courseData) {
    courses = courseData.courses || [];
    setOptions("courseFilterSelect", courses.map((course) => ({ value: course.course_code, text: `${course.course_code} ${course.course_title}` })), "All Courses & Semesters");
    setOptions("newCourse", courses.map((course) => ({ value: String(course.course_id), text: `${course.course_code} ${course.course_title}` })), "");

    const periods = [...new Set(courses.flatMap((course) => course.sections.map((section) => section.academic_year)))];
    setOptions("newAcademicYear", periods.map((year) => ({ value: year, text: year })), "");
    updateSections();
    document.getElementById("newCourse")?.addEventListener("change", updateSections);
  }

  function updateSections() {
    const course = courses.find((item) => String(item.course_id) === document.getElementById("newCourse")?.value);
    const sections = [...new Set((course?.sections || []).map((item) => item.section))];
    setOptions("newSection", sections.map((section) => ({ value: section, text: `Section ${section}` })), "");
  }

  function updateMetrics(metrics) {
    if (document.getElementById("statTotalAssignments")) {
      document.getElementById("statTotalAssignments").textContent = metrics.assignment_count;
    }
    if (document.getElementById("statPendingGrading")) {
      document.getElementById("statPendingGrading").textContent = metrics.pending_grading_count;
    }
    document.querySelectorAll(".stat-card").forEach((card) => {
      const label = card.querySelector("p")?.textContent.trim();
      const value = card.querySelector("h3");
      if (label === "Average Class Score" && value) value.textContent = "Live Monitored";
      if (label === "Submission Rate" && value) value.textContent = metrics.submission_rate === null ? "0%" : `${metrics.submission_rate}%`;
    });
  }

  async function loadAssignments() {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}`, Accept: "application/json" };
    try {
      const [assignmentsResponse, coursesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/teacher/assignments`, { headers }),
        fetch(`${API_BASE_URL}/teacher/courses`, { headers })
      ]);
      if (!assignmentsResponse.ok || !coursesResponse.ok) return;
      const [assignmentsData, coursesData] = await Promise.all([assignmentsResponse.json(), coursesResponse.json()]);
      configureForm(coursesData);
      currentRawAssignments = assignmentsData.assignments || [];
      assignmentsList = currentRawAssignments.map(formatAssignment);
      renderAssignments(assignmentsList);
      updateMetrics(assignmentsData.metrics);
      updateRecentFeed();
    } catch (err) {
      console.error("Error loading teacher assignments:", err);
    }
  }

  function updateRecentFeed() {
    const feedContainer = document.querySelector(".submission-feed-list");
    if (!feedContainer) return;
    const pendingAssignments = assignmentsList.filter(a => a.submittedCount > 0);
    if (!pendingAssignments.length) {
      feedContainer.innerHTML = '<p style="padding:12px; color:var(--text-muted); font-size:0.8rem;">No recent submissions to review.</p>';
      return;
    }
    feedContainer.innerHTML = pendingAssignments.slice(0, 4).map(a => `
      <div class="feed-item">
        <div class="feed-user">
          <div style="width:32px; height:32px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem;">
            <i class="fa-solid fa-file-pen"></i>
          </div>
          <div>
            <strong style="display:block; font-size:0.8rem;">${a.title}</strong>
            <span style="font-size:0.68rem; color:var(--text-muted);">${a.course} (${a.section}) &bull; ${a.submittedCount} Submitted</span>
          </div>
        </div>
        <button class="btn-outline" style="padding:4px 8px; font-size:0.7rem;" onclick="openSubmissionsModal(${a.id})">Review</button>
      </div>
    `).join("");
  }

  window.handleCreateAssignment = async function (event) {
    event.preventDefault();
    const token = localStorage.getItem("access_token");
    const type = document.getElementById("newType").value;
    const response = await fetch(`${API_BASE_URL}/teacher/assignments`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: Number(document.getElementById("newCourse").value),
        academic_year: document.getElementById("newAcademicYear").value,
        section: document.getElementById("newSection").value,
        title: document.getElementById("newTitle").value.trim(),
        assignment_type: type === "Lab Report" ? "Lab" : type,
        total_marks: Number(document.getElementById("newTotalMarks").value),
        due_date: `${document.getElementById("newDueDate").value}T${document.getElementById("newDueTime").value}:00`
      })
    });
    const data = await response.json();
    if (!response.ok) {
      alert(data.detail || "Unable to publish assignment.");
      return;
    }
    const file = document.getElementById("fileInput").files[0];
    if (file) {
      const upload = new FormData();
      upload.append("attachment", file);
      const attachmentResponse = await fetch(`${API_BASE_URL}/teacher/assignments/${data.assignment.assignment_id}/attachment`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: upload
      });
      if (!attachmentResponse.ok) alert("Assignment was published, but its attachment could not be uploaded.");
    }
    document.getElementById("createAssignmentModal").classList.remove("active");
    document.getElementById("createAssignmentForm").reset();
    document.getElementById("fileNameDisplay").textContent = "";
    await loadAssignments();
  };

  // Real backend DELETE assignment endpoint integration
  window.deleteAssignment = async function (assignmentId) {
    if (!confirm("Are you sure you want to delete this assignment?\nIt will be permanently removed from your dashboard and student portals.")) {
      return;
    }
    const token = localStorage.getItem("access_token");
    try {
      const response = await fetch(`${API_BASE_URL}/teacher/assignments/${assignmentId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" }
      });
      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || "Failed to delete assignment.");
        return;
      }
      alert("Assignment successfully deleted.");
      await loadAssignments();
    } catch (err) {
      console.error("Error deleting assignment:", err);
      alert("Failed to delete assignment. Please check server connection.");
    }
  };

  // Open List of Submissions for an Assignment
  window.openSubmissionsModal = async function (assignmentId) {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_BASE_URL}/teacher/assignments/${assignmentId}/submissions`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" }
    });
    if (!response.ok) {
      alert("Failed to fetch submissions for this assignment.");
      return;
    }
    const data = await response.json();
    activeAssignmentData = data.assignment;
    activeSubmissionsList = data.submissions || [];

    document.getElementById("submissionModalTitle").textContent = data.assignment.title;
    document.getElementById("submissionModalSubtitle").textContent = `${data.assignment.course_code} - Section ${data.assignment.section} (Total Marks: ${data.assignment.total_marks})`;

    const body = document.getElementById("studentSubmissionsBody");
    if (!activeSubmissionsList.length) {
      body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:24px; color:var(--text-muted); font-size:0.85rem;"><i class="fa-solid fa-folder-open" style="font-size:1.5rem; margin-bottom:6px; display:block;"></i>No student submissions have been submitted yet.</td></tr>';
    } else {
      body.innerHTML = activeSubmissionsList.map((item) => {
        const hasFile = item.file_path && item.file_path !== "inline";
        const fileLink = hasFile ? `<a href="${API_BASE_URL}/${item.file_path}" target="_blank" style="color:var(--primary); font-weight:700; text-decoration:underline;"><i class="fa-solid fa-file-arrow-down"></i> ${item.file_name || 'Download File'}</a>` : `<span style="color:var(--text-main);">${(item.response_text || 'Text Response').slice(0, 30)}...</span>`;
        const similarityWarning = (item.similarity_matches || []).length ? `<div style="font-size:0.68rem; color:#b45309; font-weight:700; margin-top:4px;"><i class="fa-solid fa-triangle-exclamation"></i> Similarity: ${item.similarity_matches[0].similarity_percent}% with ${escapeHtml(item.similarity_matches[0].student_name)}</div>` : "";
        const marksDisplay = item.graded ? `<span style="font-weight:700; color:var(--success);">${item.teacher_marks} / ${activeAssignmentData.total_marks}</span>` : '<span style="color:var(--warning); font-weight:700;">Needs Grading</span>';
        const statusBadge = item.graded ? '<span class="badge-status active">Reviewed</span>' : (item.is_late ? '<span class="badge-status pending">Late</span>' : '<span class="badge-status active">Submitted</span>');

        return `
          <tr>
            <td>
              <strong>${item.student_name}</strong>
              <div style="font-size:0.68rem; color:var(--text-muted);">${item.roll_number} &bull; Attempt #${item.submission_attempt || 1}</div>
            </td>
            <td>
              ${fileLink}
              ${similarityWarning}
              <div style="font-size:0.68rem; color:var(--text-muted);">${new Date(item.submitted_at).toLocaleString()}</div>
            </td>
            <td>${statusBadge}</td>
            <td>${marksDisplay}</td>
            <td style="text-align:right;">
              <button class="btn-primary" style="padding:5px 12px; font-size:0.75rem;" onclick="openSubmissionReview(${item.submission_id})">
                <i class="fa-solid fa-wand-magic-sparkles"></i> Review & AI
              </button>
            </td>
          </tr>
        `;
      }).join("");
    }

    document.getElementById("submissionsModal").classList.add("active");
  };

  // In-Portal Submission Review & AI Assistant Drawer
  window.openSubmissionReview = function (submissionId) {
    const sub = activeSubmissionsList.find(s => s.submission_id === submissionId);
    if (!sub || !activeAssignmentData) return;
    currentReviewSubmission = sub;
    currentAIEvaluation = null;

    document.getElementById("reviewStudentName").innerHTML = `<i class="fa-solid fa-graduation-cap" style="color:var(--primary);"></i> ${sub.student_name} (${sub.roll_number})`;
    document.getElementById("reviewSubMeta").textContent = `${activeAssignmentData.course_code} - ${activeAssignmentData.title} | ${sub.student_name} (${sub.roll_number}) | Submitted: ${new Date(sub.submitted_at).toLocaleString()} | Attempt #${sub.submission_attempt || 1} | Total Marks: ${activeAssignmentData.total_marks}`;
    document.getElementById("maxMarksLabel").textContent = activeAssignmentData.total_marks;

    // Set Teacher Reference & Download
    document.getElementById("teacherTaskDesc").textContent = activeAssignmentData.description || "No written description provided. Please refer to course syllabus.";
    const refContainer = document.getElementById("teacherRefDownloadContainer");
    if (activeAssignmentData.attachment_path) {
      refContainer.innerHTML = `<a href="${API_BASE_URL}/${activeAssignmentData.attachment_path}" target="_blank" class="btn-outline" style="padding:3px 8px; font-size:0.7rem; color:var(--primary);"><i class="fa-solid fa-download"></i> View Teacher Reference</a>`;
    } else {
      refContainer.innerHTML = `<span style="font-size:0.68rem; color:var(--text-muted);">No reference file attached</span>`;
    }

    // Set Student File Download & Work Preview
    const studentFileContainer = document.getElementById("studentFileDownloadContainer");
    const previewBox = document.getElementById("studentWorkPreview");
    if (sub.file_path && sub.file_path !== "inline") {
      studentFileContainer.innerHTML = `<a href="${API_BASE_URL}/${sub.file_path}" target="_blank" rel="noopener" class="btn-outline" style="padding:3px 8px; font-size:0.7rem; color:var(--success); font-weight:700;"><i class="fa-solid fa-folder-open"></i> Open / Download ${sub.file_name || 'Student File'}</a>`;
    } else {
      studentFileContainer.innerHTML = `<span style="font-size:0.68rem; color:var(--text-muted);">Inline Response</span>`;
    }

    // Smart in-portal document reader
    const fileExt = (sub.file_name || "").split(".").pop().toLowerCase();
    const fileUrl = (sub.file_path && sub.file_path !== "inline")
      ? `${API_BASE_URL}/${sub.file_path}` : null;

    if (sub.file_error && !sub.file_readable && !sub.response_text) {
      previewBox.style.padding = "16px";
      previewBox.innerHTML = `<div style="color:#b91c1c; text-align:center; padding:28px 12px;"><i class="fa-solid fa-triangle-exclamation" style="font-size:2rem; margin-bottom:8px;"></i><strong style="display:block;">Unable to read this submission</strong><span style="font-size:0.75rem;">${escapeHtml(sub.file_error)}</span>${fileUrl ? `<br><a href="${fileUrl}" target="_blank" rel="noopener" style="display:inline-block; margin-top:10px; color:#0369a1; font-weight:700;">Open / Download File</a>` : ""}</div>`;
    } else if (fileUrl && fileExt === "pdf") {
      // PDF: render inline iframe so teacher can read directly in portal
      previewBox.style.padding = "0";
      previewBox.style.overflow = "hidden";
      previewBox.innerHTML = `<iframe src="${fileUrl}" style="width:100%;height:100%;min-height:360px;border:none;border-radius:8px;" title="Student PDF Submission"></iframe>`;
    } else if (fileUrl && ["png", "jpg", "jpeg", "gif", "webp"].includes(fileExt)) {
      previewBox.style.padding = "10px";
      previewBox.style.overflow = "auto";
      previewBox.innerHTML = `<img src="${fileUrl}" alt="${escapeHtml(sub.file_name || 'Student image submission')}" style="display:block; max-width:100%; max-height:500px; margin:auto; object-fit:contain;" onerror="this.parentElement.innerHTML='<div style=\"padding:20px;color:#b91c1c;text-align:center;\">Image preview failed. Use Open / Download File above.</div>'">`;
    } else if (sub.extracted_text && sub.extracted_text.trim() && !sub.extracted_text.startsWith("[Attached file:")) {
      // DOCX, Code, or Text Document: render the actual extracted document text
      previewBox.style.padding = "14px";
      previewBox.style.overflow = "auto";
      const studentRespHeader = sub.response_text ? `<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #e2e8f0; font-weight:600; color:var(--primary);"><i class="fa-solid fa-comment-dots"></i> Student Remarks: ${sub.response_text}</div>` : '';
      const docHeader = sub.file_name ? `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:6px; border-bottom:1px dashed #cbd5e1; font-size:0.75rem; color:#0369a1; font-weight:700;"><i class="fa-solid fa-file-word"></i> Document Content: ${sub.file_name} <span style="font-size:0.7rem; color:#64748b; font-weight:normal;">(Direct In-Portal Reader)</span></div>` : '';
      previewBox.innerHTML = `${studentRespHeader}${docHeader}<div style="white-space:pre-wrap; line-height:1.6; font-size:0.8rem; color:#1e293b; font-family:var(--font-sans, inherit);">${escapeHtml(sub.extracted_text)}</div>`;
    } else if (sub.response_text) {
      // Inline text response
      previewBox.style.padding = "14px";
      previewBox.style.overflow = "auto";
      previewBox.innerHTML = `<div style="white-space:pre-wrap; line-height:1.6; font-size:0.8rem; color:#1e293b;">${escapeHtml(sub.response_text)}</div>`;
    } else if (fileUrl) {
      // Other binary formats (ZIP/Images)
      const iconMap = { zip:"fa-file-zipper", rar:"fa-file-zipper", jpg:"fa-file-image", jpeg:"fa-file-image", png:"fa-file-image" };
      const icon = iconMap[fileExt] || "fa-file";
      previewBox.style.padding = "16px";
      previewBox.style.overflow = "auto";
      previewBox.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:160px;color:var(--text-muted);gap:10px;text-align:center;">
          <i class="fa-solid ${icon}" style="font-size:2.8rem;color:var(--primary);opacity:0.7;"></i>
          <strong style="font-size:0.85rem;color:var(--text-main);">${sub.file_name || "Submitted File"}</strong>
          <span style="font-size:0.75rem;">Browser preview is unavailable for this format. Use <strong style="color:var(--success);">Open / Download File</strong> above.</span>
        </div>`;
    } else {
      previewBox.style.padding = "14px";
      previewBox.innerHTML = `<span style="color:var(--text-muted);">No response content entered.</span>`;
    }

    // Fill Existing Teacher Grades if any
    document.getElementById("gradeMarksInput").value = sub.teacher_marks !== null && sub.teacher_marks !== undefined ? sub.teacher_marks : "";
    document.getElementById("gradeFeedbackInput").value = sub.teacher_feedback || "";

    // Reset AI Assistant Panel & Chat
    switchAIPanelTab('eval');
    document.getElementById("aiEvaluationContainer").style.display = "none";
    document.getElementById("aiLoadingIndicator").style.display = "none";
    document.getElementById("aiPlaceholder").style.display = "block";
    resetAIChatPanel(sub);

    // If already evaluated by AI in database, restore it
    if (sub.ai_feedback) {
      try {
        const parsed = JSON.parse(sub.ai_feedback);
        currentAIEvaluation = parsed;
        displayAIEvaluation(parsed);
      } catch (e) {}
    }

    document.getElementById("reviewDrawerModal").classList.add("active");
  };

  // Tab switcher for AI Panel (Evaluation vs Chatbot)
  window.switchAIPanelTab = function (tab) {
    const evalBtn = document.getElementById("tabBtnEval");
    const chatBtn = document.getElementById("tabBtnChat");
    const evalContent = document.getElementById("aiTabEvalContent");
    const chatContent = document.getElementById("aiTabChatContent");

    if (tab === "eval") {
      evalBtn.style.borderBottom = "2px solid #0284c7";
      evalBtn.style.color = "#0284c7";
      evalBtn.style.fontWeight = "700";
      chatBtn.style.borderBottom = "2px solid transparent";
      chatBtn.style.color = "#64748b";
      chatBtn.style.fontWeight = "600";
      evalContent.style.display = "block";
      chatContent.style.display = "none";
    } else {
      chatBtn.style.borderBottom = "2px solid #0284c7";
      chatBtn.style.color = "#0284c7";
      chatBtn.style.fontWeight = "700";
      evalBtn.style.borderBottom = "2px solid transparent";
      evalBtn.style.color = "#64748b";
      evalBtn.style.fontWeight = "600";
      chatContent.style.display = "flex";
      evalContent.style.display = "none";
    }
  };

  let reviewChatHistory = [];

  function resetAIChatPanel(sub) {
    reviewChatHistory = [];
    const chatBox = document.getElementById("aiChatMessages");
    if (!chatBox) return;
    chatBox.innerHTML = `
      <div style="background:#e0f2fe; color:#0369a1; padding:8px 10px; border-radius:8px; line-height:1.4; align-self:flex-start; max-width:90%;">
        👋 <strong>AI Assistant:</strong> I have loaded <strong>${sub.student_name}</strong>'s attempt #${sub.submission_attempt || 1} for <em>"${activeAssignmentData ? activeAssignmentData.title : 'Assignment'}"</em>.<br>
        Ask me anything about their work (e.g. <em>"Is this submission authentic?"</em>, <em>"Did they answer the core questions?"</em>, <em>"Compare with reference solution"</em>).
      </div>
    `;
    const input = document.getElementById("aiChatInput");
    if (input) input.value = "";
  }

  // Interactive Chat with AI regarding current student submission
  window.sendAIChatMessage = async function () {
    const input = document.getElementById("aiChatInput");
    const message = input.value.trim();
    if (!message || !currentReviewSubmission) return;

    const chatBox = document.getElementById("aiChatMessages");
    const sendBtn = document.getElementById("btnSendAIChat");

    // Render Teacher User Message
    const userMsgEl = document.createElement("div");
    userMsgEl.style.cssText = "background:#2563eb; color:white; padding:8px 10px; border-radius:8px; line-height:1.4; align-self:flex-end; max-width:85%; word-break:break-word;";
    userMsgEl.innerHTML = `<strong>You:</strong> ${escapeHtml(message)}`;
    chatBox.appendChild(userMsgEl);
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Loading indicator
    const loadingEl = document.createElement("div");
    loadingEl.id = "aiChatTyping";
    loadingEl.style.cssText = "background:#f1f5f9; color:#64748b; padding:6px 10px; border-radius:8px; font-style:italic; align-self:flex-start;";
    loadingEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> AI is thinking...`;
    chatBox.appendChild(loadingEl);
    chatBox.scrollTop = chatBox.scrollHeight;

    sendBtn.disabled = true;

    // Build context-grounded prompt for submission chat
    const subText = currentReviewSubmission.extracted_text || currentReviewSubmission.response_text || "Attached file only.";
    const refText = activeAssignmentData ? (activeAssignmentData.description || "Course assignment guidelines").slice(0, 500) : "";
    const assignmentTitle = activeAssignmentData ? activeAssignmentData.title : "Assignment";
    const studentInfo = `${currentReviewSubmission.student_name} (${currentReviewSubmission.roll_number})`;

    const contextHeader = `[SUBMISSION REVIEW CHAT CONTEXT]
Assignment: ${assignmentTitle} (Total Marks: ${activeAssignmentData ? activeAssignmentData.total_marks : 20})
Student: ${studentInfo}
Teacher Reference/Task:
${refText}

Student Submitted Work/Document:
  `;
    const questionFooter = `

Teacher Question:
  ${message.slice(0, 500)}`;
    const availableText = Math.max(0, 1950 - contextHeader.length - questionFooter.length);
    const contextualMessage = `${contextHeader}${subText.slice(0, availableText)}${questionFooter}`;

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/teacher/ai/chat`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: contextualMessage,
          history: reviewChatHistory.slice(-4)
        })
      });

      const data = await response.json().catch(() => ({}));
      const typingEl = document.getElementById("aiChatTyping");
      if (typingEl) typingEl.remove();

      if (response.ok && data.response) {
        reviewChatHistory.push({ role: "user", content: message });
        reviewChatHistory.push({ role: "assistant", content: data.response });

        const botMsgEl = document.createElement("div");
        botMsgEl.style.cssText = "background:#ffffff; color:#0f172a; border:1px solid #bae6fd; padding:8px 10px; border-radius:8px; line-height:1.4; align-self:flex-start; max-width:90%; word-break:break-word;";
        botMsgEl.innerHTML = `<strong><i class="fa-solid fa-robot" style="color:#0284c7;"></i> AI:</strong><div style="margin-top:5px;">${renderAIMessage(data.response)}</div>`;
        chatBox.appendChild(botMsgEl);
      } else {
        throw new Error(responseErrorMessage(response, data));
      }
    } catch (err) {
      const typingEl = document.getElementById("aiChatTyping");
      if (typingEl) typingEl.remove();

      const errMsgEl = document.createElement("div");
      errMsgEl.style.cssText = "background:#fef2f2; color:#b91c1c; padding:8px 10px; border-radius:8px; align-self:flex-start;";
      errMsgEl.innerHTML = `⚠️ <em>${escapeHtml(err.message || 'Error communicating with AI assistant.')}</em>`;
      chatBox.appendChild(errMsgEl);
    } finally {
      sendBtn.disabled = false;
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  };

  // Run AI Evaluation
  window.runAIEvaluation = async function () {
    if (!currentReviewSubmission) return;
    const token = localStorage.getItem("access_token");
    const btn = document.getElementById("btnRunAIEval");
    const placeholder = document.getElementById("aiPlaceholder");
    const loader = document.getElementById("aiLoadingIndicator");
    const container = document.getElementById("aiEvaluationContainer");

    placeholder.style.display = "none";
    container.style.display = "none";
    loader.style.display = "block";
    btn.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/teacher/submissions/${currentReviewSubmission.submission_id}/ai-evaluate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" }
      });
      const data = await response.json();
      loader.style.display = "none";
      btn.disabled = false;

      if (response.ok && data.evaluation) {
        currentAIEvaluation = data.evaluation;
        displayAIEvaluation(data.evaluation);
        return;
      }
      throw new Error(data.detail || "AI service returned an unexpected response.");
    } catch (err) {
      console.warn("Server AI Evaluation warning:", err);
      loader.style.display = "none";
      btn.disabled = false;
      placeholder.style.display = "block";
      placeholder.textContent = `AI evaluation failed: ${err.message}. No automatic marks were assigned; please review the submission manually.`;
    }
  };

  function displayAIEvaluation(evalData) {
    const container = document.getElementById("aiEvaluationContainer");
    const placeholder = document.getElementById("aiPlaceholder");
    placeholder.style.display = "none";

    document.getElementById("aiSuggestedScore").textContent = `${evalData.suggested_marks} / ${activeAssignmentData.total_marks}`;
    
    const strengthsList = document.getElementById("aiStrengthsList");
    strengthsList.innerHTML = (evalData.well_attempted || []).map(s => `<li>${s}</li>`).join("");

    const limitationsList = document.getElementById("aiLimitationsList");
    limitationsList.innerHTML = (evalData.limitations || []).map(l => `<li>${l}</li>`).join("");

    document.getElementById("aiGeneralRemarks").textContent = evalData.general_remarks || "Solid submission attempt.";

    const similarityContainer = document.getElementById("aiSimilarityContainer");
    if (similarityContainer) {
      const matches = evalData.similarity_matches || [];
      similarityContainer.style.display = matches.length ? "block" : "none";
      similarityContainer.innerHTML = matches.length
        ? `<strong style="color:#b45309; display:block; margin-bottom:4px;"><i class="fa-solid fa-triangle-exclamation"></i> Similarity Warning</strong>${matches.map(match => `<div style="font-size:0.75rem; color:#92400e;">${escapeHtml(match.similarity_percent + "% similar to " + match.student_name + " (" + match.roll_number + ")")}</div>`).join("")}`
        : "";
    }

    container.style.display = "flex";
  }

  // Apply AI suggestions to teacher inputs
  window.applyAISuggestions = function () {
    if (!currentAIEvaluation) {
      alert("Please run Auto Evaluate first so there are AI marks and remarks to apply.");
      return;
    }
    document.getElementById("gradeMarksInput").value = currentAIEvaluation.suggested_marks;
    
    let feedback = `${currentAIEvaluation.general_remarks || ""}\n\n`;
    if (currentAIEvaluation.well_attempted && currentAIEvaluation.well_attempted.length) {
      feedback += `Strengths:\n- ${currentAIEvaluation.well_attempted.join("\n- ")}\n\n`;
    }
    if (currentAIEvaluation.limitations && currentAIEvaluation.limitations.length) {
      feedback += `Areas to Improve:\n- ${currentAIEvaluation.limitations.join("\n- ")}`;
    }
    document.getElementById("gradeFeedbackInput").value = feedback.trim();
  };

  // Save Teacher Submission Review
  window.handleSaveSubmissionReview = async function (event) {
    event.preventDefault();
    if (!currentReviewSubmission) return;
    const token = localStorage.getItem("access_token");
    const marks = Number(document.getElementById("gradeMarksInput").value);
    const feedback = document.getElementById("gradeFeedbackInput").value.trim();

    try {
      const response = await fetch(`${API_BASE_URL}/teacher/submissions/${currentReviewSubmission.submission_id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          teacher_marks: marks,
          teacher_feedback: feedback
        })
      });
      const data = await response.json();
      if (!response.ok) {
        alert(data.detail || "Failed to save submission review.");
        return;
      }
      alert("Marks and remarks saved successfully! The student portal will now display your review.");
      document.getElementById("reviewDrawerModal").classList.remove("active");
      if (activeAssignmentData) {
        await openSubmissionsModal(activeAssignmentData.assignment_id);
      }
      await loadAssignments();
    } catch (err) {
      console.error("Error saving submission review:", err);
      alert("Failed to save grade review. Please check server connection.");
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    // Clear legacy mock data and bind close modal handlers
    assignmentsList = [];
    renderAssignments(assignmentsList);

    document.getElementById("closeReviewModal")?.addEventListener("click", () => {
      document.getElementById("reviewDrawerModal")?.classList.remove("active");
    });

    loadAssignments().catch(() => {});
  });
})();

