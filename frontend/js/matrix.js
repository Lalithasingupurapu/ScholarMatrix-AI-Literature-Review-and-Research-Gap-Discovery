// ==========================================================================
// ScholarMatrix AI - Literature-Review Matrix Controller
// ==========================================================================

let currentMatrixData = [];
let matrixSortField = 'citations';
let matrixSortAsc = false;

function renderLiteratureMatrix(matrix) {
  currentMatrixData = matrix || [];
  applyMatrixFilters();
}

function toggleMatrixRow(rowId) {
  // Deep dive column removed as requested
}

function expandAllMatrixRows() {
  // Deep dive column removed as requested
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
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 48px;">No matching papers found in matrix.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((row, index) => {
    const linkUrl = row.pdf_url || row.url || '#';

    return `
      <!-- Main Row -->
      <tr class="matrix-row" id="matrix-row-${row.paper_id}">
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

        <!-- Col 4: Datasets & Metrics -->
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
      </tr>
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

  let md = '| Paper & Authors | Year | Research Focus | Methodology | Datasets | Key Results | Limitations & Bottlenecks |\n';
  md += '| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n';

  currentMatrixData.forEach(row => {
    md += `| ${row.title} (${row.authors}) | ${row.year} | ${row.research_focus} | ${row.methodology} | ${row.datasets} | ${row.results} | ${row.limitations} |\n`;
  });

  navigator.clipboard.writeText(md).then(() => {
    showToast('Literature Matrix copied as Markdown table!');
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
