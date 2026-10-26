// ==========================================================================
// Research Gaps & Evidence Controller
// ==========================================================================

let currentGapsData = [];

function renderResearchGaps(gaps) {
  currentGapsData = gaps || [];
  const grid = document.getElementById('gaps-grid');
  if (!grid) return;

  if (currentGapsData.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #64748b; padding: 40px;">No research gaps synthesized yet.</div>`;
    return;
  }

  grid.innerHTML = currentGapsData.map(gap => {
    const sevClass = (gap.severity || 'high').toLowerCase();

    return `
      <div class="gap-card ${sevClass}">
        <div class="gap-header">
          <span class="gap-category">${escapeHtml(gap.category)}</span>
          <span class="gap-badge ${sevClass}">Priority: ${gap.severity}</span>
        </div>

        <h3 class="gap-title">${escapeHtml(gap.title)}</h3>
        <p class="gap-desc">${escapeHtml(gap.description)}</p>

        <div class="gap-evidence-box">
          <div class="evidence-title">
            <span>📑 Empirical Evidence (${(gap.supporting_evidence || []).length} Citations)</span>
          </div>
          ${(gap.supporting_evidence || []).map(ev => `
            <div class="evidence-item">
              <span class="evidence-cite">[${escapeHtml(ev.citation)}]:</span>
              <em>"${escapeHtml(ev.evidence_quote)}"</em>
            </div>
          `).join('')}
        </div>

        <div class="directions-box">
          <div class="directions-title">Proposed Future Research Directions</div>
          <ul class="direction-list">
            ${(gap.future_directions || []).map(dir => `
              <li>${escapeHtml(dir)}</li>
            `).join('')}
          </ul>
        </div>
      </div>
    `;
  }).join('');

  const countBadge = document.getElementById('gaps-count-badge');
  if (countBadge) {
    countBadge.innerText = `${currentGapsData.length} Research Gaps Identified`;
  }
}
