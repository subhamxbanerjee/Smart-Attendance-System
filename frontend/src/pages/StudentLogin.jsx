import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api/client'

export default function StudentLogin(){
  const nav = useNavigate()
  const [usn, setUsn] = useState('')
  const [msg, setMsg] = useState('')

  async function usnOnlyLogin(){
    setMsg('')
    if(!usn) return setMsg('Enter USN first')
    const res = await fetch('/api/accounts/student/login-usn-nopass/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({usn}) })
    const data = await res.json().catch(()=>null)
    if(res.ok){ api.setToken(data.access); setMsg('Logged in'); nav('/student/portal') }
    else setMsg(data?.detail || 'Login failed')
  }

  

  return (
    <div className="container py-4" style={{maxWidth: 560}}>
      <h1 className="h4 mb-3">Student Login (USN only)</h1>
      <div className="vstack gap-2">
        <input className="form-control" placeholder="USN" value={usn} onChange={e=>setUsn(e.target.value)} />
        <div className="d-flex gap-2">
          <button className="btn btn-primary" onClick={usnOnlyLogin}>Login</button>
        </div>
      </div>

      {msg && <div className="small mt-2">{msg}</div>}
    </div>
  )
}
