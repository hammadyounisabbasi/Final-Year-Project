(function(){
  const API=window.ACOS_CONFIG.API_BASE_URL+'/admin/timetable-builder';
  const $=id=>document.getElementById(id),state={options:null,drafts:[],active:null,editing:null,customCourses:[]};
  const token=()=>localStorage.getItem('access_token')||localStorage.getItem('token')||sessionStorage.getItem('access_token')||'';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const opt=(v,l,s=false)=>`<option value="${esc(v)}" ${s?'selected':''}>${esc(l)}</option>`;

  function errors(values,target='builder-errors'){
    values=Array.isArray(values)?values:[values];
    $(target).innerHTML=`<b>Please Review Requirements</b><ul>${values.map(v=>`<li>${esc(v)}</li>`).join('')}</ul>`;
    $(target).hidden=false;
    $(target).scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function clear(){
    $('builder-errors').hidden=true;
    $('builder-errors').replaceChildren();
    $('draft-conflicts').hidden=true;
    $('draft-conflicts').replaceChildren();
  }

  function renderMeetingRows(courseId, count, defaultTeacherId, roomType, defaultRoomId) {
    const days = state.options?.defaults?.working_days || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const teachers = state.options?.teachers || [];
    const rooms = (state.options?.rooms || []).filter(r => !roomType || r.room_type === roomType);
    let html = '';
    for (let i = 1; i <= count; i++) {
      html += `
        <div class="meeting-row-card meeting-setup" data-meeting-index="${i}">
          <div class="meeting-tag-badge">
            <span class="m-dot"></span>
            <span>Class ${i}</span>
          </div>
          <div class="form-field">
            <label class="compact-label">Day</label>
            <select class="meeting-day">
              <option value="">Auto Schedule</option>
              ${days.map(d => opt(d, d)).join('')}
            </select>
          </div>
          <div class="form-field">
            <label class="compact-label">Start</label>
            <input class="meeting-start" type="time">
          </div>
          <div class="form-field">
            <label class="compact-label">End</label>
            <input class="meeting-end" type="time">
          </div>
          <div class="form-field">
            <label class="compact-label">Teacher</label>
            <select class="meeting-teacher">
              <option value="">Default Faculty</option>
              ${teachers.map(t => opt(t.id, t.name, t.id === defaultTeacherId)).join('')}
            </select>
          </div>
          <div class="form-field">
            <label class="compact-label">Assigned Room</label>
            <select class="meeting-room">
              <option value="">Auto Allocate</option>
              ${rooms.map(r => opt(r.id, `${r.code} (${r.capacity} seats)`, r.id === defaultRoomId)).join('')}
            </select>
          </div>
        </div>`;
    }
    return html;
  }

  function courseRow(c){
    const deptId=Number($('builder-department').value);
    const teachers=state.options.teachers.filter(t=>t.department_id===deptId||t.id===c.assigned_teacher_id);
    const type=c.course_type==='Lab'?'Laboratory':'Classroom';
    const rooms=state.options.rooms.filter(r=>r.room_type===type);
    const isCustom=!!c.is_custom;
    const weeklyCount = c.credit_hours || 3;

    return `<div class="course-setup-card course-setup is-active-course" data-course-id="${c.id}" data-credit-hours="${c.credit_hours}" data-custom="${isCustom}">
      <div class="course-main-row">
        <label class="course-check-label">
          <input class="course-enabled" type="checkbox" checked>
          <div class="course-title-meta">
            <div class="course-code-row">
              <strong class="course-code-text">${esc(c.code)}</strong>
              ${isCustom?'<span class="custom-course-badge">Manual Addition</span>':''}
            </div>
            <span class="course-title-text">${esc(c.title)}</span>
          </div>
        </label>
        <div class="form-field">
          <label>Assigned Faculty <span class="req">*</span></label>
          <select class="course-teacher" required>
            <option value="">Choose Faculty…</option>
            ${teachers.map(t=>opt(t.id,t.name,t.id===c.assigned_teacher_id)).join('')}
          </select>
        </div>
        <div class="form-field form-field-narrow">
          <label>Credits</label>
          <input class="text-center font-mono font-bold" value="${c.credit_hours}" readonly>
        </div>
        <div class="form-field form-field-narrow">
          <label>Classes/Wk</label>
          <input class="course-sessions text-center font-mono" type="number" min="1" max="12" value="${weeklyCount}">
        </div>
        <div class="form-field form-field-medium">
          <label>Duration</label>
          <select class="course-duration">
            ${[30,45,60,90,120,180].map(x=>opt(x,x+' min',x===60)).join('')}
          </select>
        </div>
        <div class="form-field form-field-medium">
          <label>Space Type</label>
          <select class="course-room-type">
            ${['Classroom','Computer Lab','Laboratory','Seminar Room'].map(x=>opt(x,x,x===type)).join('')}
          </select>
        </div>
        <div class="form-field field-with-action">
          <div class="field-label-action-row">
            <label>Eligible Rooms <span class="req">*</span></label>
            <button type="button" class="btn-inline-add trigger-add-room-btn">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
              <span>+ New</span>
            </button>
          </div>
          <select class="course-rooms" multiple size="3">
            ${rooms.map((r,idx)=>opt(r.id,`${r.code} (${r.capacity} seats)`,idx===0)).join('')}
          </select>
        </div>
      </div>
      <div class="meetings-container">
        <div class="meetings-header">
          <div class="meetings-title-tag">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            <span>Weekly Class Meetings (${weeklyCount} sessions per week)</span>
          </div>
          <span class="meetings-toggle-hint">Optional: Set independent times/rooms for each class meeting or leave for automatic AI placement</span>
        </div>
        <div class="meetings-list">
          ${renderMeetingRows(c.id, weeklyCount, c.assigned_teacher_id, type, rooms[0]?.id)}
        </div>
      </div>
    </div>`;
  }

  function renderSemesters(){
    if(!state.options)return;
    const dept=Number($('builder-department').value);
    const selected=[...$('builder-semesters').querySelectorAll('input:checked')].map(x=>Number(x.value)).sort((a,b)=>a-b);
    
    // Update counter
    const countBadge=$('selected-semesters-count');
    if(countBadge)countBadge.textContent=`${selected.length} Selected`;

    if(!selected.length){
      $('semester-configurations').innerHTML=`
        <div class="empty-state-card">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
          <h4>No Semesters Selected</h4>
          <p>Please choose one or more semesters above (1 to 8) to configure course allocations and faculty assignments.</p>
        </div>`;
      return;
    }

    $('semester-configurations').innerHTML=selected.map(semester=>{
      const dbCourses=state.options.courses.filter(c=>c.department_id===dept&&c.semester===semester);
      const customCourses=state.customCourses.filter(c=>c.department_id===dept&&c.semester===semester);
      const allCourses=[...dbCourses,...customCourses];

      return `<section class="semester-card" data-semester="${semester}">
        <div class="semester-card-header">
          <div class="semester-card-title-group">
            <h3>Semester ${semester} — Courses</h3>
            <span class="semester-course-badge">${allCourses.length} Course${allCourses.length===1?'':'s'}</span>
          </div>
          <div class="semester-card-controls">
            <div class="semester-section-input-wrap">
              <span>Cohort Section:</span>
              <input class="semester-section" value="A" maxlength="10" placeholder="A">
            </div>
            <button type="button" class="btn btn-secondary btn-sm add-custom-course-btn" data-semester="${semester}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              <span>+ Add Course</span>
            </button>
          </div>
        </div>
        <div class="semester-courses-list">
          ${allCourses.length ? allCourses.map(courseRow).join('') : '<p class="muted" style="padding:10px;">No registered courses found for this semester. Click "+ Add Course" to add required subjects.</p>'}
        </div>
      </section>`;
    }).join('');
  }

  function payload(){
    return {
      department_id: Number($('builder-department').value),
      academic_year: $('builder-year').value,
      working_days: [...$('builder-days').querySelectorAll('input:checked')].map(x=>x.value),
      day_start_time: $('builder-start').value,
      day_end_time: $('builder-end').value,
      slot_minutes: Number($('builder-slot').value),
      semesters: [...$('semester-configurations').querySelectorAll('.semester-card')].map(card=>({
        semester: Number(card.dataset.semester),
        section: (card.querySelector('.semester-section').value.trim() || 'A'),
        courses: [...card.querySelectorAll('.course-setup')].filter(row=>row.querySelector('.course-enabled').checked).map(row=>({
          course_id: Number(row.dataset.courseId),
          teacher_id: Number(row.querySelector('.course-teacher').value),
          credit_hours: Number(row.dataset.creditHours),
          weekly_sessions: Number(row.querySelector('.course-sessions').value),
          session_duration_minutes: Number(row.querySelector('.course-duration').value),
          class_type: row.querySelector('.course-room-type').value.includes('Lab')?'Lab':'Lecture',
          required_room_type: row.querySelector('.course-room-type').value,
          room_ids: [...row.querySelector('.course-rooms').selectedOptions].map(x=>Number(x.value)),
          meetings: [...row.querySelectorAll('.meeting-setup')].map(m=>({
            meeting_index: Number(m.dataset.meetingIndex),
            day: m.querySelector('.meeting-day').value || null,
            start_time: m.querySelector('.meeting-start').value || null,
            end_time: m.querySelector('.meeting-end').value || null,
            teacher_id: Number(m.querySelector('.meeting-teacher').value) || null,
            room_id: Number(m.querySelector('.meeting-room').value) || null
          })).filter(m => m.day && m.start_time && m.end_time && m.room_id)
        }))
      }))
    };
  }

  function check(p){
    const e=[];
    if(!p.department_id) e.push('Please select a department.');
    if(!p.academic_year) e.push('Please select an academic year.');
    if(!p.working_days.length) e.push('Please select at least one working day.');
    if(!p.semesters.length) e.push('Please select at least one semester.');
    p.semesters.forEach(s=>{
      if(!s.courses.length) e.push(`Semester ${s.semester} has no enabled courses. Enable or add at least one course.`);
      s.courses.forEach(c=>{
        if(!c.teacher_id) e.push(`Please assign a faculty member for course #${c.course_id} in Semester ${s.semester}.`);
        if(!c.room_ids.length) e.push(`Please select at least one eligible room for course #${c.course_id} in Semester ${s.semester}.`);
      });
    });
    return e;
  }

  const flat=d=>d.courses.flatMap(c=>c.sessions.map(s=>({...s,course:c})));

  function conflicts(items){
    $('draft-conflicts').hidden=!items?.length;
    $('draft-conflicts').innerHTML=(items||[]).map(i=>`
      <article class="draft-conflict">
        <b>⚠️ ${esc(i.course||i.code||'Schedule Conflict')}</b>
        <span>${esc(i.reason||i.message)}</span>
        ${i.teacher?`<span><strong>Teacher:</strong> ${esc(i.teacher)}</span>`:''}
        ${i.room?`<span><strong>Room:</strong> ${esc(i.room)}</span>`:''}
        ${i.possible_adjustment?`<span><strong>Suggested Adjustment:</strong> ${esc(i.possible_adjustment)}</span>`:''}
      </article>`).join('');
  }

  function stage(n){
    document.querySelectorAll('.stage-track li').forEach((x,i)=>{
      x.classList.toggle('active',i<=n);
    });
  }

  function getCourseBadgeStyle(code, type) {
    let hash = 0;
    for (let i = 0; i < code.length; i++) {
      hash = code.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash % 360);
    const isLab = (type || '').toLowerCase().includes('lab');
    return {
      borderLeft: `4px solid hsl(${hue}, 70%, ${isLab ? '45%' : '52%'})`,
      badgeBg: `hsl(${hue}, 85%, 95%)`,
      badgeColor: `hsl(${hue}, 90%, 28%)`
    };
  }

  function grid(d){
    const rows=flat(d);
    const slots=[...new Map(rows.map(x=>[`${x.start_time}-${x.end_time}`,{start:x.start_time,end:x.end_time}])).values()].sort((a,b)=>a.start.localeCompare(b.start));
    
    if(!rows.length){
      $('timetable-grid').innerHTML=`
        <div class="empty-state-card" style="padding: 48px 24px; background: transparent; border: none;">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/></svg>
          <h4 style="font-size: 16px; margin: 8px 0 4px; color: var(--ink-800);">No Sessions Scheduled Yet</h4>
          <p style="color: var(--ink-500); font-size: 13px;">Click <strong>Generate Timetable</strong> above to automatically allocate conflict-free slots, or edit sessions directly.</p>
        </div>`;
      return;
    }

    const cells=new Map(rows.map(x=>[`${x.day}|${x.start_time}|${x.end_time}`,x]));

    $('timetable-grid').innerHTML=`
      <table class="timetable-grid">
        <thead>
          <tr>
            <th class="grid-time-head">
              <div class="th-content-wrap">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                <span>Day / Time</span>
              </div>
            </th>
            ${slots.map(s=>`
              <th>
                <div class="slot-time-header">
                  <span class="slot-time-range">${s.start} — ${s.end}</span>
                </div>
              </th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${d.configuration.working_days.map(day=>`
            <tr>
              <th class="day-row-header">
                <span class="day-name">${day}</span>
              </th>
              ${slots.map(s=>{
                const x=cells.get(`${day}|${s.start}|${s.end}`);
                if (!x) return '<td class="empty-cell"><div class="grid-empty-dash">—</div></td>';
                const style = getCourseBadgeStyle(x.course.course_code, x.course.class_type);
                return `<td class="occupied-cell">
                  <button class="session-cell" data-session-id="${x.session_id}" style="border-left: ${style.borderLeft};" title="Click to modify session (${x.course.course_code})">
                    <div class="session-top">
                      <span class="session-code-badge" style="background: ${style.badgeBg}; color: ${style.badgeColor};">${esc(x.course.course_code)}</span>
                      <span class="session-type-pill ${x.course.class_type.toLowerCase().includes('lab') ? 'is-lab' : 'is-lecture'}">${esc(x.course.class_type)}</span>
                    </div>
                    <div class="session-title" title="${esc(x.course.course_title)}">${esc(x.course.course_title)}</div>
                    <div class="session-bottom">
                      <div class="session-meta-row session-teacher">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        <span>${esc(x.course.teacher)}</span>
                      </div>
                      <div class="session-meta-row session-room-tag">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16M9 9h1M9 13h1M9 17h1M14 9h1M14 13h1M14 17h1"/></svg>
                        <span>${esc(x.room)}</span>
                      </div>
                    </div>
                  </button>
                </td>`;
              }).join('')}
            </tr>`).join('')}
        </tbody>
      </table>`;
  }

  function render(d){
    state.active=d;
    $('draft-workspace').hidden=false;
    $('draft-title').textContent=`${d.department} — Semester ${d.semester} (Section ${d.section})`;
    $('draft-state').textContent=d.status.toUpperCase();
    $('draft-state').className='status-pill '+d.status.toLowerCase();
    
    $('draft-tabs').innerHTML=state.drafts.map(x=>`
      <button data-draft-id="${x.timetable_id}" class="${x.timetable_id===d.timetable_id?'active':''}">
        Semester ${x.semester} · Section ${esc(x.section)}
      </button>`).join('');

    $('draft-generate').disabled=d.status!=='Draft';
    $('draft-approve').disabled=d.status!=='Draft'||!flat(d).length;
    $('draft-publish').disabled=d.status!=='Approved';
    
    grid(d);
    stage(d.status==='Published'?6:d.status==='Approved'?5:flat(d).length?3:2);
  }

  async function call(path,method='POST',body){
    clear();
    $('draft-message').textContent='Processing timetable engine constraints…';
    const r=await fetch(API+path,{
      method,
      headers:{Authorization:'Bearer '+token(),...(body?{'Content-Type':'application/json'}:{})},
      body:body?JSON.stringify(body):undefined
    });
    const data=await r.json();
    if(!r.ok){
      const d=data.detail;
      conflicts(d?.issues||[]);
      throw Error(typeof d==='string'?d:d?.message||'Operation failed.');
    }
    if(data.draft){
      state.drafts=state.drafts.map(x=>x.timetable_id===data.draft.timetable_id?data.draft:x);
      render(data.draft);
    }
    conflicts(data.conflicts||data.issues||data.validation||[]);
    $('draft-message').textContent=data.message||(!data.success?'Timetable generated with constraint notices.':'Completed successfully.');
    return data;
  }

  async function load(){
    try{
      const r=await fetch(API+'/options',{headers:{Authorization:'Bearer '+token()}});
      const d=await r.json();
      if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:d.detail?.message||'Unable to load university options.');
      
      state.options=d;
      $('builder-department').innerHTML='<option value="">Choose Department…</option>'+d.departments.map(x=>opt(x.id,x.name)).join('');
      $('builder-year').innerHTML='<option value="">Choose Academic Year…</option>'+d.academic_years.map(x=>opt(x,x)).join('');
      
      $('builder-days').innerHTML=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].map(x=>{
        const isDefault=d.defaults.working_days.includes(x);
        return `<label class="check-chip-label ${isDefault?'is-checked':''}">
          <input type="checkbox" value="${x}" ${isDefault?'checked':''}>
          <span>${x}</span>
        </label>`;
      }).join('');

      // Semester 1 to 8 support
      const allSemesters = [1, 2, 3, 4, 5, 6, 7, 8];
      $('builder-semesters').innerHTML=allSemesters.map(x=>`
        <label class="check-chip-label">
          <input type="checkbox" value="${x}">
          <span>Semester ${x}</span>
        </label>`).join('');

      $('builder-start').value=d.defaults.day_start_time;
      $('builder-end').value=d.defaults.day_end_time;
      $('builder-slot').value=d.defaults.slot_minutes;
      $('builder-status').textContent=`Live Connected: ${d.departments.length} departments, ${d.courses.length} courses, ${d.teachers.length} teachers, ${d.rooms.length} rooms.`;
    }catch(e){
      $('builder-status').textContent=e.message;
      errors(e.message);
    }
  }

  // Event Listeners
  $('builder-department').onchange=renderSemesters;
  $('builder-semesters').onchange=e=>{
    if(e.target.tagName==='INPUT'){
      e.target.closest('.check-chip-label').classList.toggle('is-checked', e.target.checked);
    }
    renderSemesters();
  };

  $('builder-days').onchange=e=>{
    if(e.target.tagName==='INPUT'){
      e.target.closest('.check-chip-label').classList.toggle('is-checked', e.target.checked);
    }
  };

  $('semester-configurations').onchange=e=>{
    if(e.target.classList.contains('course-room-type')){
      const row=e.target.closest('.course-setup');
      const type=e.target.value;
      const rooms=state.options.rooms.filter(r=>r.room_type===type);
      row.querySelector('.course-rooms').innerHTML=rooms.map((r,idx)=>opt(r.id,`${r.code} (${r.capacity} seats)`,idx===0)).join('');
      row.querySelectorAll('.meeting-room').forEach(sel => {
        sel.innerHTML='<option value="">Auto Room</option>'+rooms.map(r=>opt(r.id,`${r.code} (${r.capacity} seats)`)).join('');
      });
    }
    if(e.target.classList.contains('course-sessions')){
      const card=e.target.closest('.course-setup');
      const courseId=Number(card.dataset.courseId);
      const count=Math.max(1, Math.min(12, Number(e.target.value)||1));
      const teacherId=Number(card.querySelector('.course-teacher').value);
      const roomType=card.querySelector('.course-room-type').value;
      const defaultRoomId=Number(card.querySelector('.course-rooms').value);
      card.querySelector('.meetings-list').innerHTML=renderMeetingRows(courseId, count, teacherId, roomType, defaultRoomId);
    }
    if(e.target.classList.contains('course-teacher')){
      const card=e.target.closest('.course-setup');
      const teacherId=Number(e.target.value);
      card.querySelectorAll('.meeting-teacher').forEach(sel => {
        if(!sel.value) sel.innerHTML='<option value="">Same Faculty</option>'+state.options.teachers.map(t=>opt(t.id,t.name,t.id===teacherId)).join('');
      });
    }
    if(e.target.classList.contains('course-enabled')){
      const card=e.target.closest('.course-setup-card');
      card.classList.toggle('is-active-course', e.target.checked);
    }
  };

  // Add room dialog trigger
  $('semester-configurations').onclick=e=>{
    const roomBtn=e.target.closest('.trigger-add-room-btn');
    if(roomBtn){
      const setupCard=roomBtn.closest('.course-setup');
      const roomTypeSel=setupCard?.querySelector('.course-room-type');
      if(roomTypeSel) $('modal-room-type').value=roomTypeSel.value;
      $('modal-room-code').value='';
      $('modal-room-name').value='';
      $('modal-room-capacity').value='50';
      $('modal-room-error').hidden=true;
      $('add-room-dialog').showModal();
      return;
    }
    const btn=e.target.closest('.add-custom-course-btn');
    if(!btn)return;
    const sem=Number(btn.dataset.semester);
    $('modal-target-semester').value=sem;
    $('modal-course-title').value='';
    $('modal-course-code').value='';
    $('modal-course-credits').value='3';
    $('modal-course-sessions').value='3';
    
    const deptId=Number($('builder-department').value);
    const teachers=state.options.teachers.filter(t=>t.department_id===deptId);
    $('modal-course-teacher').innerHTML='<option value="">Choose Teacher…</option>'+teachers.map(t=>opt(t.id,t.name)).join('');
    
    const type=$('modal-course-type').value;
    $('modal-course-rooms').innerHTML=state.options.rooms.filter(r=>r.room_type===type).map(r=>opt(r.id,`${r.code} (${r.capacity} seats)`)).join('');
    
    $('add-course-dialog').showModal();
  };

  // Add Room form submit
  $('add-room-form').onsubmit=async e=>{
    e.preventDefault();
    const code=$('modal-room-code').value.trim().toUpperCase();
    const name=$('modal-room-name').value.trim();
    const type=$('modal-room-type').value;
    const capacity=Number($('modal-room-capacity').value);
    const errBox=$('modal-room-error');
    errBox.hidden=true;

    if(!code || !capacity){
      errBox.innerHTML='<b>Validation Error</b> Room code and capacity are required.';
      errBox.hidden=false;
      return;
    }

    $('modal-room-submit').disabled=true;
    try{
      const res=await fetch(API+'/rooms',{
        method:'POST',
        headers:{Authorization:'Bearer '+token(),'Content-Type':'application/json'},
        body:JSON.stringify({room_code:code,room_name:name,room_type:type,capacity:capacity})
      });
      const data=await res.json();
      if(!res.ok){
        throw Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Failed to create room.');
      }
      // Add newly created room to state.options.rooms
      state.options.rooms.push(data.room);
      $('add-room-dialog').close();
      // Re-render course rows to include the new room
      renderSemesters();
    }catch(err){
      errBox.innerHTML=`<b>Failed to add room:</b> ${esc(err.message)}`;
      errBox.hidden=false;
    }finally{
      $('modal-room-submit').disabled=false;
    }
  };

  $('modal-course-type').onchange=e=>{
    const type=e.target.value;
    $('modal-course-rooms').innerHTML=state.options.rooms.filter(r=>r.room_type===type).map(r=>opt(r.id,`${r.code} (${r.capacity} seats)`)).join('');
  };

  // Add custom course form submit
  $('add-course-form').onsubmit=e=>{
    e.preventDefault();
    const sem=Number($('modal-target-semester').value);
    const deptId=Number($('builder-department').value);
    const title=$('modal-course-title').value.trim();
    const code=$('modal-course-code').value.trim();
    const credits=Number($('modal-course-credits').value);
    const teacherId=Number($('modal-course-teacher').value);
    const type=$('modal-course-type').value;
    
    if(!deptId){
      alert('Please select a department first.');
      $('add-course-dialog').close();
      return;
    }

    // Reuse a matching course ID if existing or generate a transient negative ID for custom additions
    const matchingCourse=state.options.courses.find(c=>c.department_id===deptId && c.semester===sem && c.code.toLowerCase()===code.toLowerCase());
    const courseId = matchingCourse ? matchingCourse.id : -Math.floor(Date.now() % 1000000);

    const newCourse = {
      id: courseId,
      department_id: deptId,
      semester: sem,
      code: code,
      title: title,
      credit_hours: credits,
      course_type: type.includes('Lab') ? 'Lab' : 'Lecture',
      assigned_teacher_id: teacherId,
      is_custom: true
    };

    state.customCourses.push(newCourse);
    $('add-course-dialog').close();
    renderSemesters();
  };

  $('builder-toggle').onclick=()=>{
    const show=$('builder-form').hidden;
    $('builder-form').hidden=!show;
    $('builder-toggle').querySelector('span').textContent=show?'Toggle Setup (Expanded)':'Toggle Setup (Collapsed)';
  };

  $('builder-form').onsubmit=async e=>{
    e.preventDefault();
    clear();
    const p=payload();
    const bad=check(p);
    if(bad.length)return errors(bad);
    
    $('builder-submit').disabled=true;
    try{
      const r=await fetch(API+'/drafts',{
        method:'POST',
        headers:{Authorization:'Bearer '+token(),'Content-Type':'application/json'},
        body:JSON.stringify(p)
      });
      const d=await r.json();
      if(!r.ok){
        const x=d.detail;
        throw Error(typeof x==='string'?x:(x?.errors||[x?.message]).join(' '));
      }
      state.drafts=d.drafts;
      render(d.drafts[0]);
      $('builder-status').textContent=d.message;
      stage(2);
      $('draft-workspace').scrollIntoView({behavior:'smooth'});
    }catch(x){
      errors(x.message);
    }finally{
      $('builder-submit').disabled=false;
    }
  };

  $('draft-tabs').onclick=e=>{
    const b=e.target.closest('[data-draft-id]');
    if(b) render(state.drafts.find(x=>x.timetable_id===Number(b.dataset.draftId)));
  };

  $('draft-generate').onclick=()=>call(`/drafts/${state.active.timetable_id}/generate`).catch(e=>$('draft-message').textContent=e.message);
  
  $('draft-validate').onclick=()=>call(`/drafts/${state.active.timetable_id}/validate`).then(x=>{
    if(x.success){
      stage(4);
      $('draft-message').textContent='Validation check passed. All faculty and rooms are conflict-free. Ready for approval.';
    }
  }).catch(e=>$('draft-message').textContent=e.message);

  $('draft-edit-config').onclick=()=>{
    $('builder-form').hidden=false;
    $('builder-form').scrollIntoView({behavior:'smooth'});
  };

  $('draft-print').onclick=()=>{
    window.print();
  };

  $('draft-approve').onclick=()=>call(`/drafts/${state.active.timetable_id}/approve`).catch(e=>$('draft-message').textContent=e.message);
  $('draft-publish').onclick=()=>call(`/drafts/${state.active.timetable_id}/publish`).catch(e=>$('draft-message').textContent=e.message);

  $('timetable-grid').onclick=e=>{
    const b=e.target.closest('[data-session-id]');
    if(!b||state.active.status!=='Draft')return;
    const x=flat(state.active).find(v=>v.session_id===Number(b.dataset.sessionId));
    state.editing=x;
    
    $('session-day').innerHTML=state.active.configuration.working_days.map(d=>opt(d,d,d===x.day)).join('');
    $('session-start').value=x.start_time;
    $('session-end').value=x.end_time;
    $('session-teacher').innerHTML=state.options.teachers.map(t=>opt(t.id,t.name,t.id===x.course.teacher_id)).join('');
    
    const allowed=new Set(x.course.room_ids);
    $('session-room').innerHTML=state.options.rooms.filter(r=>allowed.has(r.id)).map(r=>opt(r.id,`${r.code} (${r.capacity} seats)`,r.id===x.room_id)).join('');
    $('session-dialog').showModal();
  };

  $('session-cancel').onclick=()=>$('session-dialog').close();
  $('session-form').onsubmit=e=>{
    e.preventDefault();
    const x=state.editing;
    $('session-dialog').close();
    call(`/sessions/${x.session_id}`,'PATCH',{
      day_of_week:$('session-day').value,
      start_time:$('session-start').value,
      end_time:$('session-end').value,
      teacher_id:Number($('session-teacher').value),
      room_id:Number($('session-room').value)
    }).then(()=>stage(4)).catch(e=>$('draft-message').textContent=e.message);
  };

  load();
})();

