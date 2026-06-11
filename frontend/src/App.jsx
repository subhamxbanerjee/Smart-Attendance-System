import React, { useEffect, useState } from 'react'
import { Link, Route, Routes, useNavigate } from 'react-router-dom'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import StudentLogin from './pages/StudentLogin'
import StudentPortal from './pages/StudentPortal'
import SetupPassword from './pages/SetupPassword'
import api from './api/client'

function Nav(){
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand" to="/">Attendance</Link>
        <div className="collapse navbar-collapse">
          <ul className="navbar-nav me-auto">
            <li className="nav-item"><Link className="nav-link" to="/admin">Admin</Link></li>
            <li className="nav-item"><Link className="nav-link" to="/student">Student</Link></li>
          </ul>
        </div>
      </div>
    </nav>
  )
}

function Home(){
  const [adminExists, setAdminExists] = useState(null) // null = loading, true/false loaded
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ username:'', email:'', password:'' })
  const [msg, setMsg] = useState('')
  const [newAdmin, setNewAdmin] = useState({ username:'', email:'', password:'' })
  const [adminMsg, setAdminMsg] = useState('')
  const [invite, setInvite] = useState({ email:'', code:'', username:'', password:'' })
  const [inviteMsg, setInviteMsg] = useState('')
  const [inviteSent, setInviteSent] = useState(false)

  useEffect(()=>{
    let cancelled = false
    async function check(){
      try{
        const res = await fetch('/api/accounts/admin/exists/')
        const data = await res.json()
        if(!cancelled) setAdminExists(Boolean(data?.exists))
      }catch(e){
        if(!cancelled) setAdminExists(true) // fail safe: hide creation form
      }
    }
    check()
    return ()=>{ cancelled = true }
  },[])

  async function onCreateAdditionalAdmin(e){
    e.preventDefault()
    setAdminMsg('')
    try{
      const res = await fetch('/api/accounts/admin/create/', { method:'POST', headers: api.headers(), body: JSON.stringify(newAdmin) })
      const data = await res.json().catch(()=>null)
      if(res.ok){
        setAdminMsg('Admin created successfully')
        setNewAdmin({ username:'', email:'', password:'' })
      } else {
        setAdminMsg((data && data.detail) || 'Failed to create admin')
      }
    }catch(err){
      setAdminMsg('Failed to create admin')
    }
  }

  async function requestAdminInvite(e){
    e.preventDefault()
    setInviteMsg('')
    try{
      // Endpoint not implemented on backend yet; keep UX non-blocking
      // const res = await fetch('/api/accounts/admin/invite/', { method:'POST', headers: api.headers(), body: JSON.stringify({email: invite.email}) })
      // if(res.ok){
      //   setInviteSent(true); setInviteMsg('OTP sent to email')
      // } else { setInviteMsg('Failed to send OTP') }
      setInviteSent(true)
      setInviteMsg('Demo: OTP flow placeholder (backend not implemented)')
    }catch(err){
      setInviteMsg('Failed to send OTP')
    }
  }

  async function verifyAdminInvite(e){
    e.preventDefault()
    setInviteMsg('')
    try{
      // Endpoint not implemented; simulate success
      setInviteMsg('Demo: Verification placeholder (backend not implemented)')
    }catch(err){
      setInviteMsg('Verification failed')
    }
  }

  async function onCreateAdmin(e){
    e.preventDefault()
    setMsg('')
    setCreating(true)
    try{
      const res = await fetch('/api/accounts/admin/setup/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(form) })
      if(res.ok){
        setMsg('Admin created. You can now login.')
        setAdminExists(true)
      } else {
        const d = await res.json().catch(()=>({detail:'Failed to create admin'}))
        setMsg(d.detail || 'Failed to create admin')
      }
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      {/* Hero Section */}
      <section className="py-5" style={{background: 'linear-gradient(90deg, #0d6efd 0%, #6610f2 100%)'}}>
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-7 text-white">
              <h1 className="display-6 fw-semibold">Student Attendance System</h1>
              <p className="lead mb-4">Modern, secure, and fast attendance tracking with live face recognition, session management, and automated SMS alerts.</p>
              <div className="d-flex gap-2">
                <Link className="btn btn-light btn-lg" to="/admin">Admin Login</Link>
                <Link className="btn btn-outline-light btn-lg" to="/student">Student Portal</Link>
              </div>
            </div>
            <div className="col-lg-5 d-none d-lg-block text-end">
              <img alt="illustration" src="https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?q=80&w=1200&auto=format&fit=crop" className="img-fluid rounded shadow" />
            </div>
          </div>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="py-5">
        <div className="container">
          <div className="row g-4">
            <div className="col-md-6">
              <div className="card h-100 shadow-sm border-0">
                <div className="card-body p-4">
                  <h5 className="card-title">Admin Portal</h5>
                  <p className="text-muted">Manage students, upload photos, start live sessions, and send absence notifications.</p>
                  <Link className="btn btn-primary" to="/admin">Go to Admin</Link>
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="card h-100 shadow-sm border-0">
                <div className="card-body p-4">
                  <h5 className="card-title">Student Portal</h5>
                  <p className="text-muted">Login with your USN to view attendance grouped by session and get updates.</p>
                  <Link className="btn btn-outline-primary" to="/student">Go to Student</Link>
                </div>
              </div>
            </div>
          </div>

          {/* Admin Invite (Email-gated initial admin creation) */}
          {adminExists === false && (
            <div className="card shadow-sm border-0 mt-5">
              <div className="card-body p-4">
                <h5 className="card-title">Request Admin Access</h5>
                <p className="text-muted small">Enter your authorized email to receive a one-time code. Only whitelisted emails are allowed.</p>
                <form onSubmit={requestAdminInvite} className="row g-2" style={{maxWidth: 720}}>
                  <div className="col-md-6"><input className="form-control" type="email" placeholder="Email" value={invite.email} onChange={e=>setInvite({...invite, email:e.target.value})} required /></div>
                  <div className="col-md-6"><button className="btn btn-primary" type="submit">Send OTP</button></div>
                </form>
                {inviteSent && (
                  <form onSubmit={verifyAdminInvite} className="row g-2 mt-3" style={{maxWidth: 720}}>
                    <div className="col-md-3"><input className="form-control" placeholder="OTP Code" value={invite.code} onChange={e=>setInvite({...invite, code:e.target.value})} required /></div>
                    <div className="col-md-3"><input className="form-control" placeholder="Username (optional)" value={invite.username} onChange={e=>setInvite({...invite, username:e.target.value})} /></div>
                    <div className="col-md-6"><input className="form-control" type="password" placeholder="Password" value={invite.password} onChange={e=>setInvite({...invite, password:e.target.value})} required /></div>
                    <div className="col-12"><button className="btn btn-success" type="submit">Verify & Create Admin</button></div>
                  </form>
                )}
                {inviteMsg && <div className="small mt-2">{inviteMsg}</div>}
              </div>
            </div>
          )}

          {/* Create Additional Admin (visible when authenticated) */}
          {api.token && (
            <div className="card shadow-sm border-0 mt-4">
              <div className="card-body p-4">
                <h5 className="card-title">Create Admin Account</h5>
                <p className="text-muted small">You must be an admin. If not, this action will be denied.</p>
                <form onSubmit={onCreateAdditionalAdmin} className="row g-2" style={{maxWidth: 720}}>
                  <div className="col-md-4"><input className="form-control" placeholder="Username" value={newAdmin.username} onChange={e=>setNewAdmin({...newAdmin, username:e.target.value})} required /></div>
                  <div className="col-md-4"><input className="form-control" type="email" placeholder="Email" value={newAdmin.email} onChange={e=>setNewAdmin({...newAdmin, email:e.target.value})} required /></div>
                  <div className="col-md-4"><input className="form-control" type="password" placeholder="Password" value={newAdmin.password} onChange={e=>setNewAdmin({...newAdmin, password:e.target.value})} required /></div>
                  <div className="col-12"><button className="btn btn-success" type="submit">Create Admin</button></div>
                </form>
                {adminMsg && <div className="small mt-2">{adminMsg}</div>}
              </div>
            </div>
          )}

          {/* Highlights */}
          <div className="row g-4 mt-5">
            <div className="col-md-4">
              <div className="p-4 rounded border h-100">
                <h6 className="fw-semibold mb-2">Live Face Recognition</h6>
                <div className="text-muted small">OpenCV camera capture with DeepFace embeddings and fast cosine matching.</div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="p-4 rounded border h-100">
                <h6 className="fw-semibold mb-2">Session Management</h6>
                <div className="text-muted small">Start/stop sessions, auto-mark present within 5 minutes, and notify absentees.</div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="p-4 rounded border h-100">
                <h6 className="fw-semibold mb-2">Reliable Notifications</h6>
                <div className="text-muted small">SMS via Twilio and email OTP for secure student onboarding.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-4 border-top">
        <div className="container d-flex justify-content-between small text-muted">
          <span>© {new Date().getFullYear()} Student Attendance System</span>
          <span>Built with Django, React, and DeepFace</span>
        </div>
      </footer>
    </div>
  )
}

export default function App(){
  return (
    <div>
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/admin" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/student" element={<StudentLogin />} />
        <Route path="/student/portal" element={<StudentPortal />} />
        <Route path="/student/setup-password" element={<SetupPassword />} />
      </Routes>
    </div>
  )
}
