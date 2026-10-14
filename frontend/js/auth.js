/* ─── ChildNutri AI — Auth helpers ──────────────────────────────────────── */
let _cachedUser = null;

async function getUser() {
  if (_cachedUser) return _cachedUser;
  try {
    _cachedUser = await API.get('/api/auth/me');
    return _cachedUser;
  } catch {
    return null;
  }
}

async function requireUser() {
  const user = await getUser();
  if (!user) {
    location.href = '/login.html';
    throw new Error('Not authenticated');
  }
  return user;
}

// Bind logout buttons
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[id="logout-btn"], [data-logout]').forEach(btn => {
    btn.addEventListener('click', async () => {
      try { await API.post('/api/auth/logout', {}); } catch {}
      _cachedUser = null;
      location.href = '/login.html';
    });
  });
});
