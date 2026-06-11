const api = {
  token: (typeof localStorage !== 'undefined' ? localStorage.getItem('jwt_access') : null),
  setToken(t){ this.token = t; try{ localStorage.setItem('jwt_access', t) }catch(e){} },
  headers(extra={}){
    const h = { 'Content-Type': 'application/json', ...extra }
    if(this.token){ h['Authorization'] = 'Bearer ' + this.token }
    return h
  },
  async get(url){
    const res = await fetch(url, { headers: this.headers() })
    return res
  },
  async post(url, body){
    const res = await fetch(url, { method:'POST', headers: this.headers(), body: JSON.stringify(body) })
    return res
  },
  async patch(url, body){
    const res = await fetch(url, { method:'PATCH', headers: this.headers(), body: JSON.stringify(body) })
    return res
  },
  async put(url, body){
    const res = await fetch(url, { method:'PUT', headers: this.headers(), body: JSON.stringify(body) })
    return res
  },
  async delete(url){
    const res = await fetch(url, { method:'DELETE', headers: this.headers() })
    return res
  },
  async postForm(url, formData){
    const headers = this.token ? { 'Authorization': 'Bearer ' + this.token } : {}
    const res = await fetch(url, { method:'POST', headers, body: formData })
    return res
  }
}

export default api
