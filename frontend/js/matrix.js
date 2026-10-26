// ==========================================================================
// Literature-Review Matrix Controller
// ==========================================================================

let currentMatrixData = [];
let matrixSortField = 'citations';
let matrixSortAsc = false;

function renderLiteratureMatrix(matrix) {
  currentMatrixData = matrix || [];
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
      (row.methodology || '').toLowerCase().includes(query) ||
      (row.datasets || '').toLowerCase().includes(query) ||
      (row.results || '').toLowerCase().includes(query) ||
      (row.limitations || '').toLowerCase().includes(query)
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
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 32px;">No matching papers in matrix.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(row => `
    <tr>
      <td class="col-paper">
        <div style="font-weight: 700; color: #ffffff; margin-bottom: 4px;">${escapeHtml(row.title)}</div>
        <div style="font-size: 0.8rem; color: #94a3b8;">${escapeHtml(row.authors)} (${row.year})</div>
        <div style="margin-top: 6px; display: flex; gap: 6px;">
          <span class="paper-cite-badge" style="font-size: 0.75rem; padding: 1px 6px;">★ ${row.citations}</span>
          <a href="${row.pdf_url || row.url || '#'}" target="_blank" style="color: #6366f1; text-decoration: none; font-size: 0.75rem;">Link ↗</a>
        </div>
      </td>
      <td class="col-method">
        <div>${escapeHtml(row.methodology)}</div>
      </td>
      <td class="col-datasets">
        <span style="background: rgba(167, 139, 250, 0.12); color: #c4b5fd; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 0.82rem;">
          ${escapeHtml(row.datasets)}
        </span>
      </td>
      <td class="col-results">
        <div>${escapeHtml(row.results)}</div>
      </td>
      <td class="col-limitations">
        <div>${escapeHtml(row.limitations)}</div>
      </td>
    </tr>
  `).join('');

  const countBadge = document.getElementById('matrix-count-badge');
  if (countBadge) {
    countBadge.innerText = `${filtered.length} of ${currentMatrixData.length} papers`;
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

  let md = '| Paper & Authors | Year | Methodology | Datasets | Key Results | Limitations |\n';
  md += '| :--- | :--- | :--- | :--- | :--- | :--- |\n';

  currentMatrixData.forEach(row => {
    md += `| ${row.title} (${row.authors}) | ${row.year} | ${row.methodology} | ${row.datasets} | ${row.results} | ${row.limitations} |\n`;
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
