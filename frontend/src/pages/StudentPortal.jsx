import React, { useEffect, useMemo, useState } from 'react'
import api from '../api/client'

export default function StudentPortal(){
  const [history, setHistory] = useState([])

  async function loadHistory(){
    const res = await fetch('/api/accounts/student/attendance-history/', { headers: api.headers() })
    if(res.ok){ setHistory(await res.json()) }
    else alert('Please login first')
  }

  useEffect(()=>{ loadHistory() }, [])

  const grouped = useMemo(()=>{
    const map = {}
    for(const r of history){
      const key = r.session_name || 'Session'
      if(!map[key]) map[key] = []
      map[key].push(r)
    }
    return map
  }, [history])

  const sessionNames = Object.keys(grouped)

  const summary = useMemo(()=>{
    const total = history.length
    const present = history.filter(r=>r.status==='present').length
    const absent = history.filter(r=>r.status==='absent').length
    const pct = total ? Math.round((present/total)*100) : 0
    return { total, present, absent, pct }
  }, [history])

  return (
    <div className="container py-4">
      <h1 className="h4 mb-3">My Attendance</h1>
      <button className="btn btn-outline-primary btn-sm" onClick={loadHistory}>Refresh</button>

      <div className="row g-3 mt-2">
        <div className="col-6 col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <div className="small text-muted">Total Records</div>
              <div className="h5 mb-0">{summary.total}</div>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <div className="small text-muted">Present</div>
              <div className="h5 mb-0 text-success">{summary.present}</div>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <div className="small text-muted">Absent</div>
              <div className="h5 mb-0 text-danger">{summary.absent}</div>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3">
          <div className="card text-center">
            <div className="card-body">
              <div className="small text-muted">Attendance %</div>
              <div className="h5 mb-0">{summary.pct}%</div>
            </div>
          </div>
        </div>
      </div>

      {history.length === 0 && (
        <div className="alert alert-info mt-3 small">Click "Load / Refresh" to view your attendance records.</div>
      )}

      {sessionNames.map((name)=>{
        const recs = grouped[name]
        const present = recs.filter(r=>r.status === 'present').length
        const absent = recs.filter(r=>r.status === 'absent').length
        return (
          <div key={name} className="card mt-3">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">{name}</h5>
                <div className="small text-muted">Present: {present} | Absent: {absent}</div>
              </div>
              <ul className="list-group small mt-3">
                {recs.map((r, idx)=> (
                  <li key={idx} className="list-group-item d-flex justify-content-between">
                    <span>{new Date(r.timestamp).toLocaleString()}</span>
                    <span className={`badge ${r.status==='present' ? 'bg-success' : 'bg-danger'}`}>{r.status?.toUpperCase()}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )
      })}
    </div>
  )
}
