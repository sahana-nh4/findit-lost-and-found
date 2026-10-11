/**
 * FindIt — Community Lost & Found Portal
 * Main Frontend Logic (app.js)
 */

let allItems = [];
let currentFilter = {
  tab: 'all',
  search: '',
  category: 'all',
  status: 'all'
};
let activeDetailItem = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  // Set default date in report form to today
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('report-date');
  if (dateInput) dateInput.value = today;

  // Initialize search & filter event listeners
  setupFilterListeners();

  // Load initial statistics and listings
  fetchStats();
  loadItems();
});

// Category Icons Dictionary (SVG paths)
const categoryIcons = {
  'Electronics': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="4" y="4" width="16" height="12" rx="2"/><path d="M12 16v4m-4 0h8"/></svg>',
  'Wallets & Bags': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/><path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/><circle cx="18" cy="12" r="1"/></svg>',
  'Keys': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="7.5" cy="15.5" r="4.5"/><path d="m21 3-9.5 9.5m5.5-5.5 2 2m-4 0 2 2"/></svg>',
  'Documents & Books': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  'Pets': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M10 5.172C10 3.782 8.423 2.679 6.5 3c-2.823.47-4.113 6.006-4 7 .107.94 1.177 1 2 1 2.5 0 5.5-1.5 5.5-5.828zM14 5.172c0-1.39 1.577-2.493 3.5-2.172 2.823.47 4.113 6.006 4 7-.107.94-1.177 1-2 1-2.5 0-5.5-1.5-5.5-5.828zM12 14c-3.5 0-6 2-6 5 0 1 1 2 3 2h6c2 0 3-1 3-2 0-3-2.5-5-6-5z"/></svg>',
  'Clothing & Accessories': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>',
  'Jewelry': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M6 3h12l4 6-10 12L2 9l4-6z"/></svg>',
  'Other': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/></svg>'
};

// ==================== METRICS & DATA FETCHING ====================

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-total').textContent = data.total ?? 0;
    document.getElementById('stat-lost').textContent = data.lost ?? 0;
    document.getElementById('stat-found').textContent = data.found ?? 0;
    document.getElementById('stat-returned').textContent = data.returned ?? 0;
  } catch (err) {
    console.error('Failed to load portal stats', err);
  }
}

async function loadItems() {
  const grid = document.getElementById('items-grid');
  grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">Loading community listings...</div>';

  const params = new URLSearchParams();
  if (currentFilter.search.trim()) {
    params.append('search', currentFilter.search.trim());
  }

  // Handle Tab filter vs Status filter
  if (currentFilter.tab === 'lost') {
    params.append('type', 'lost');
  } else if (currentFilter.tab === 'found') {
    params.append('type', 'found');
  } else if (currentFilter.tab === 'returned') {
    params.append('status', 'returned');
  }

  if (currentFilter.category && currentFilter.category !== 'all') {
    params.append('category', currentFilter.category);
  }

  if (currentFilter.status && currentFilter.status !== 'all' && currentFilter.tab !== 'returned') {
    params.append('status', currentFilter.status);
  }

  try {
    const res = await fetch(`/api/items?${params.toString()}`);
    if (!res.ok) throw new Error('Could not retrieve items');
    const data = await res.json();
    allItems = data.items || [];
    renderItems(allItems);
  } catch (err) {
    console.error(err);
    grid.innerHTML = `
      <div class="empty-state">
        <h3>Could not load listings</h3>
        <p>There was a problem reaching the FindIt server. Please check your connection and try refreshing.</p>
        <button class="btn btn-primary" onclick="loadItems()">Try Again</button>
      </div>
    `;
    showToast('Failed to load items. Please try again.', 'error');
  }
}

function renderItems(items) {
  const grid = document.getElementById('items-grid');
  const countBadge = document.getElementById('items-count-display');
  countBadge.textContent = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;

  if (!items || items.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3>No matching listings found</h3>
        <p>Try adjusting your search terms or filters, or be the first to report this item to our community.</p>
        <button class="btn btn-primary" onclick="openReportModal()">+ Report New Item</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = items.map(item => {
    const isLost = item.type === 'lost';
    const isReturned = item.is_returned === 1;
    const catIcon = categoryIcons[item.category] || categoryIcons['Other'];

    const mediaHtml = item.image_url 
      ? `<img src="${item.image_url}" alt="${escapeHtml(item.title)}" loading="lazy">`
      : `<div class="placeholder-image">${catIcon}<span class="placeholder-category">${escapeHtml(item.category)}</span></div>`;

    const statusBadge = isReturned
      ? `<span class="badge badge-returned">✓ Reunited</span>`
      : isLost
        ? `<span class="badge badge-lost">🔴 Lost</span>`
        : `<span class="badge badge-found">🟢 Found</span>`;

    const returnBtnLabel = isReturned ? 'Reopen Listing' : 'Mark as Reunited';
    const returnBtnClass = isReturned ? 'btn-outline' : 'btn-return';

    return `
      <div class="item-card ${isReturned ? 'returned' : ''}">
        <div class="item-card-media">
          ${mediaHtml}
          <div class="badge-overlay-container">
            ${statusBadge}
          </div>
          <div class="badge-category">${escapeHtml(item.category)}</div>
        </div>
        <div class="item-card-body">
          <h3 class="item-card-title">${escapeHtml(item.title)}</h3>
          
          <div class="item-meta">
            <div class="meta-row">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/></svg>
              <span>${escapeHtml(item.location)}</span>
            </div>
            <div class="meta-row">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>
              <span>Date: ${escapeHtml(item.date_event)}</span>
            </div>
          </div>

          <p class="item-card-desc">${escapeHtml(item.description)}</p>

          <div class="item-card-footer">
            <button class="btn btn-sm btn-outline" onclick="openDetailsModal(${item.id})">
              Details & Contact
            </button>
            <button class="btn btn-sm ${returnBtnClass}" onclick="handleToggleReturn(${item.id})">
              ${returnBtnLabel}
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ==================== SEARCH & FILTERS ====================

function setupFilterListeners() {
  const searchInput = document.getElementById('search-input');
  let debounceTimeout = null;

  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      currentFilter.search = e.target.value;
      loadItems();
    }, 250);
  });

  const categorySelect = document.getElementById('category-filter');
  categorySelect.addEventListener('change', (e) => {
    currentFilter.category = e.target.value;
    loadItems();
  });

  const statusSelect = document.getElementById('status-filter');
  statusSelect.addEventListener('change', (e) => {
    currentFilter.status = e.target.value;
    loadItems();
  });
}

function setQuickTab(tab) {
  currentFilter.tab = tab;

  // Update tabs visual state
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
  });

  // Update view title
  const titleMap = {
    'all': 'Community Listings',
    'lost': 'Lost Items Seeking Owners',
    'found': 'Found Items Awaiting Claim',
    'returned': 'Successfully Reunited Items'
  };
  document.getElementById('current-view-title').textContent = titleMap[tab] || 'Community Listings';

  loadItems();
}

function resetFilters() {
  document.getElementById('search-input').value = '';
  document.getElementById('category-filter').value = 'all';
  document.getElementById('status-filter').value = 'all';
  currentFilter.search = '';
  currentFilter.category = 'all';
  currentFilter.status = 'all';
  setQuickTab('all');
}

// ==================== REPORT ITEM FORM & MODAL ====================

function openReportModal(defaultType = 'lost') {
  selectReportType(defaultType);
  document.getElementById('report-modal').classList.add('open');
}

function closeReportModal() {
  document.getElementById('report-modal').classList.remove('open');
  document.getElementById('report-form').reset();
  clearPhoto();
}

function selectReportType(type) {
  document.getElementById('report-type').value = type;
  const lostBtn = document.getElementById('type-btn-lost');
  const foundBtn = document.getElementById('type-btn-found');
  const title = document.getElementById('report-modal-title');

  if (type === 'lost') {
    lostBtn.className = 'type-radio-btn selected-lost';
    foundBtn.className = 'type-radio-btn';
    title.textContent = 'Report a Lost Item';
  } else {
    lostBtn.className = 'type-radio-btn';
    foundBtn.className = 'type-radio-btn selected-found';
    title.textContent = 'Report a Found Item';
  }
}

function previewPhoto(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    showToast('Photo is larger than 5MB. Please choose a smaller image.', 'error');
    event.target.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('image-preview').src = e.target.result;
    document.getElementById('image-preview-container').style.display = 'inline-block';
  };
  reader.readAsDataURL(file);
}

function clearPhoto() {
  const input = document.getElementById('photo-input');
  if (input) input.value = '';
  const preview = document.getElementById('image-preview');
  if (preview) preview.src = '';
  const container = document.getElementById('image-preview-container');
  if (container) container.style.display = 'none';
}

async function handleReportSubmit(e) {
  e.preventDefault();
  const form = document.getElementById('report-form');
  const submitBtn = document.getElementById('report-submit-btn');

  const formData = new FormData(form);

  // Client-side quick check
  if (!formData.get('title') || !formData.get('location') || !formData.get('contact_info')) {
    showToast('Please fill out all required fields marked with *', 'error');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting report...';

  try {
    const res = await fetch('/api/items', {
      method: 'POST',
      body: formData
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.detail || 'Failed to submit report');
    }

    showToast(result.message || 'Item listed successfully!', 'success');
    closeReportModal();
    fetchStats();
    loadItems();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'An error occurred while submitting.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Publish Report';
  }
}

// ==================== DETAILS & CONTACT MODAL ====================

function openDetailsModal(itemId) {
  const item = allItems.find(i => i.id === itemId);
  if (!item) return;

  activeDetailItem = item;

  document.getElementById('modal-item-title').textContent = item.title;
  document.getElementById('modal-item-desc').textContent = item.description;
  document.getElementById('modal-item-location').textContent = item.location;
  document.getElementById('modal-item-date').textContent = item.date_event;

  // Badges
  const isLost = item.type === 'lost';
  const isReturned = item.is_returned === 1;
  const badgesContainer = document.getElementById('modal-item-badges');
  badgesContainer.innerHTML = `
    <span class="badge ${isLost ? 'badge-lost' : 'badge-found'}">${isLost ? '🔴 Lost Item' : '🟢 Found Item'}</span>
    <span class="badge" style="background: #f1f5f9; color: var(--text-main);">${escapeHtml(item.category)}</span>
    ${isReturned ? '<span class="badge badge-returned">✓ Reunited</span>' : ''}
  `;

  // Photo
  const photoContainer = document.getElementById('modal-photo-container');
  if (item.image_url) {
    photoContainer.innerHTML = `<img src="${item.image_url}" class="details-image" alt="${escapeHtml(item.title)}">`;
  } else {
    photoContainer.innerHTML = '';
  }

  // Reset contact reveal box
  document.getElementById('unmasked-contact-area').style.display = 'none';
  document.getElementById('reveal-contact-btn').style.display = 'inline-flex';

  // Toggle button inside modal
  const modalToggleBtn = document.getElementById('modal-toggle-return-btn');
  modalToggleBtn.textContent = isReturned ? 'Mark as Active' : 'Mark as Reunited';
  modalToggleBtn.className = isReturned ? 'btn btn-outline' : 'btn btn-return';

  document.getElementById('details-modal').classList.add('open');
}

function closeDetailsModal() {
  document.getElementById('details-modal').classList.remove('open');
  activeDetailItem = null;
}

async function revealContact() {
  if (!activeDetailItem) return;

  try {
    const res = await fetch(`/api/items/${activeDetailItem.id}/contact`);
    if (!res.ok) throw new Error('Could not retrieve contact information');
    const data = await res.json();

    document.getElementById('unmasked-name').textContent = data.contact_name;
    document.getElementById('unmasked-info').textContent = data.contact_info;

    // Build mailto or tel link if recognized
    const actionBtn = document.getElementById('unmasked-action-btn');
    if (data.contact_info.includes('@')) {
      actionBtn.href = `mailto:${data.contact_info}?subject=Regarding your FindIt report: ${encodeURIComponent(data.title)}`;
      actionBtn.textContent = 'Send Email';
    } else {
      actionBtn.href = `tel:${data.contact_info.replace(/[^0-9+]/g, '')}`;
      actionBtn.textContent = 'Call / Message';
    }

    document.getElementById('reveal-contact-btn').style.display = 'none';
    document.getElementById('unmasked-contact-area').style.display = 'block';
  } catch (err) {
    showToast(err.message || 'Failed to reveal contact', 'error');
  }
}

// ==================== RETURN / RESOLVE ACTIONS ====================

async function handleToggleReturn(itemId) {
  try {
    const res = await fetch(`/api/items/${itemId}/toggle-returned`, {
      method: 'POST'
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not update status');

    showToast(data.message, 'success');
    fetchStats();
    loadItems();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function toggleReturnFromModal() {
  if (!activeDetailItem) return;
  await handleToggleReturn(activeDetailItem.id);
  closeDetailsModal();
}

// ==================== UTILITY FUNCTIONS ====================

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
