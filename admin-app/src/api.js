const BASE = window.location.origin

export function getToken() {
  return localStorage.getItem('admin_token') || ''
}

export function setToken(v) {
  localStorage.setItem('admin_token', v || '')
}

function adminHeaders() {
  return { 'Content-Type': 'application/json', 'X-Admin-Token': getToken() }
}

async function handle(res, fallback) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || fallback || `请求失败 ${res.status}`)
  }
  return res.json().catch(() => ({}))
}

export async function fetchChapters() {
  const res = await fetch(`${BASE}/api/chapters?full=1`)
  return handle(res, '题库读取失败')
}

export async function saveChapter(unit) {
  const res = await fetch(`${BASE}/api/chapters`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify(unit)
  })
  return handle(res, '保存失败')
}

export async function removeChapter(id) {
  const res = await fetch(`${BASE}/api/chapters/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: adminHeaders()
  })
  return handle(res, '删除失败')
}

export async function reorderChapters(ids) {
  const res = await fetch(`${BASE}/api/chapters/reorder`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ ids })
  })
  return handle(res, '排序失败')
}

export async function fetchStudents() {
  const res = await fetch(`${BASE}/api/users`, { headers: adminHeaders() })
  return handle(res, '口令不对或读取失败')
}

export async function removeStudent(uid) {
  const res = await fetch(`${BASE}/api/users/${encodeURIComponent(uid)}`, {
    method: 'DELETE',
    headers: adminHeaders()
  })
  return handle(res, '删除失败')
}

export const ADMIN_BASE = BASE
