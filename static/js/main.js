// Language toggle
function setLang(lang) {
  document.querySelectorAll('[data-en]').forEach(el => {
    el.textContent = lang === 'ta' ? (el.dataset.ta || el.dataset.en) : el.dataset.en;
  });
  document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelector(`.lang-btn[onclick="setLang('${lang}')"]`).classList.add('active');
  localStorage.setItem('devabhoomi_lang', lang);
}

// Restore language on load
document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('devabhoomi_lang');
  if (saved === 'ta') setLang('ta');

  // Live stats ticker
  fetchStats();
  setInterval(fetchStats, 30000);
});

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    const els = {
      temples: document.querySelector('.stat-item:nth-child(1) .stat-number'),
      farmers: document.querySelector('.stat-item:nth-child(3) .stat-number'),
      matches: document.querySelector('.stat-item:nth-child(5) .stat-number'),
      waste:   document.querySelector('.stat-item:nth-child(7) .stat-number'),
    };
    if (els.temples) els.temples.textContent = data.temples;
    if (els.farmers) els.farmers.textContent = data.farmers;
    if (els.matches) els.matches.textContent = data.matches;
    if (els.waste)   els.waste.textContent = data.total_waste_kg + 'kg';
  } catch(e) {}
}
