// ==========================================================================
// ScholarMatrix AI - Paper-by-Paper Research Gap Renderer
// ==========================================================================

let currentGapsData = [];

function renderResearchGaps(gaps) {
  currentGapsData = gaps || [];
  const countBadge = document.getElementById('gaps-count-badge');
  if (countBadge) {
    countBadge.innerText = `${currentGapsData.length} Papers Analyzed`;
  }
  applyGapsFilter();
}

function applyGapsFilter() {
  const grid = document.getElementById('gaps-grid');
  if (!grid) return;

  if (currentGapsData.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: #64748b; padding: 60px 20px; background: rgba(15, 23, 42, 0.4); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
        <div style="font-size: 1rem; font-weight: 600; color: #94a3b8;">No papers available for gap analysis.</div>
      </div>
    `;
    return;
  }

  grid.innerHTML = currentGapsData.map((gap, index) => {
    const evidence = (gap.supporting_evidence || [])[0];
    const paperTitle = gap.paper_title || gap.title || 'Untitled paper';
    const explicitGap = Boolean(gap.has_explicit_gap);

    return `
      <article class="gap-card medium" id="gap-card-${escapeHtml(gap.id || index)}">
        <div class="gap-header">
          <span class="gap-category">Paper ${index + 1} of ${currentGapsData.length}</span>
          <span class="gap-meta-badge">${escapeHtml(gap.citation || '')}</span>
        </div>

        <h3 class="gap-title">${escapeHtml(paperTitle)}</h3>

        <div class="gap-analysis-section">
          <div class="section-micro-heading">RESEARCH GAP FOR THIS PAPER</div>
          <p class="gap-analysis-text">${escapeHtml(gap.research_gap || gap.description || '')}</p>
        </div>

        <div class="gap-bottleneck-row">
          <span class="bottleneck-tag">Evidence status:</span>
          <span class="bottleneck-text">${escapeHtml(gap.gap_basis || '')}</span>
        </div>

        ${evidence ? `
          <div class="gap-evidence-box">
            <div class="evidence-title">
              <span>Evidence from this paper</span>
              <span class="section-tag">${escapeHtml(evidence.section || 'Paper text')}</span>
            </div>
            <div class="evidence-item-card">
              <div class="evidence-source-info">
                <span class="evidence-cite-tag">${escapeHtml(evidence.citation || '')}</span>
                <span class="evidence-paper-title">${escapeHtml(evidence.title || paperTitle)}</span>
              </div>
              <div class="evidence-quote-bubble">
                <span class="quote-mark">“</span>
                <em>${escapeHtml(evidence.evidence_quote || '')}</em>
                <span class="quote-mark">”</span>
              </div>
            </div>
          </div>
        ` : ''}

        ${!explicitGap && gap.context_excerpt ? `
          <div class="gap-evidence-box">
            <div class="evidence-title">Available paper context</div>
            <p class="gap-analysis-text">${escapeHtml(gap.context_excerpt)}</p>
          </div>
        ` : ''}

        ${(evidence && evidence.url || gap.url) && (evidence && evidence.url || gap.url) !== '#' ? `
          <div class="evidence-footer">
            <a href="${escapeHtml((evidence && evidence.url) || gap.url)}" target="_blank" rel="noopener noreferrer" class="evidence-link-btn">
              <span>Open this paper</span>
            </a>
          </div>
        ` : ''}
      </article>
    `;
  }).join('');
}
