/**
 * FindIt — Admin Moderation Portal Logic (admin.js)
 */

let adminItems = [];
let adminPasscode = sessionStorage.getItem('findit_admin_passcode') || '';

document.addEventListener('DOMContentLoaded', () => {
  if (adminPasscode) {
    verifyAndInitAdmin(adminPasscode);
  } else {
    showLoginView();
  }
});

function showLoginView() {
  document.getElementById('admin-login-view').style.display = 'block';
  document.getElementById('admin-dashboard-view').style.display = 'none';
  document.getElementById('admin-logout-btn').style.display = 'none';
}

function showDashboardView() {
  document.getElementById('admin-login-view').style.display = 'none';
  document.getElementById('admin-dashboard-view').style.display = 'block';
  document.getElementById('admin-logout-btn').style.display = 'inline-flex';
}

async function handleAdminLogin(e) {
  e.preventDefault();
  const input = document.getElementById('admin-passcode');
  const code = input.value.trim();

  if (!code) {
    showToast('Please enter an admin passkey.', 'error');
    return;
  }

  await verifyAndInitAdmin(code);
}

async function verifyAndInitAdmin(passcodeToTest) {
  try {
    const res = await fetch('/api/admin/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ passcode: passcodeToTest })
    });

    if (!res.ok) {
      sessionStorage.removeItem('findit_admin_passcode');
      adminPasscode = '';
      showToast('Incorrect passkey. Default passkey is admin123', 'error');
      showLoginView();
      return;
    }

    // Success
    adminPasscode = passcodeToTest;
    sessionStorage.setItem('findit_admin_passcode', adminPasscode);
    showDashboardView();
    showToast('Admin panel unlocked.', 'success');
    loadAdminItems();
  } catch (err) {
    console.error(err);
    showToast('Server connection failed.', 'error');
  }
}

function adminLogout() {
  sessionStorage.removeItem('findit_admin_passcode');
  adminPasscode = '';
  document.getElementById('admin-passcode').value = '';
  showLoginView();
  showToast('Logged out of admin console.', 'info');
}

async function loadAdminItems() {
  const tbody = document.getElementById('admin-table-body');
  tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">Loading admin listings...</td></tr>';

  try {
    const res = await fetch('/api/admin/items', {
      headers: {
        'X-Admin-Passcode': adminPasscode
      }
    });

    if (res.status === 401) {
      showToast('Session expired or invalid passkey.', 'error');
      adminLogout();
      return;
    }

    if (!res.ok) throw new Error('Could not fetch items');

    const data = await res.json();
    adminItems = data.items || [];
    filterAdminTable();
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--lost-color); padding: 2rem;">Error loading items: ${err.message}</td></tr>`;
    showToast(err.message, 'error');
  }
}

function filterAdminTable() {
  const query = (document.getElementById('admin-search-input')?.value || '').toLowerCase().trim();
  const typeFilter = document.getElementById('admin-type-filter')?.value || 'all';
  const statusFilter = document.getElementById('admin-status-filter')?.value || 'all';

  const filtered = adminItems.filter(item => {
    // Type match
    if (typeFilter !== 'all' && item.type !== typeFilter) return false;

    // Status match
    if (statusFilter === 'active' && item.is_returned !== 0) return false;
    if (statusFilter === 'returned' && item.is_returned !== 1) return false;

    // Search text match
    if (query) {
      const matchText = `${item.title} ${item.description} ${item.location} ${item.contact_name} ${item.contact_info}`.toLowerCase();
      if (!matchText.includes(query)) return false;
    }

    return true;
  });

  renderAdminTable(filtered);
}

function renderAdminTable(items) {
  const tbody = document.getElementById('admin-table-body');

  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-muted);">No listings match the current filters.</td></tr>';
    return;
  }

  tbody.innerHTML = items.map(item => {
    const isLost = item.type === 'lost';
    const isReturned = item.is_returned === 1;

    const typeBadge = isLost
      ? '<span class="badge badge-lost">🔴 Lost</span>'
      : '<span class="badge badge-found">🟢 Found</span>';

    const statusBadge = isReturned
      ? '<span class="badge badge-returned">✓ Returned</span>'
      : '<span class="badge" style="background:#f1f5f9; color:#475569;">Active</span>';

    const returnToggleLabel = isReturned ? 'Reopen' : 'Mark Returned';

    const photoIndicator = item.image_url
      ? `<a href="${item.image_url}" target="_blank" style="color: var(--primary); font-size: 0.8rem; display: block; margin-top: 0.2rem;">📷 View Attached Photo</a>`
      : '';

    return `
      <tr>
        <td style="font-weight: 700; color: var(--text-muted);">#${item.id}</td>
        <td>${typeBadge}</td>
        <td>
          <strong style="color: var(--text-main); display: block;">${escapeHtml(item.title)}</strong>
          <span style="font-size: 0.82rem; color: var(--text-muted); display: block; max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${escapeHtml(item.description)}
          </span>
          ${photoIndicator}
        </td>
        <td><span class="badge" style="background:#f8fafc; border: 1px solid #e2e8f0; color:#334155;">${escapeHtml(item.category)}</span></td>
        <td style="font-size: 0.85rem;">
          <div>📍 ${escapeHtml(item.location)}</div>
          <div style="color: var(--text-muted);">📅 ${escapeHtml(item.date_event)}</div>
        </td>
        <td style="font-size: 0.85rem;">
          <strong>${escapeHtml(item.contact_name)}</strong>
          <div style="color: var(--primary);">${escapeHtml(item.contact_info)}</div>
        </td>
        <td>${statusBadge}</td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-sm btn-outline" style="margin-right: 0.35rem;" onclick="adminToggleStatus(${item.id})">
            ${returnToggleLabel}
          </button>
          <button class="btn btn-sm btn-danger" onclick="adminDeleteItem(${item.id}, '${escapeHtml(item.title).replace(/'/g, "\\'")}')">
            Delete
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

async function adminToggleStatus(itemId) {
  try {
    const res = await fetch(`/api/items/${itemId}/toggle-returned`, {
      method: 'POST'
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to update item');

    showToast(data.message, 'success');
    loadAdminItems();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function adminDeleteItem(itemId, title) {
  const confirmed = confirm(`Are you sure you want to permanently delete listing #${itemId} ("${title}")?\n\nThis cannot be undone.`);
  if (!confirmed) return;

  try {
    const res = await fetch(`/api/admin/items/${itemId}`, {
      method: 'DELETE',
      headers: {
        'X-Admin-Passcode': adminPasscode
      }
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to delete listing');

    showToast(data.message, 'success');
    loadAdminItems();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
