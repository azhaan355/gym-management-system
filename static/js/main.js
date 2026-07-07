document.addEventListener('DOMContentLoaded', function () {
  const icons = {
    layout: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    dumbbell: '<path d="M6.5 6.5l11 11"/><path d="M21 14l-7 7"/><path d="M3 10l7-7"/><path d="M18 11l3-3"/><path d="M13 6l3-3"/><path d="M8 21l3-3"/><path d="M3 16l3-3"/>',
    badge: '<path d="M12 2l2.4 5 5.6.8-4 3.9.9 5.5L12 14.6 7.1 17.2l.9-5.5-4-3.9 5.6-.8L12 2z"/>',
    wallet: '<path d="M3 7h18v13H3z"/><path d="M16 12h5v4h-5a2 2 0 0 1 0-4z"/><path d="M3 7l3-4h12l3 4"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-7"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    'user-plus': '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M20 8v6M23 11h-6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    activity: '<path d="M22 12h-4l-3 8-6-16-3 8H2"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>',
    x: '<path d="M18 6L6 18M6 6l12 12"/>',
    check: '<path d="M20 6L9 17l-5-5"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>'
  };

  document.querySelectorAll('[data-icon]').forEach(function (el) {
    const name = el.dataset.icon;
    el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (icons[name] || icons.check) + '</svg>';
  });

  const sidebar = document.getElementById('sidebar');
  const mainWrap = document.getElementById('mainWrap');
  const toggleBtn = document.getElementById('toggleBtn');
  const overlay = document.getElementById('overlay');
  const themeBtn = document.getElementById('themeBtn');
  const html = document.documentElement;
  const mobile = () => window.innerWidth <= 768;

  html.setAttribute('data-theme', localStorage.getItem('flexfit-theme') || 'dark');
  themeBtn?.addEventListener('click', function () {
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('flexfit-theme', next);
  });

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('on');
  }

  toggleBtn?.addEventListener('click', function () {
    if (mobile()) {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('on');
    } else {
      sidebar.classList.toggle('collapsed');
      mainWrap.classList.toggle('wide');
    }
  });
  overlay?.addEventListener('click', closeSidebar);

  document.querySelectorAll('.nav-item').forEach(function (item) {
    item.addEventListener('click', function () {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      if (mobile()) closeSidebar();
    });
  });

  function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeModal(modal) {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-modal]').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn.dataset.openModal));
  });
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(modal); });
    modal.querySelectorAll('[data-close-modal]').forEach(btn => btn.addEventListener('click', () => closeModal(modal)));
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') document.querySelectorAll('.modal.open').forEach(closeModal);
  });

  function filterTable(tableId, term, status) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const needle = (term || '').toLowerCase();
    table.querySelectorAll('tbody tr').forEach(row => {
      const textMatch = row.textContent.toLowerCase().includes(needle);
      const statusMatch = !status || row.dataset.status === status;
      row.style.display = textMatch && statusMatch ? '' : 'none';
    });
  }
  document.querySelectorAll('[data-table-search]').forEach(input => {
    input.addEventListener('input', () => {
      const tableId = input.dataset.tableSearch;
      const filter = document.querySelector('[data-table-filter="' + tableId + '"]');
      filterTable(tableId, input.value, filter?.value);
    });
  });
  document.querySelectorAll('[data-table-filter]').forEach(select => {
    select.addEventListener('change', () => {
      const tableId = select.dataset.tableFilter;
      const input = document.querySelector('[data-table-search="' + tableId + '"]');
      filterTable(tableId, input?.value, select.value);
    });
  });
  document.getElementById('globalSearch')?.addEventListener('input', function () {
    filterTable('membersTable', this.value);
    filterTable('trainersTable', this.value);
    filterTable('trainerMembersTable', this.value);
  });

  document.querySelectorAll('.sortable th').forEach(function (th, index) {
    th.addEventListener('click', function () {
      const table = th.closest('table');
      const body = table.querySelector('tbody');
      const rows = Array.from(body.querySelectorAll('tr')).filter(row => row.children.length > 1);
      const dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
      th.dataset.dir = dir;
      rows.sort((a, b) => {
        const av = a.children[index]?.innerText.trim().toLowerCase() || '';
        const bv = b.children[index]?.innerText.trim().toLowerCase() || '';
        return dir === 'asc' ? av.localeCompare(bv, undefined, { numeric: true }) : bv.localeCompare(av, undefined, { numeric: true });
      });
      rows.forEach(row => body.appendChild(row));
    });
  });

  document.querySelectorAll('[data-count]').forEach(function (el) {
    const raw = el.dataset.count;
    const target = Number(raw);
    if (Number.isNaN(target)) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 28));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = el.textContent.includes('Rs') ? 'Rs ' + Math.round(target) : Math.round(target);
        clearInterval(timer);
      } else {
        el.textContent = el.textContent.includes('Rs') ? 'Rs ' + current : current;
      }
    }, 22);
  });

  const clock = document.getElementById('clockText');
  function tick() {
    if (!clock) return;
    clock.textContent = new Intl.DateTimeFormat('en-IN', {
      weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    }).format(new Date());
  }
  tick();
  setInterval(tick, 30000);

  const panel = document.getElementById('notificationPanel');
  document.getElementById('notificationBtn')?.addEventListener('click', () => panel?.classList.toggle('open'));
  document.getElementById('closeNotifications')?.addEventListener('click', () => panel?.classList.remove('open'));

  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = 'Saving...';
        btn.style.opacity = '.72';
      }
    });
  });

  document.getElementById('generateAi')?.addEventListener('click', function () {
    const goal = document.getElementById('aiGoal').value.trim() || 'general fitness';
    const output = document.getElementById('aiOutput');
    output.innerHTML = '<b>Starter plan for ' + goal + '</b><br>3 strength sessions, 2 mobility/cardio days, 7-8 hours sleep, and a protein-focused diet with vegetables at every major meal. Review progress weekly and adjust intensity gradually.';
  });

  window.addEventListener('resize', function () {
    if (!mobile()) closeSidebar();
    if (mobile()) {
      sidebar?.classList.remove('collapsed');
      mainWrap?.classList.remove('wide');
    }
  });
});
