import React, { useState } from 'react'

export default function SetupPassword(){
  const [form, setForm] = useState({ usn:'', username:'', email:'', password:'' })
  const [msg, setMsg] = useState('')

  async function onSubmit(e){
    e.preventDefault()
    setMsg('')
    const res = await fetch('/api/accounts/student/setup-password/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(form) })
    if(res.ok) setMsg('Password set. You can now login.')
    else setMsg('Failed to set password')
  }

  return (
    <div className="container py-4" style={{maxWidth: 680}}>
      <h1 className="h4 mb-3">Set / Reset Password</h1>
      <form onSubmit={onSubmit} className="row g-2">
        <div className="col-3"><input className="form-control" placeholder="USN" value={form.usn} onChange={e=>setForm({...form, usn:e.target.value})} required /></div>
        <div className="col-3"><input className="form-control" placeholder="Username" value={form.username} onChange={e=>setForm({...form, username:e.target.value})} required /></div>
        <div className="col-3"><input className="form-control" placeholder="Email (optional)" value={form.email} onChange={e=>setForm({...form, email:e.target.value})} /></div>
        <div className="col-3"><input className="form-control" placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form, password:e.target.value})} required /></div>
        <div className="col-12"><button className="btn btn-success" type="submit">Save Password</button></div>
      </form>
      {msg && <div className="small mt-2">{msg}</div>}
    </div>
  )
}
