'use strict';

const state = { profiles: [], selectedId: null, filter: 'all', rankings: null, activeDate: null };
const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function safeHref(value) {
  try { const u = new URL(value); return u.protocol === 'https:' ? esc(u.href) : '#'; } catch (_) { return '#'; }
}
function initials(name) {
  return String(name || '?').split(/\s+/).slice(0,2).map(v => v[0] || '').join('').toUpperCase();
}
function toneFor(id) {
  let total = 0; for (const c of String(id)) total += c.charCodeAt(0);
  return total % 6;
}
function avatar(p, extra = '') {
  return `<span class="avatar avatar-tone-${toneFor(p.id)} ${extra}">${esc(initials(p.name))}</span>`;
}
function personBadge(p) {
  return p.is_demo ? 'FICTIONAL DEMO' : 'CONSENTED PROFILE';
}
async function api(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  let data;
  try { data = await response.json(); } catch (_) { data = {}; }
  if (!response.ok) throw new Error((data.details && data.details.join('\n')) || data.error || `Request failed (${response.status})`);
  return data;
}
let toastTimer;
function toast(message) {
  const box = $('toast'); box.textContent = message; box.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => box.classList.remove('show'), 3200);
}
function filteredProfiles() {
  const q = $('profile-search').value.trim().toLowerCase();
  return state.profiles.filter(p => {
    if (state.filter === 'demo' && !p.is_demo) return false;
    if (state.filter === 'consented' && p.is_demo) return false;
    if (!q) return true;
    return [p.name, p.city, p.bio, ...(p.interests || []), ...(p.values || []), p.goal].join(' ').toLowerCase().includes(q);
  });
}
function renderProfiles() {
  const items = filteredProfiles();
  $('profiles-grid').innerHTML = items.map(p => `
    <button type="button" class="person-card ${state.selectedId === p.id ? 'selected' : ''}" data-person-id="${esc(p.id)}" aria-pressed="${state.selectedId === p.id}">
      <span class="card-arrow">↗</span>
      <div class="person-top">${avatar(p)}<div style="min-width:0"><div class="person-name">${esc(p.name)}</div><div class="person-meta">${esc(p.age)} · ${esc(p.city)}</div></div></div>
      <span class="person-badge">${personBadge(p)}</span>
      <p class="person-bio">${esc(p.bio)}</p>
      <div class="tag-row">${(p.interests || []).slice(0,3).map(t => `<span class="tag">${esc(t)}</span>`).join('')}${(p.interests || []).length > 3 ? `<span class="tag more">+${p.interests.length - 3}</span>` : ''}</div>
    </button>`).join('');
  $('empty-profiles').classList.toggle('hidden', items.length > 0);
  $('profiles-grid').classList.toggle('hidden', items.length === 0);
  document.querySelectorAll('.person-card').forEach(card => card.addEventListener('click', () => selectProfile(card.dataset.personId)));
  $('filter-all-count').textContent = state.profiles.length;
}
function populateDateSelects() {
  const opts = state.profiles.map(p => `<option value="${esc(p.id)}">${esc(p.name)} · ${esc(p.age)}</option>`).join('');
  const oldA = $('date-person-a').value, oldB = $('date-person-b').value;
  $('date-person-a').innerHTML = opts; $('date-person-b').innerHTML = opts;
  $('date-person-a').value = state.profiles.some(p => p.id === oldA) ? oldA : (state.profiles[0]?.id || '');
  const nextB = state.profiles.some(p => p.id === oldB) && oldB !== $('date-person-a').value ? oldB : (state.profiles.find(p => p.id !== $('date-person-a').value)?.id || '');
  $('date-person-b').value = nextB;
}
function needsCopy(p) {
  const map = {
    'long-term relationship': 'Has stated a preference for a long-term relationship; discuss pace, consistency and expectations directly.',
    'meaningful connection': 'Wants a meaningful connection; a good next step is to ask what emotional availability and connection look like to them.',
    'friendship first': 'Prefers friendship first; make space for a low-pressure start and avoid assuming romantic intent.',
    'casual dating': 'Has stated a casual-dating goal; clarity around expectations and boundaries is especially important.'
  };
  return map[p.goal] || 'Ask about expectations and boundaries directly.';
}
async function selectProfile(id) {
  state.selectedId = id; renderProfiles();
  const p = state.profiles.find(x => x.id === id); if (!p) return;
  $('detail-content').innerHTML = `<div class="detail-placeholder"><span class="placeholder-spark">✳</span><h3>Reading profile…</h3><p>Comparing stated interests, values and preferences.</p></div>`;
  try {
    const data = await api(`/api/rankings?profile_id=${encodeURIComponent(id)}`);
    renderDetail(p, data.rankings || []);
  } catch (e) {
    renderDetail(p, []); toast(e.message);
  }
}
function renderDetail(p, rankings) {
  let sources;
  if (p.is_demo) {
    sources = `<div class="source-note">Synthetic demo persona · no real social profiles or external sources are attached.</div>`;
  } else {
    sources = `<div class="detail-source-row"><a class="source-link" href="${safeHref(p.linkedin_url)}" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a><a class="source-link" href="${safeHref(p.instagram_url)}" target="_blank" rel="noopener noreferrer">Instagram ↗</a></div><div class="source-note" style="margin-top:8px">Links provided with consent; this app does not fetch their contents.</div>`;
  }
  const top = rankings.slice(0,3).map((r,i) => `<div class="detail-match"><span class="match-rank">0${i+1}</span><div><div class="detail-match-name">${esc(r.profile.name)}</div><div class="match-mini-bar"><span style="width:${r.score}%"></span></div></div><span class="match-score">${r.score}%</span></div>`).join('');
  $('detail-content').innerHTML = `
    <div class="detail-person-head">${avatar(p)}<div><div class="detail-person-name">${esc(p.name)}</div><div class="detail-person-meta">${esc(p.age)} · ${esc(p.city)} · ${esc(p.goal)}</div></div></div>
    <p class="detail-bio">${esc(p.bio)}</p>
    <div class="detail-block"><div class="detail-block-title">THEIR INTERESTS</div><div class="tag-row">${(p.interests || []).map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div></div>
    <div class="detail-block"><div class="detail-block-title">STATED VALUES</div><div class="tag-row">${(p.values || []).map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div></div>
    <div class="detail-block"><div class="detail-block-title">WHAT MATTERS TO THEM</div><div class="detail-copy">${esc(needsCopy(p))}<br><br><span style="color:#bda477">Conversation style:</span> ${esc(p.style)}. <span style="color:#bda477">Preferred age range:</span> ${esc(p.min_age)}–${esc(p.max_age)}.</div></div>
    <div class="detail-block"><div class="detail-block-title">SOURCE REFERENCES</div>${sources}</div>
    <div class="detail-block"><div class="detail-block-title">TOP RANKED MATCHES</div><div class="detail-ranking-list">${top || '<div class="source-note">Run the ranking engine to discover matches.</div>'}</div></div>
    <button type="button" class="button button-outline button-full" id="date-this-person">Meet their agent ↗</button>`;
  $('date-this-person').addEventListener('click', () => {
    $('date-person-a').value = p.id;
    if ($('date-person-b').value === p.id) $('date-person-b').value = state.profiles.find(x => x.id !== p.id)?.id || '';
    document.getElementById('date-lab').scrollIntoView({behavior:'smooth'});
    toast(`${p.name}'s agent is ready for a simulated date.`);
  });
}
function openAddModal() {
  $('add-modal').classList.remove('hidden'); document.body.style.overflow = 'hidden';
  setTimeout(() => $('add-profile-form').elements.name.focus(), 30);
}
function closeAddModal() { $('add-modal').classList.add('hidden'); document.body.style.overflow = ''; }
function renderDateResult(data) {
  const score = data.match.score;
  const dialogues = data.dialogue.map((d,i) => `<div class="dialogue-bubble ${i % 2 ? 'right' : ''}"><span class="bubble-speaker">${esc(d.speaker.toUpperCase())}</span>${esc(d.text)}</div>`).join('');
  $('date-result').classList.add('has-date');
  $('date-result').innerHTML = `
    <div class="date-result-head"><h3>${esc(data.a.name.split(' ')[0])} <span style="color:var(--gold)">×</span> ${esc(data.b.name.split(' ')[0])}</h3><div class="score-large">${score}<small> / 100</small></div></div>
    <div class="date-readout">${esc(data.readout)}</div>
    <div class="dialogue-list">${dialogues}</div>
    <div class="date-flags"><h4>WHAT THE AGENTS NOTICED</h4><ul>${data.green_flags.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>
    <div class="date-flags"><h4>A QUESTION FOR REAL LIFE</h4><div class="detail-copy">${esc(data.next_question)}</div></div>
    <p class="tiny-notice">${esc(data.notice)}</p>`;
}
function renderRankings(data) {
  state.rankings = data.rankings;
  const profilesById = Object.fromEntries(state.profiles.map(p => [p.id,p]));
  const entries = Object.entries(data.rankings || {}).sort((a,b) => (profilesById[a[0]]?.name || '').localeCompare(profilesById[b[0]]?.name || ''));
  $('rankings-content').innerHTML = entries.map(([id, matches]) => {
    const p = profilesById[id]; if (!p) return '';
    const safeMatches = matches.slice(0,3);
    return `<article class="rank-card"><div class="rank-card-head">${avatar(p)}<div style="min-width:0"><div class="rank-person-name">${esc(p.name)}</div><div class="rank-person-sub">Top ${safeMatches.length} suggested matches</div></div></div><div class="top-score">${safeMatches[0]?.score ?? '—'}<small> /100</small></div><div class="rank-card-bottom">${safeMatches.map((m,i) => `<div class="rank-match-row"><span class="rank-n">0${i+1}</span><span class="rank-match-name">${esc(m.profile.name)}</span><span class="rank-bar"><span style="width:${m.score}%"></span></span><span class="rank-match-score">${m.score}%</span></div>`).join('')}</div></article>`;
  }).join('');
  $('ranking-status').textContent = `${data.profile_count} profiles · ranked`;
}
async function runRankings() {
  const btn = $('run-rankings'); btn.disabled = true; btn.textContent = 'Ranking profiles…';
  try {
    const data = await api('/api/simulate', {method:'POST', body:JSON.stringify({})});
    renderRankings(data);
    $('metric-people').textContent = data.profile_count;
    $('metric-pairs').textContent = data.possible_pairs;
    if (state.selectedId) {
      const chosen = state.profiles.find(p => p.id === state.selectedId);
      if (chosen) await selectProfile(chosen.id);
    }
    toast(`Ranked ${data.profile_count} profiles across ${data.possible_pairs} possible pairings.`);
  } catch (e) { toast(e.message); }
  finally { btn.disabled = false; btn.innerHTML = 'Rank everyone <span>↗</span>'; }
}
async function startDate() {
  const a = $('date-person-a').value, b = $('date-person-b').value;
  if (!a || !b || a === b) return toast('Choose two different people first.');
  const btn = $('start-date'); btn.disabled = true; btn.textContent = 'Agents are meeting…';
  try {
    const data = await api('/api/date', {method:'POST', body:JSON.stringify({a_id:a,b_id:b})});
    renderDateResult(data);
  } catch (e) { toast(e.message); }
  finally { btn.disabled = false; btn.innerHTML = 'Start their simulated date <span>↗</span>'; }
}
async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget, btn = $('save-profile'), feedback = $('form-feedback');
  feedback.classList.add('hidden'); feedback.classList.remove('success');
  const fd = new FormData(form);
  const body = Object.fromEntries(fd.entries());
  body.age = Number(body.age); body.min_age = Number(body.min_age); body.max_age = Number(body.max_age);
  body.interests = body.interests.split(',').map(x => x.trim()).filter(Boolean);
  body.values = body.values.split(',').map(x => x.trim()).filter(Boolean);
  body.consent = fd.get('consent') === 'on';
  btn.disabled = true; btn.textContent = 'Validating consent…';
  try {
    const data = await api('/api/profiles', {method:'POST', body:JSON.stringify(body)});
    state.profiles.push(data.profile);
    state.filter = 'all'; document.querySelectorAll('.filter-pill').forEach(b => b.classList.toggle('active', b.dataset.filter === 'all'));
    state.selectedId = data.profile.id;
    populateDateSelects(); renderProfiles(); closeAddModal(); form.reset();
    toast(`${data.profile.name} was added. Now inspect their profile or rank the full line-up.`);
    await selectProfile(data.profile.id);
    document.getElementById('profiles').scrollIntoView({behavior:'smooth'});
    feedback.textContent = data.message;
  } catch (e) {
    feedback.textContent = e.message; feedback.classList.remove('hidden');
  } finally { btn.disabled = false; btn.textContent = 'Save profile with consent ↗'; }
}
async function init() {
  try {
    const data = await api('/api/profiles'); state.profiles = data.profiles;
    $('metric-people').textContent = state.profiles.length;
    $('metric-pairs').textContent = state.profiles.length * (state.profiles.length - 1) / 2;
    populateDateSelects(); renderProfiles();
    const first = state.profiles[0]; if (first) await selectProfile(first.id);
  } catch (e) {
    $('profiles-grid').innerHTML = `<div class="loading-card">Could not connect to the app service. Run <code>python server.py</code> and reload. Details: ${esc(e.message)}</div>`;
    toast('The app service is not reachable.');
  }
  $('profile-search').addEventListener('input', renderProfiles);
  document.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
    state.filter = b.dataset.filter; document.querySelectorAll('.filter-pill').forEach(x => x.classList.toggle('active', x === b)); renderProfiles();
  }));
  ['open-add','open-add-top','trust-add-link'].forEach(id => $(id).addEventListener('click', event => { event.preventDefault(); openAddModal(); }));
  $('close-add').addEventListener('click', closeAddModal); $('cancel-add').addEventListener('click', closeAddModal);
  $('add-modal').addEventListener('click', e => { if (e.target === $('add-modal')) closeAddModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('add-modal').classList.contains('hidden')) closeAddModal(); });
  $('add-profile-form').addEventListener('submit', saveProfile);
  $('run-rankings').addEventListener('click', runRankings); $('hero-run').addEventListener('click', async () => { document.getElementById('rankings').scrollIntoView({behavior:'smooth'}); await runRankings(); });
  $('start-date').addEventListener('click', startDate);
  $('date-person-a').addEventListener('change', () => { if ($('date-person-a').value === $('date-person-b').value) $('date-person-b').value = state.profiles.find(p => p.id !== $('date-person-a').value)?.id || ''; });
  $('date-person-b').addEventListener('change', () => { if ($('date-person-a').value === $('date-person-b').value) $('date-person-a').value = state.profiles.find(p => p.id !== $('date-person-b').value)?.id || ''; });

  // Evaluator-friendly, pre-run demo URL: append ?demo=1 to the live site.
  // It automatically computes rankings, starts a sample agent conversation,
  // and opens the date lab; no form entry is needed.
  if (new URLSearchParams(window.location.search).get('demo') === '1') {
    window.setTimeout(async () => {
      try {
        await runRankings();
        const first = state.profiles[0];
        const bestMatch = first && state.rankings?.[first.id]?.[0]?.profile?.id;
        if (first && bestMatch && bestMatch !== first.id) {
          $('date-person-a').value = first.id;
          $('date-person-b').value = bestMatch;
          await startDate();
        }
        document.getElementById('date-lab').scrollIntoView({behavior: 'auto', block: 'start'});
      } catch (e) {
        toast(`Demo setup could not complete: ${e.message}`);
      }
    }, 150);
  }
}
document.addEventListener('DOMContentLoaded', init);
