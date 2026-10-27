// ==========================================================================
// ScholarMatrix AI - Enlarged Literature-Review Matrix Controller
// ==========================================================================

let currentMatrixData = [];
let matrixSortField = 'citations';
let matrixSortAsc = false;
let expandedRowIds = new Set();

function renderLiteratureMatrix(matrix) {
  currentMatrixData = matrix || [];
  applyMatrixFilters();
}

function toggleMatrixRow(rowId) {
  if (expandedRowIds.has(rowId)) {
    expandedRowIds.delete(rowId);
  } else {
    expandedRowIds.add(rowId);
  }
  applyMatrixFilters();
}

function expandAllMatrixRows() {
  if (expandedRowIds.size === currentMatrixData.length) {
    expandedRowIds.clear();
  } else {
    expandedRowIds = new Set(currentMatrixData.map(r => r.paper_id));
  }
  applyMatrixFilters();
}

function applyMatrixFilters() {
  const searchInput = document.getElementById('matrix-search-input');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  let filtered = currentMatrixData.filter(row => {
    if (!query) return true;
    return (
      (row.title || '').toLowerCase().includes(query) ||
      (row.authors || '').toLowerCase().includes(query) ||
      (row.research_focus || '').toLowerCase().includes(query) ||
      (row.methodology || '').toLowerCase().includes(query) ||
      (row.datasets || '').toLowerCase().includes(query) ||
      (row.metrics_and_baselines || '').toLowerCase().includes(query) ||
      (row.results || '').toLowerCase().includes(query) ||
      (row.limitations || '').toLowerCase().includes(query) ||
      (row.future_scope || '').toLowerCase().includes(query)
    );
  });

  // Sort
  filtered.sort((a, b) => {
    let valA = a[matrixSortField];
    let valB = b[matrixSortField];
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA < valB) return matrixSortAsc ? -1 : 1;
    if (valA > valB) return matrixSortAsc ? 1 : -1;
    return 0;
  });

  const tbody = document.getElementById('matrix-table-body');
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #64748b; padding: 48px;">No matching papers found in matrix.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((row, index) => {
    const isExpanded = expandedRowIds.has(row.paper_id);
    const linkUrl = row.pdf_url || row.url || '#';

    return `
      <!-- Main Row -->
      <tr class="matrix-row ${isExpanded ? 'row-expanded' : ''}" id="matrix-row-${row.paper_id}">
        <!-- Col 1: Paper & Metadata -->
        <td class="col-paper">
          <div class="matrix-paper-title">${escapeHtml(row.title)}</div>
          <div class="matrix-author-line">${escapeHtml(row.authors)} (${row.year || 'Year unavailable'})</div>
          <div class="matrix-author-line">${escapeHtml(row.source_scope || '')}</div>
          <div class="matrix-paper-badges">
            <span class="paper-cite-badge" title="Citation count">${row.citations == null ? 'Citations unavailable' : `★ ${row.citations}`}</span>
            <span class="venue-pill">${escapeHtml(row.venue || 'Peer-reviewed')}</span>
            <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="link-btn">Access ↗</a>
          </div>
        </td>

        <!-- Col 2: Research Focus -->
        <td class="col-focus">
          <div class="focus-pill">${escapeHtml(row.research_focus || 'Not reported in available paper text.')}</div>
        </td>

        <!-- Col 3: Methodology (Enlarged) -->
        <td class="col-method">
          <div class="method-text">${escapeHtml(row.methodology)}</div>
        </td>

        <!-- Col 4: Datasets, Benchmarks & Metrics -->
        <td class="col-datasets">
          <div class="dataset-tags-wrap">
            <span class="dataset-badge">${escapeHtml(row.datasets)}</span>
          </div>
          ${row.metrics_and_baselines ? `
            <div class="metrics-micro-line">
              <span>${escapeHtml(row.metrics_and_baselines)}</span>
            </div>
          ` : ''}
        </td>

        <!-- Col 5: Key Results (Enlarged) -->
        <td class="col-results">
          <div class="results-text">${escapeHtml(row.results)}</div>
        </td>

        <!-- Col 6: Limitations & Vulnerabilities (Enlarged) -->
        <td class="col-limitations">
          <div class="limitations-text">${escapeHtml(row.limitations)}</div>
        </td>

        <!-- Col 7: Deep Dive Action -->
        <td class="col-action" style="text-align: center;">
          <button class="pill-button detail-toggle-btn ${isExpanded ? 'active' : ''}" onclick="toggleMatrixRow('${row.paper_id}')" title="Inspect full paper abstract, metrics and future scope">
            ${isExpanded ? '▲ Hide' : '🔍 Deep Dive'}
          </button>
        </td>
      </tr>

      <!-- Deep Dive Expandable Drawer Row -->
      ${isExpanded ? `
        <tr class="matrix-drawer-row">
          <td colspan="7">
            <div class="matrix-deep-dive-panel">
              <div class="deep-dive-header">
                <span class="deep-dive-tag">COMPREHENSIVE SCHOLARLY DEEP-DIVE</span>
                <span style="font-size: 0.78rem; color: #94a3b8;">${escapeHtml(row.title)}</span>
              </div>

              <div class="deep-dive-grid">
                <!-- Abstract Box -->
                <div class="deep-dive-box">
                  <div class="box-title">📄 Original Abstract & Synthesis Context</div>
                  <p class="box-content abstract-text">${escapeHtml(row.abstract || 'Abstract not available from the selected source.')}</p>
                </div>

                <!-- Experimental Setup & Future Scope -->
                <div class="deep-dive-box">
                  <div class="box-title">🔬 Evaluation Configuration & Baselines</div>
                  <p class="box-content" style="margin-bottom: 12px;">${escapeHtml(row.metrics_and_baselines || 'Not reported in available paper text.')}</p>

                  <div class="box-title" style="color: #34d399;">✦ Strategic Future Scope & Open Directions</div>
                  <p class="box-content">${escapeHtml(row.future_scope || 'No explicit future-work statement found in available paper text.')}</p>

                  <div style="margin-top: 14px; display: flex; gap: 10px;">
                    <a href="${linkUrl}" target="_blank" class="cta-btn-sm">
                      <span>Open Full Manuscript ↗</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </td>
        </tr>
      ` : ''}
    `;
  }).join('');

  const countBadge = document.getElementById('matrix-count-badge');
  if (countBadge) {
    countBadge.innerText = `${filtered.length} of ${currentMatrixData.length} papers analyzed`;
  }
}

function sortMatrixBy(field) {
  if (matrixSortField === field) {
    matrixSortAsc = !matrixSortAsc;
  } else {
    matrixSortField = field;
    matrixSortAsc = false;
  }
  applyMatrixFilters();
}

function copyMatrixMarkdown() {
  if (!currentMatrixData || currentMatrixData.length === 0) return;

  let md = '| Paper & Authors | Year | Research Focus | Methodology | Datasets & Benchmarks | Key Results | Limitations & Bottlenecks |\n';
  md += '| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n';

  currentMatrixData.forEach(row => {
    md += `| ${row.title} (${row.authors}) | ${row.year} | ${row.research_focus} | ${row.methodology} | ${row.datasets} | ${row.results} | ${row.limitations} |\n`;
  });

  navigator.clipboard.writeText(md).then(() => {
    showToast('Enlarged Literature Matrix copied as Markdown table!');
  });
}

function downloadMatrixCsv() {
  window.open('/api/export/csv', '_blank');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
