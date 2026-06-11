import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api/client'

export default function AdminLogin(){
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')
  const [email, setEmail] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [otpCode, setOtpCode] = useState('')
  const [newPass, setNewPass] = useState('')

  async function onSubmit(e){
    e.preventDefault()
    setMsg('')
    const res = await fetch('/api/accounts/token/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username,password}) })
    if(res.ok){
      const data = await res.json()
      api.setToken(data.access)
      setMsg('Logged in')
      nav('/admin/dashboard')
    } else {
      setMsg('Login failed')
    }
  }

  async function requestAdminOtp(){
    setMsg('')
    if(!email) return setMsg('Enter your admin email first')
    const res = await fetch('/api/accounts/admin/request-otp/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email}) })
    const data = await res.json().catch(()=>null)
    if(res.ok){ setOtpSent(true); setMsg('OTP sent to your email') }
    else setMsg(data?.detail || 'Failed to send OTP')
  }

  async function verifyAdminOtp(e){
    e.preventDefault()
    setMsg('')
    const res = await fetch('/api/accounts/admin/verify-otp/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, code: otpCode, password: newPass}) })
    const data = await res.json().catch(()=>null)
    if(res.ok){ setMsg('Password reset. You can now login.'); setOtpSent(false); setOtpCode(''); setNewPass('') }
    else setMsg(data?.detail || 'Failed to reset password')
  }

  return (
    <div className="container py-4" style={{maxWidth: 520}}>
      <h1 className="h4 mb-3">Admin Login</h1>
      <form onSubmit={onSubmit} className="vstack gap-2">
        <input className="form-control" placeholder="Username" value={username} onChange={e=>setUsername(e.target.value)} />
        <input className="form-control" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="btn btn-primary" type="submit">Login</button>
      </form>
      {msg && <div className="small mt-2">{msg}</div>}

      <div className="card mt-4">
        <div className="card-body">
          <h5 className="card-title">Forgot Password?</h5>
          <div className="d-flex gap-2">
            <input className="form-control" type="email" placeholder="Admin Email" value={email} onChange={e=>setEmail(e.target.value)} />
            <button className="btn btn-outline-secondary" onClick={requestAdminOtp}>Send OTP</button>
          </div>
          {otpSent && (
            <form onSubmit={verifyAdminOtp} className="row g-2 mt-3">
              <div className="col-4"><input className="form-control" placeholder="OTP Code" value={otpCode} onChange={e=>setOtpCode(e.target.value)} required /></div>
              <div className="col-8"><input className="form-control" type="password" placeholder="New Password" value={newPass} onChange={e=>setNewPass(e.target.value)} required /></div>
              <div className="col-12"><button className="btn btn-success" type="submit">Verify & Reset</button></div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
