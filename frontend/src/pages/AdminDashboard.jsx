import React, { useEffect, useState, useRef } from 'react'
import api from '../api/client'

export default function AdminDashboard() {
  const [students, setStudents] = useState([])
  const [form, setForm] = useState({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' })
  const [sessionId, setSessionId] = useState('')
  const [sessName, setSessName] = useState('')
  const [records, setRecords] = useState([])
  const [upload, setUpload] = useState({ usn: '', file: null })
  const [sessions, setSessions] = useState([])
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [sessionSummary, setSessionSummary] = useState({ present: 0, absent: 0 })
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' })
  const [searchUsn, setSearchUsn] = useState('')
  const backendBase = (typeof window !== 'undefined' && window.location && /:\d{4}$/.test(window.location.port)) ? 'http://127.0.0.1:8001' : ''
  const [liveRunning, setLiveRunning] = useState(false)
  const [manageUsn, setManageUsn] = useState('')
  const [managePhotos, setManagePhotos] = useState([])
  const [manageLoading, setManageLoading] = useState(false)
  const [manageFile, setManageFile] = useState(null)
  const [weekForm, setWeekForm] = useState({
    week_start_date: '',          // YYYY-MM-DD
    days_to_create: [0, 1, 2, 3, 4],  // Mon-Fri
    session_name_prefix: 'Class',
    sessions_per_day: 6,
    first_session_start_time: '09:00',
    session_duration_minutes: 60,
    break_minutes_between_sessions: 10,
    is_active: true,
  })
  const [classes, setClasses] = useState([])
  const [classId, setClassId] = useState('')
  const [newClass, setNewClass] = useState({ name: '', section: '' })
  const [refreshing, setRefreshing] = useState(false)
  const [displayUsn, setDisplayUsn] = useState('')
  const uploadFileRef = useRef(null)

  function clearUploadForm() {
    setUpload({ usn: '', file: null })
    if (uploadFileRef.current) {
      uploadFileRef.current.value = ''
    }
  }

  async function loadStudents() {
    setRefreshing(true)
    // Append timestamp to prevent caching
    const res = await api.get(`/api/accounts/students/?t=${new Date().getTime()}`)
    if (res.ok) { setStudents(await res.json()) }
    setRefreshing(false)
  }

  async function handleRefresh() {
    setSearchUsn('')
    setDisplayUsn('')
    setEditingId(null)
    setEditForm({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' })
    setManageUsn('')
    setManagePhotos([])
    setManageFile(null)
    await loadStudents()
  }

  async function loadClasses() {
    try {
      const res = await api.get('/api/attendance/classes/')
      if (res.ok) {
        const data = await res.json()
        setClasses(data)
      }
    } catch (err) { /* ignore */ }
  }

  function startEdit(s) {
    setEditingId(s.id)
    setEditForm({
      usn: s.usn || '',
      name: s.name || '',
      student_phone: s.student_phone || '',
      parent_phone: s.parent_phone || '',
      email: s.email || ''
    })
  }

  async function saveEdit() {
    if (!editingId) return
    const payload = {
      usn: editForm.usn,
      name: editForm.name,
      student_phone: editForm.student_phone,
      parent_phone: editForm.parent_phone,
      email: editForm.email
    }
    const res = await api.patch(`/api/accounts/students/${editingId}/`, payload)
    if (res.ok) {
      setEditingId(null)
      setEditForm({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' })
      await loadStudents()
      alert('Student updated')
    } else {
      const d = await res.json().catch(() => null)
      alert(d?.detail || 'Failed to update')
    }
  }

  function cancelEdit() {
    setEditingId(null)
    setEditForm({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' })
  }

  async function toggleCanLogin(student) {
    const next = !student.can_login
    const res = await api.patch(`/api/accounts/students/${student.id}/`, { can_login: next })
    if (res.ok) { await loadStudents() }
    else alert('Failed to update permission')
  }

  async function loadStudentPhotos(usn) {
    setManageLoading(true)
    try {
      const res = await api.get(`/api/accounts/student/photos/?usn=${encodeURIComponent(usn)}`)
      if (res.ok) {
        const data = await res.json()
        setManagePhotos(data)
      }
    } finally {
      setManageLoading(false)
    }
  }

  function openPhotoManager(usn) {
    setManageUsn(usn)
    setManagePhotos([])
    setManageFile(null)
    loadStudentPhotos(usn)
  }

  async function deleteStudentPhoto(filename) {
    if (!manageUsn || !filename) return
    if (!confirm(`Delete photo ${filename}?`)) return
    const res = await api.post('/api/accounts/student/delete-photo/', { usn: manageUsn, filename })
    if (res.ok) {
      await loadStudentPhotos(manageUsn)
      alert('Deleted')
    } else {
      alert('Failed to delete')
    }
  }

  async function uploadManagedPhoto(e) {
    e.preventDefault()
    if (!manageUsn || !manageFile) return
    const fd = new FormData()
    fd.append('usn', manageUsn)
    fd.append('photo', manageFile)
    try {
      console.log("Uploading file...", manageFile);
      const res = await fetch('/api/accounts/student/upload-photo/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.token}`
          // Do NOT set Content-Type for FormData, browser does it
        },
        body: fd
      })
      console.log("Upload response status:", res.status);
      if (res.ok) {
        const data = await res.json()
        console.log("Upload success:", data);
        alert('Uploaded successfully')
        setManageFile(null)
        loadStudentPhotos(manageUsn)
      } else {
        const err = await res.text()
        console.error("Upload failed:", err);
        alert('Upload failed: ' + err)
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert('Error uploading: ' + error)
    }
  }

  async function sendStudentPasswordOtp(usn) {
    if (!usn) return
    const res = await api.post('/api/accounts/student/request-otp/', { usn })
    if (res.ok) {
      alert('OTP sent to student\'s email (if available)')
    } else {
      alert('Failed to send OTP')
    }
  }


  async function addStudent(e) {
    e.preventDefault()
    const res = await api.post('/api/accounts/students/', form)
    if (res.ok) { setForm({ usn: '', name: '', student_phone: '', parent_phone: '', email: '' }); loadStudents(); alert('Student added') }
    else alert('Failed to add')
  }



  async function stopSession() {
    if (!sessionId) return alert('Set session id')
    const res = await fetch(`/api/attendance/sessions/${sessionId}/stop/`, { method: 'POST', headers: api.headers() })
    if (res.ok) {
      alert('Stopped')
      await loadSessions()
    }
  }

  async function markAbsent() {
    if (!sessionId) return alert('Set session id')
    const res = await fetch(`/api/attendance/sessions/${sessionId}/mark_absent/`, { method: 'POST', headers: api.headers() })
    if (res.ok) { const d = await res.json(); alert('Absent marked for ' + d.marked_absent) }
  }



  async function loadRecords() {
    if (!sessionId) return alert('Set session id')
    const res = await api.get(`/api/attendance/records/?session=${sessionId}`)
    if (res.ok) {
      const data = await res.json()
      setRecords(data)
      const present = data.filter(r => r.status === 'present').length
      const absent = data.filter(r => r.status === 'absent').length
      setSessionSummary({ present, absent })
    }
  }

  async function loadSessions() {
    setLoadingSessions(true)
    try {
      const res = await api.get('/api/attendance/sessions/')
      if (res.ok) {
        let data = await res.json()
        // Active sessions first
        data = data.sort((a, b) => Number(b.is_active) - Number(a.is_active))
        setSessions(data)
        // If no sessionId selected but there is an active session, preselect first active
        if (!sessionId) {
          const active = data.find(s => s.is_active)
          if (active) setSessionId(String(active.id))
        }
      }
    } finally {
      setLoadingSessions(false)
    }
  }

  async function uploadPhoto(e) {
    e.preventDefault()
    if (!upload.usn || !upload.file) return alert('Fill both')
    const fd = new FormData()
    fd.append('usn', upload.usn)
    fd.append('photo', upload.file)

    try {
      console.log("Uploading file (Add Student)...", upload.file);
      const res = await fetch('/api/accounts/student/upload-photo/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${api.token}`
        },
        body: fd
      })
      console.log("Upload response status:", res.status);
      if (res.ok) {
        const data = await res.json()
        console.log("Upload success:", data);
        alert('Uploaded successfully')
        clearUploadForm()
        loadStudentPhotos(upload.usn)
      } else {
        const err = await res.text()
        console.error("Upload failed:", err);
        alert('Upload failed: ' + err)
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert('Error uploading: ' + error)
    }
  }

  async function buildEncodings() {
    const res = await fetch('/api/face/build-encodings/', { method: 'POST', headers: api.headers() })
    if (res.ok) alert('Encodings built')
  }

  async function startLive() {
    if (!sessionId) return alert('Set session id')
    const res = await fetch('/api/face/start/', { method: 'POST', headers: api.headers(), body: JSON.stringify({ session_id: Number(sessionId) }) })
    if (res.ok) {
      alert('Live started')
      setLiveRunning(true)
    }
  }

  async function stopLive() {
    const res = await fetch('/api/face/stop/', { method: 'POST', headers: api.headers() })
    if (res.ok) {
      alert('Live stopped')
      setLiveRunning(false)
    }
  }

  // Auto-poll for sessions every 5 seconds to detect auto-created sessions
  useEffect(() => {
    const interval = setInterval(() => {
      loadSessions(true); // Pass true to indicate background poll
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-refresh attendance records when session is active
  useEffect(() => {
    if (sessionId) {
      loadRecords();
      const interval = setInterval(loadRecords, 3000);
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  // Load students on mount so search works immediately
  useEffect(() => {
    loadStudents();
  }, [])

  async function loadSessions(isBackground = false) {
    if (!isBackground) setLoadingSessions(true)
    try {
      const res = await api.get('/api/attendance/sessions/')
      if (res.ok) {
        let data = await res.json()
        // Active sessions first
        data = data.sort((a, b) => Number(b.is_active) - Number(a.is_active))
        setSessions(data)

        // Auto-select the first active session if exists
        const active = data.find(s => s.is_active)
        if (active) {
          // If we're not already viewing this active session, switch to it
          if (sessionId !== String(active.id)) {
            setSessionId(String(active.id))
            // Also ensure live running state is true if session is active
            setLiveRunning(true)
          }
        } else {
          // No active session
          if (liveRunning) setLiveRunning(false)
        }
      }
    } finally {
      if (!isBackground) setLoadingSessions(false)
    }
  }

  // ... (keep existing helper functions like uploadPhoto, etc.) ...

  return (
    <div className="container py-4">
      <h1 className="h4 mb-3">Admin Dashboard</h1>

      {/* Status Banner */}


      <div className="row g-4">
        {/* Left Column: Students & Photos */}
        <div className="col-lg-5">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">Student Management</h5>

              {/* Add Student Form */}
              <h6 className="small text-muted mb-2">Add New Student</h6>
              <form onSubmit={addStudent} className="row g-2 mb-3">
                <div className="col-4"><input className="form-control form-control-sm" placeholder="USN" value={form.usn} onChange={e => setForm({ ...form, usn: e.target.value })} required /></div>
                <div className="col-8"><input className="form-control form-control-sm" placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
                <div className="col-6"><input className="form-control form-control-sm" placeholder="Student Phone" value={form.student_phone} onChange={e => setForm({ ...form, student_phone: e.target.value })} required /></div>
                <div className="col-6"><input className="form-control form-control-sm" placeholder="Parent Phone" value={form.parent_phone} onChange={e => setForm({ ...form, parent_phone: e.target.value })} required /></div>
                <div className="col-12"><input className="form-control form-control-sm" placeholder="Email (optional)" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></div>
                <div className="col-12"><button className="btn btn-success btn-sm w-100" type="submit">Add Student</button></div>
              </form>
              <hr />

              <div className="d-flex justify-content-between align-items-center mb-2">
                <button className="btn btn-outline-primary btn-sm" onClick={handleRefresh} disabled={refreshing}>
                  {refreshing ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                      Refreshing...
                    </>
                  ) : 'Refresh List'}
                </button>

                <form onSubmit={(e) => {
                  e.preventDefault();
                  setDisplayUsn(searchUsn);
                  setEditingId(null);
                }} className="d-flex gap-2 align-items-center">
                  <input className="form-control form-control-sm" placeholder="Enter USN" value={searchUsn} onChange={e => setSearchUsn(e.target.value)} style={{ width: '120px' }} />
                  <button className="btn btn-primary btn-sm" type="submit">Search</button>
                </form>
              </div>

              {/* Student List Table */}
              <div className="table-responsive" style={{ maxHeight: '500px' }}>
                <table className="table table-sm table-hover align-middle">
                  <thead className="table-light">
                    <tr>
                      <th>USN</th>
                      <th>Details</th>
                      <th className="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!displayUsn ? (
                      <tr><td colSpan="3" className="text-center text-muted py-4">Please enter USN to search</td></tr>
                    ) : students.filter(s => s.usn.toLowerCase().includes(displayUsn.toLowerCase())).length === 0 ? (
                      <tr><td colSpan="3" className="text-center text-muted small py-4">No student found</td></tr>
                    ) : students.filter(s => s.usn.toLowerCase().includes(displayUsn.toLowerCase())).map(s => (
                      <tr key={s.usn}>
                        <td style={{ verticalAlign: 'top' }}>
                          {editingId === s.id ? (
                            <input className="form-control form-control-sm mb-1" style={{ width: '80px' }} value={editForm.usn} onChange={e => setEditForm({ ...editForm, usn: e.target.value })} placeholder="USN" />
                          ) : <strong className="small">{s.usn}</strong>}
                        </td>
                        <td>
                          {editingId === s.id ? (
                            <div className="d-flex flex-column gap-1">
                              <input className="form-control form-control-sm" placeholder="Name" value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} />
                              <input className="form-control form-control-sm" placeholder="Email" value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} />
                              <input className="form-control form-control-sm" placeholder="Student Phone" value={editForm.student_phone} onChange={e => setEditForm({ ...editForm, student_phone: e.target.value })} />
                              <input className="form-control form-control-sm" placeholder="Parent Phone" value={editForm.parent_phone} onChange={e => setEditForm({ ...editForm, parent_phone: e.target.value })} />
                            </div>
                          ) : (
                            <div className="small">
                              <div className="fw-bold">{s.name}</div>
                              <div className="text-muted">{s.email}</div>
                              <div className="text-muted">S: {s.student_phone} | P: {s.parent_phone}</div>
                            </div>
                          )}
                        </td>
                        <td className="text-end" style={{ verticalAlign: 'top' }}>
                          <div className="d-flex gap-1 justify-content-end">
                            {editingId === s.id ? (
                              <>
                                <button type="button" className="btn btn-success btn-xs" onClick={saveEdit}>Save</button>
                                <button type="button" className="btn btn-secondary btn-xs" onClick={cancelEdit}>Cancel</button>
                              </>
                            ) : (
                              <>
                                <button type="button" className="btn btn-outline-primary btn-xs" onClick={() => startEdit(s)}>Edit</button>
                                <button type="button" className="btn btn-outline-secondary btn-xs" onClick={() => sendStudentPasswordOtp(s.usn)}>OTP</button>
                                <button type="button" className="btn btn-outline-dark btn-xs" onClick={() => openPhotoManager(s.usn)}>Photos</button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Photo Manager (Keep existing logic) */}
              {manageUsn && (
                <div className="mt-3 border-top pt-3">
                  <h6>Photos: {manageUsn}</h6>
                  <form onSubmit={uploadManagedPhoto} className="d-flex gap-2 mb-2">
                    <input className="form-control form-control-sm" type="file" onChange={e => setManageFile(e.target.files?.[0])} />
                    <button className="btn btn-sm btn-primary">Upload</button>
                  </form>
                  <div className="d-flex flex-wrap gap-2">
                    {managePhotos.map(p => (
                      <div key={p.filename} className="position-relative">
                        <img src={`${backendBase}${p.url}`} style={{ width: 60, height: 60, objectFit: 'cover' }} />
                        <button className="btn btn-sm btn-danger position-absolute top-0 end-0 p-0" style={{ width: 20, height: 20, lineHeight: 1 }} onClick={() => deleteStudentPhoto(p.filename)}>×</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Live Feed & Attendance */}
        <div className="col-lg-7">
          {/* Live Feed removed by user request */}

          {/* Attendance List */}

          {/* Attendance List */}
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <span>Attendance Log ({records.length})</span>
              <button className="btn btn-sm btn-outline-primary py-0" onClick={loadRecords} disabled={!sessionId}>Refresh</button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive" style={{ maxHeight: '400px' }}>
                <table className="table table-striped mb-0">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Student</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r, idx) => (
                      <tr key={idx}>
                        <td>{new Date(r.timestamp).toLocaleTimeString()}</td>
                        <td>{r.student_detail?.name} ({r.student_detail?.usn})</td>
                        <td>
                          <span className={`badge bg-${r.status === 'present' ? 'success' : 'danger'}`}>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {records.length === 0 && (
                      <tr><td colSpan="3" className="text-center text-muted py-3">No records yet</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Controls Section */}
      <div className="card mt-4">
        <div className="card-header bg-light d-flex justify-content-between align-items-center">
          <strong>Manual Controls & Management</strong>
          <span className="badge bg-secondary">Manual Mode</span>
        </div>
        <div className="card-body">
          <div className="row g-4">
            {/* Photo Upload */}
            <div className="col-md-4">
              <h6 className="card-title">Upload Student Photo/Video</h6>
              <form onSubmit={uploadPhoto} className="row g-2">
                <div className="col-12"><input className="form-control form-control-sm" placeholder="USN" value={upload.usn} onChange={e => setUpload({ ...upload, usn: e.target.value })} required /></div>
                <div className="col-12"><input className="form-control form-control-sm" type="file" accept="image/*,video/*" ref={uploadFileRef} onChange={e => setUpload({ ...upload, file: e.target.files?.[0] || null })} required /></div>
                <div className="col-6"><button className="btn btn-secondary btn-sm w-100" type="submit">Upload</button></div>
                <div className="col-6"><button className="btn btn-outline-secondary btn-sm w-100" type="button" onClick={clearUploadForm}>Refresh</button></div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
