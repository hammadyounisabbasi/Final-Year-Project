(() => {
  'use strict';
  const token = () => localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || localStorage.getItem('token');
  const apiBase = window.ACOS_CONFIG.API_BASE_URL;
  const esc = value => String(value ?? 'N/A').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const display = value => value === null || value === undefined || value === '' ? 'N/A' : value;
  const money = value => value === null || value === undefined ? 'N/A' : `PKR ${Number(value).toLocaleString()}`;
  const state = {page: 1, pageSize: 20, sortBy: 'name', sortOrder: 'asc', overview: null, selectedStudentId: null, detail: null, chart: null};

  async function api(path, options = {}) {
    const response = await fetch(`${apiBase}${path}`, { ...options, headers: {Authorization: `Bearer ${token()}`, Accept: 'application/json', ...(options.body ? {'Content-Type':'application/json'} : {}), ...(options.headers || {})} });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 401) throw new Error('Your session has expired. Please sign in again.');
      throw new Error(typeof data.detail === 'string' ? data.detail : 'The request could not be completed.');
    }
    return data;
  }

  function toast(message, error = false) {
    const item = document.createElement('div'); item.className = `student-toast${error ? ' error' : ''}`; item.textContent = message; document.body.append(item); setTimeout(() => item.remove(), 3200);
  }

  function buildDirectory() {
    const grid = document.querySelector('.metrics-grid');
    const panel = document.createElement('section'); panel.className = 'student-directory-panel'; panel.id = 'studentDirectory';
    panel.innerHTML = `<div class="student-directory-head"><div><h4>Student Directory</h4><span class="student-directory-status" id="directoryStatus">Loading real student records…</span></div></div>
      <form class="student-filters" id="studentFilters">
        <input id="directorySearch" type="search" maxlength="200" placeholder="Name, roll no., registration no. or email">
        <select id="departmentFilter"><option value="">All departments</option></select>
        <select id="programFilter"><option value="">All programs</option></select>
        <select id="semesterFilter"><option value="">All semesters</option></select>
        <select id="sectionFilter"><option value="">All sections</option></select>
        <select id="statusFilter"><option value="">All statuses</option></select>
        <select id="sortFilter"><option value="name:asc">Name A–Z</option><option value="name:desc">Name Z–A</option><option value="roll_number:asc">Roll number</option><option value="semester:asc">Semester low–high</option><option value="semester:desc">Semester high–low</option><option value="batch_year:desc">Newest batch</option></select>
      </form>
      <div class="student-table-wrap"><table class="student-directory-table"><thead><tr><th>Student</th><th>Roll / Registration</th><th>Department / Program</th><th>Semester</th><th>Section</th><th>Batch</th><th>Current courses</th><th>Email / Phone</th><th>Status</th><th>Actions</th></tr></thead><tbody id="studentRows"><tr><td class="student-empty" colspan="10">Loading…</td></tr></tbody></table></div>
      <div class="student-pagination"><span id="pageSummary"></span><div><button class="student-btn" id="prevPage" type="button">Previous</button><button class="student-btn" id="nextPage" type="button">Next</button></div></div>`;
    grid.insertAdjacentElement('afterend', panel);
    panel.querySelector('#studentFilters').addEventListener('submit', event => event.preventDefault());
    let debounce;
    panel.querySelector('#directorySearch').addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(() => { state.page = 1; loadDirectory(); }, 280); });
    ['departmentFilter','programFilter','semesterFilter','sectionFilter','statusFilter'].forEach(id => panel.querySelector(`#${id}`).addEventListener('change', () => { state.page = 1; loadDirectory(); }));
    panel.querySelector('#sortFilter').addEventListener('change', event => { [state.sortBy, state.sortOrder] = event.target.value.split(':'); state.page = 1; loadDirectory(); });
    panel.querySelector('#prevPage').addEventListener('click', () => { if (state.page > 1) { state.page--; loadDirectory(); } });
    panel.querySelector('#nextPage').addEventListener('click', () => { state.page++; loadDirectory(); });
    const topSearch = document.querySelector('.search-container input');
    if (topSearch) { topSearch.placeholder = 'Search student records…'; topSearch.addEventListener('input', () => { panel.querySelector('#directorySearch').value = topSearch.value; panel.querySelector('#directorySearch').dispatchEvent(new Event('input')); }); }
  }

  function optionList(selectId, rows, valueKey = null, labelKey = null, prefix = '') {
    const select = document.getElementById(selectId); const first = select.firstElementChild.outerHTML;
    select.innerHTML = first + rows.map(row => { const value = valueKey ? row[valueKey] : row; const label = labelKey ? row[labelKey] : row; return `<option value="${esc(value)}">${esc(prefix + label)}</option>`; }).join('');
  }

  async function loadOverview() {
    const data = await api('/admin/students/overview'); state.overview = data;
    document.body.classList.add('student-data-ready');
    document.getElementById('statTotalStudents').textContent = data.stats.total_students.toLocaleString();
    document.getElementById('statActiveEnrollment').textContent = data.stats.active_students.toLocaleString();
    document.getElementById('statAtRisk').textContent = data.stats.at_risk_students.toLocaleString();
    document.getElementById('statPendingRequests').textContent = data.stats.active_accounts.toLocaleString();
    document.getElementById('statScholarships').textContent = data.stats.scholarship_students.toLocaleString();
    optionList('departmentFilter', data.filters.departments, 'id', 'name'); optionList('programFilter', data.filters.programs); optionList('semesterFilter', data.filters.semesters, null, null, 'Semester '); optionList('sectionFilter', data.filters.sections, null, null, 'Section '); optionList('statusFilter', data.filters.statuses);
    renderOverviewChart(data.distributions.programs);
    const list = document.querySelector('.program-dist-list');
    if (list) { const max = Math.max(...data.distributions.programs.map(x => x.count), 1); list.innerHTML = data.distributions.programs.slice(0, 6).map(item => `<div><div class="program-item-row"><span>${esc(item.name)}</span><strong>${item.count.toLocaleString()}</strong></div><div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${item.count / max * 100}%"></div></div></div>`).join('') || '<p class="student-empty">No program data available.</p>'; }
    const second = document.querySelector('.grid-2-col-wide .panel:nth-child(2)');
    if (second) { const max = Math.max(...data.distributions.semesters.map(x => x.count), 1); second.innerHTML = `<div class="panel-header"><div><h4>Semester Distribution</h4><small style="color:#64748b">Real current student profile data</small></div></div><div class="semester-list">${data.distributions.semesters.map(item => `<div class="semester-row"><span>Semester ${item.semester}</span><div class="semester-bar"><span style="width:${item.count / max * 100}%"></span></div><strong>${item.count}</strong></div>`).join('') || '<p>No semester data available.</p>'}</div><p style="margin-top:12px;font-size:10px;color:#64748b">At-risk count: ${esc(data.risk_definition)}</p>`; }
  }

  function renderOverviewChart(programs) {
    const canvas = document.getElementById('studentOverviewChart');
    if (!canvas) return;
    if (!window.Chart) { canvas.parentElement.hidden = true; return; }
    if (state.chart) state.chart.destroy();
    const top = programs.slice(0, 5); const rest = programs.slice(5).reduce((sum, item) => sum + item.count, 0); if (rest) top.push({name:'Other programs', count:rest});
    state.chart = new Chart(canvas.getContext('2d'), {type:'doughnut', data:{labels:top.map(x => x.name),datasets:[{data:top.map(x => x.count),backgroundColor:['#2563eb','#10b981','#f59e0b','#8b5cf6','#06b6d4','#64748b'],borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},cutout:'72%'}});
  }

  function queryString() {
    const params = new URLSearchParams({page: state.page, page_size: state.pageSize, sort_by: state.sortBy, sort_order: state.sortOrder});
    [['search','directorySearch'],['department_id','departmentFilter'],['program','programFilter'],['semester','semesterFilter'],['section','sectionFilter'],['student_status','statusFilter']].forEach(([key,id]) => { const value = document.getElementById(id).value.trim(); if (value) params.set(key, value); }); return params;
  }

  async function loadDirectory() {
    const body = document.getElementById('studentRows'), status = document.getElementById('directoryStatus'); status.textContent = 'Loading…';
    try {
      const data = await api(`/admin/students?${queryString()}`); const p = data.pagination;
      if (state.page > 1 && p.total_pages && state.page > p.total_pages) { state.page = p.total_pages; return loadDirectory(); }
      body.innerHTML = data.items.length ? data.items.map(row => `<tr><td><div class="student-name-cell"><span class="student-avatar">${row.profile_photo ? `<img src="${esc(row.profile_photo)}" alt="">` : esc((row.first_name?.[0] || '') + (row.last_name?.[0] || ''))}</span><span>${esc(row.name)}</span></div></td><td>${esc(row.roll_number)}<br><small>${esc(row.registration_number)}</small></td><td>${esc(row.department)}<br><small>${esc(row.program)}</small></td><td>${esc(row.semester)}</td><td>${esc(row.section)}</td><td>${esc(row.batch_year)}</td><td>${esc(row.active_enrollments)}</td><td>${esc(row.email)}<br><small>${esc(row.phone)}</small></td><td><span class="student-badge ${row.student_status === 'Active' && row.account_active ? 'active' : ''}">${esc(row.student_status)}${row.account_active ? '' : ' / account inactive'}</span></td><td><div class="student-row-actions"><button class="student-btn primary" data-view="${row.student_id}">View</button><button class="student-btn" data-edit="${row.student_id}">Edit</button></div></td></tr>`).join('') : '<tr><td class="student-empty" colspan="10">No students match the selected filters.</td></tr>';
      status.textContent = `${p.total.toLocaleString()} real database record${p.total === 1 ? '' : 's'}`; document.getElementById('pageSummary').textContent = p.total ? `Page ${p.page} of ${p.total_pages} · ${p.total.toLocaleString()} students` : 'No results';
      document.getElementById('prevPage').disabled = p.page <= 1; document.getElementById('nextPage').disabled = !p.total_pages || p.page >= p.total_pages;
      body.querySelectorAll('[data-view]').forEach(btn => btn.addEventListener('click', () => openDetail(Number(btn.dataset.view), false))); body.querySelectorAll('[data-edit]').forEach(btn => btn.addEventListener('click', () => openDetail(Number(btn.dataset.edit), true)));
    } catch (error) { body.innerHTML = `<tr><td class="student-empty" colspan="10">${esc(error.message)}</td></tr>`; status.textContent = 'Unable to load records'; }
  }

  function buildModal() {
    document.body.insertAdjacentHTML('beforeend', `<div class="student-modal" id="studentModal" hidden><section class="student-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="studentModalTitle"><header class="student-modal-head"><h3 id="studentModalTitle">Student record</h3><button type="button" id="studentModalClose" aria-label="Close">×</button></header><div class="student-modal-body" id="studentModalBody"></div></section></div>`);
    const modal = document.getElementById('studentModal'); document.getElementById('studentModalClose').addEventListener('click', closeModal); modal.addEventListener('click', event => { if (event.target === modal) closeModal(); }); document.addEventListener('keydown', event => { if (event.key === 'Escape' && !modal.hidden) closeModal(); });
  }
  function closeModal() { document.getElementById('studentModal').hidden = true; document.body.style.overflow = ''; }
  const cards = values => `<div class="student-info-grid">${values.map(([label,value]) => `<div class="student-info-card"><small>${esc(label)}</small><strong>${esc(display(value))}</strong></div>`).join('')}</div>`;
  const table = (headers, rows) => rows.length ? `<div class="student-table-wrap"><table class="student-detail-table"><thead><tr>${headers.map(x => `<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>` : '<p class="student-empty">No records are available for this section.</p>';

  function detailSections(data) {
    const p=data.profile,a=data.academics,en=data.enrollments,at=data.attendance,fee=data.fees,as=data.assignments,tt=data.timetable;
    return {
      profile: cards([['Roll number',p.roll_number],['Registration',p.registration_number],['Email',p.email],['Phone',p.phone],['Department',p.department],['Program',p.program],['Semester',p.semester],['Section',p.section],['Batch',p.batch_year],['Admission date',p.admission_date],['Expected graduation',p.expected_graduation],['Student status',p.student_status],['Account active',p.account_active?'Yes':'No'],['Account verified',p.account_verified?'Yes':'No'],['Last login',p.last_login],['Address',p.address]]),
      academic: cards([['CGPA',a.overall_cgpa],['Academic standing',a.academic_status],['Completed credits',a.total_completed_credits],['Passed courses',a.completed_course_results.filter(x=>x.status==='Pass').length],['Failed courses',a.completed_course_results.filter(x=>x.status==='Fail').length],['Current enrollments',en.total_enrolled_courses]]) + '<h4 class="student-section-title">Current courses</h4>' + table(['Code','Course','Credits','Teacher'],en.courses.map(x=>`<tr><td>${esc(x.course_code)}</td><td>${esc(x.course_title)}</td><td>${esc(x.credit_hours)}</td><td>${esc(x.teacher)}</td></tr>`)) + '<h4 class="student-section-title">Published course results</h4>' + table(['Semester','Course','Grade','GPA points','Status'],a.completed_course_results.map(x=>`<tr><td>${esc(x.semester)}</td><td>${esc(x.course_code)} — ${esc(x.course_title)}</td><td>${esc(x.letter_grade)}</td><td>${esc(x.grade_points)}</td><td>${esc(x.status)}</td></tr>`)),
      attendance: (!at.has_records ? '<p class="student-empty">No attendance records are available; no percentage has been inferred.</p>' : cards([['Recorded classes',at.total_classes],['Overall attendance',`${at.overall_percentage}%`],['Absent',at.total_absent],['Late',at.total_late],['Leave',at.total_leave]]) + '<h4 class="student-section-title">Course attendance</h4>' + table(['Course','Classes','Present/Late','Absent','Attendance'],at.courses_attendance.map(x=>`<tr><td>${esc(x.course_code)} — ${esc(x.course_title)}</td><td>${x.total_classes}</td><td>${x.attended}</td><td>${x.absent}</td><td>${x.percentage}%</td></tr>`))),
      fees: (!fee.has_fee_records ? '<p class="student-empty">No fee record is available.</p>' : cards([['Status',fee.payment_status],['Total fee',money(fee.total_fee)],['Paid',money(fee.paid_amount)],['Outstanding',money(fee.remaining_amount)],['Scholarship',money(fee.scholarship_amount)],['Discount',money(fee.discount_amount)],['Due date',fee.due_date],['Verified',fee.verified?'Yes':'No']]) + '<h4 class="student-section-title">Fee history</h4>' + table(['Semester','Year','Total','Paid','Outstanding','Status'],fee.all_semester_records.map(x=>`<tr><td>${esc(x.semester)}</td><td>${esc(x.academic_year)}</td><td>${esc(money(x.total_fee))}</td><td>${esc(money(x.paid_amount))}</td><td>${esc(money(x.remaining_amount))}</td><td>${esc(x.status)}</td></tr>`))),
      assignments: cards([['Total published assignments',as.total_assignments],['Submitted',as.submitted_count],['Pending',as.pending_count],['Missed',as.missed_count]]) + '<h4 class="student-section-title">Pending and missed</h4>' + table(['Course','Assignment','Due','Status'],[...as.pending_assignments,...as.missed_assignments].map(x=>`<tr><td>${esc(x.course_code)}</td><td>${esc(x.title)}</td><td>${esc(x.due_date)}</td><td>${esc(x.submission_status)}</td></tr>`)),
      timetable: table(['Day','Time','Course','Room','Teacher'],tt.weekly_schedule.map(x=>`<tr><td>${esc(x.day)}</td><td>${esc(x.start_time)}–${esc(x.end_time)}</td><td>${esc(x.course_code)} — ${esc(x.course_title)}</td><td>${esc(x.room)}</td><td>${esc(x.teacher)}</td></tr>`)),
      notifications: table(['Date','Title','Type','Priority'],data.notifications.map(x=>`<tr><td>${esc(x.created_at)}</td><td>${esc(x.title)}</td><td>${esc(x.notification_type)}</td><td>${esc(x.priority)}</td></tr>`))
    };
  }

  async function openDetail(id, edit) {
    const modal=document.getElementById('studentModal'),body=document.getElementById('studentModalBody'); modal.hidden=false; document.body.style.overflow='hidden'; body.innerHTML='<p class="student-empty">Loading student record…</p>';
    try { const data=await api(`/admin/students/${id}`); state.selectedStudentId=id; state.detail=data; renderDetail(data,edit); } catch(error){ body.innerHTML=`<p class="student-empty">${esc(error.message)}</p>`; }
  }
  function renderDetail(data, edit=false) {
    const p=data.profile,body=document.getElementById('studentModalBody'); document.getElementById('studentModalTitle').textContent=`${p.name} · ${p.roll_number}`;
    if(edit){ renderEdit(data); return; }
    const sections=detailSections(data); body.innerHTML=`<div class="student-detail-hero"><span class="student-avatar">${esc((p.first_name?.[0]||'')+(p.last_name?.[0]||''))}</span><div><h2>${esc(p.name)}</h2><p>${esc(p.roll_number)} · ${esc(p.program)} · Semester ${esc(p.semester)}</p></div><button class="student-btn" id="detailEdit" type="button">Edit supported fields</button></div><div class="student-detail-tabs">${Object.keys(sections).map((key,i)=>`<button class="${i===0?'active':''}" data-tab="${key}">${key[0].toUpperCase()+key.slice(1)}</button>`).join('')}</div><div id="detailSection">${sections.profile}</div>`;
    body.querySelector('#detailEdit').addEventListener('click',()=>renderEdit(data)); body.querySelectorAll('[data-tab]').forEach(btn=>btn.addEventListener('click',()=>{body.querySelectorAll('[data-tab]').forEach(x=>x.classList.remove('active'));btn.classList.add('active');body.querySelector('#detailSection').innerHTML=sections[btn.dataset.tab];}));
  }
  function renderEdit(data) {
    const p=data.profile,departments=state.overview.filters.departments,body=document.getElementById('studentModalBody'); body.innerHTML=`<form class="student-edit-form" id="studentEditForm"><label>First name<input name="first_name" required value="${esc(p.first_name)}"></label><label>Last name<input name="last_name" required value="${esc(p.last_name)}"></label><label>Email<input name="email" type="email" required value="${esc(p.email)}"></label><label>Phone<input name="phone" value="${esc(p.phone==='N/A'?'':p.phone||'')}"></label><label>Emergency contact<input name="emergency_contact" value="${esc(p.emergency_contact||'')}"></label><label>Program<input name="program" required value="${esc(p.program)}"></label><label>Department<select name="department_id">${departments.map(x=>`<option value="${x.id}" ${x.id===p.department_id?'selected':''}>${esc(x.name)}</option>`).join('')}</select></label><label>Semester<input name="semester" type="number" min="1" max="20" required value="${esc(p.semester)}"></label><label>Section<input name="section" value="${esc(p.section||'')}"></label><label>Batch year<input name="batch_year" type="number" min="1900" max="2200" value="${esc(p.batch_year||'')}"></label><label>Student status<select name="status">${['Active','Graduated','Suspended','Dropped'].map(x=>`<option ${x===p.student_status?'selected':''}>${x}</option>`).join('')}</select></label><label>Account status<select name="account_active"><option value="true" ${p.account_active?'selected':''}>Active</option><option value="false" ${!p.account_active?'selected':''}>Inactive</option></select></label><label class="wide">Address<textarea name="address" rows="3">${esc(p.address||'')}</textarea></label><div class="student-form-actions"><button type="button" class="student-btn" id="cancelEdit">Cancel</button><button type="submit" class="student-btn primary">Save changes</button></div></form>`;
    body.querySelector('#cancelEdit').addEventListener('click',()=>renderDetail(data)); body.querySelector('form').addEventListener('submit',saveEdit);
  }
  async function saveEdit(event){ event.preventDefault(); const form=event.currentTarget,button=form.querySelector('[type=submit]'),fd=new FormData(form),payload={}; fd.forEach((v,k)=>payload[k]=v===''?null:v); payload.semester=Number(payload.semester); payload.department_id=Number(payload.department_id); payload.batch_year=payload.batch_year?Number(payload.batch_year):null; payload.account_active=payload.account_active==='true'; button.disabled=true; try{await api(`/admin/students/${state.selectedStudentId}`,{method:'PATCH',body:JSON.stringify(payload)});toast('Student record updated safely.');await Promise.all([loadDirectory(),loadOverview()]);await openDetail(state.selectedStudentId,false);}catch(error){toast(error.message,true);button.disabled=false;}}

  function renderMarkdown(value){ return esc(value).split(/\r?\n/).map(line=>line.startsWith('- ')?`<li>${line.slice(2)}</li>`:line.startsWith('### ')?`<h3>${line.slice(4)}</h3>`:line?`<p>${line.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')}</p>`:'').join('').replace(/(?:<li>.*?<\/li>)+/g,m=>`<ul>${m}</ul>`); }
  function buildAssistant(){
    const auth=token(); if(!auth)return; let records=[],history=[]; const key='admin-student-ai-state'; try{records=JSON.parse(sessionStorage.getItem(key)||'[]');if(!Array.isArray(records))records=[];}catch(_){records=[];} history=records.map(x=>({role:x.role,content:x.text})).slice(-12);
    document.body.insertAdjacentHTML('beforeend',`<button class="fee-ai-launcher" id="studentAiLauncher" type="button" aria-label="Open Student Management AI Assistant" aria-expanded="false" title="Ask Student Management AI Assistant">🤖</button><section class="fee-ai-drawer" id="studentAiDrawer" hidden aria-label="Student Management AI Assistant"><header class="fee-ai-header"><div class="fee-ai-title"><span>🤖</span><span>Student Management AI</span></div><div class="fee-ai-actions"><button id="studentAiClear" type="button" aria-label="Start a new chat" title="New chat">↻</button><button id="studentAiClose" type="button" aria-label="Close assistant" title="Close">×</button></div></header><div class="fee-ai-body" id="studentAiBody" role="log" aria-live="polite"></div><form class="fee-ai-footer" id="studentAiForm"><textarea id="studentAiInput" rows="1" maxlength="2000" required aria-label="Message the Student Management AI Assistant" placeholder="Ask about students, results, attendance, fees…"></textarea><button type="submit" aria-label="Send" title="Send">➤</button></form><p class="fee-ai-status" id="studentAiStatus" role="status"></p></section>`);
    const launcher=document.getElementById('studentAiLauncher'),drawer=document.getElementById('studentAiDrawer'),chatBody=document.getElementById('studentAiBody'),input=document.getElementById('studentAiInput'),form=document.getElementById('studentAiForm'),status=document.getElementById('studentAiStatus');
    const add=(role,text,replace)=>{const el=replace||document.createElement('div');el.className=`fee-ai-message ${role}`;el.innerHTML=`<strong>${role==='user'?'You':'Student Management AI'}</strong><div class="fee-ai-text">${role==='assistant'?renderMarkdown(text):esc(text)}</div>`;if(!replace)chatBody.append(el);chatBody.scrollTop=chatBody.scrollHeight;return el;}; const greeting='Hello! I can query the real student directory, academic records, attendance, fees, assignments, and timetables available to your admin account.'; if(records.length)records.forEach(x=>add(x.role,x.text));else add('assistant',greeting);
    launcher.onclick=()=>{drawer.hidden=false;launcher.setAttribute('aria-expanded','true');input.focus();};document.getElementById('studentAiClose').onclick=()=>{drawer.hidden=true;launcher.setAttribute('aria-expanded','false');};document.getElementById('studentAiClear').onclick=()=>{records=[];history=[];sessionStorage.removeItem(key);chatBody.innerHTML='';add('assistant',greeting);};
    form.addEventListener('submit',async event=>{event.preventDefault();const message=input.value.trim();if(!message)return;const oldHistory=history.slice(-12);add('user',message);records.push({role:'user',text:message});history.push({role:'user',content:message});const pending=add('assistant','Checking authenticated database records…');input.value='';form.querySelector('button').disabled=true;status.textContent='Preparing a grounded answer…';try{const data=await api('/admin/students/ai/chat',{method:'POST',body:JSON.stringify({message,history:oldHistory,selected_student_id:state.selectedStudentId})});add('assistant',data.response,pending);records.push({role:'assistant',text:data.response});history.push({role:'assistant',content:data.response});status.textContent=data.provider?`Grounded query · ${data.provider}`:'';}catch(error){const reply=`I could not complete that request: ${error.message}`;add('assistant',reply,pending);records.push({role:'assistant',text:reply});status.textContent=error.message;}finally{form.querySelector('button').disabled=false;sessionStorage.setItem(key,JSON.stringify(records.slice(-24)));input.focus();}}); input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit();}});
  }

  async function init(){
    document.querySelectorAll('.grid-3-col-equal,.grid-3-col-bottom').forEach(element => element.remove());
    buildDirectory();buildModal();buildAssistant();try{await loadOverview();await loadDirectory();}catch(error){toast(error.message,true);document.getElementById('directoryStatus').textContent='Authentication or API error';}
  }
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init();
})();
