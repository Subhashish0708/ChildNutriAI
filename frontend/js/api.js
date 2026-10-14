/* ─── ChildNutri AI — API Client ─────────────────────────────────────────── */
const API = (() => {
  const BASE = '';  // same-origin: FastAPI serves frontend

  async function request(method, path, body, isForm = false) {
    const opts = {
      method,
      credentials: 'include',
    };
    if (body) {
      if (isForm) {
        opts.body = body;
      } else {
        opts.headers = { 'Content-Type': 'application/json' };
        opts.body = JSON.stringify(body);
      }
    }
    const res = await fetch(BASE + path, opts);
    if (res.status === 204) return null;
    let data;
    try { data = await res.json(); } catch { data = { detail: 'Non-JSON response' }; }
    if (!res.ok) {
      const msg = data?.detail || data?.message || `HTTP ${res.status}`;
      throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join('; ') : msg);
    }
    return data;
  }

  return {
    get:      (path)          => request('GET',    path),
    post:     (path, body)    => request('POST',   path, body),
    put:      (path, body)    => request('PUT',    path, body),
    patch:    (path, body)    => request('PATCH',  path, body),
    del:      (path)          => request('DELETE', path),
    postForm: (path, form)    => request('POST',   path, form, true),
  };
})();

/* Helpers */
function qs(key) {
  return new URLSearchParams(location.search).get(key);
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function setMessage(text, type = 'info') {
  const el = document.querySelector('[data-message], #global-msg, #assess-msg, #child-msg, .message');
  if (!el) return;
  el.textContent = text;
  el.className = `message ${type}`;
}
