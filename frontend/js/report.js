// ==========================================================================
// Systematic Research Report Controller
// ==========================================================================

let currentReportData = null;

function renderResearchReport(report) {
  currentReportData = report || {};
  const container = document.getElementById('report-markdown-rendered');
  const tocContainer = document.getElementById('report-toc-list');
  if (!container) return;

  const md = report.markdown || '# No report available';

  // Render markdown using marked.js
  if (typeof marked !== 'undefined') {
    container.innerHTML = marked.parse(md);
  } else {
    container.innerHTML = `<pre style="white-space: pre-wrap;">${escapeHtml(md)}</pre>`;
  }

  // Generate Table of Contents dynamically
  if (tocContainer) {
    const headings = container.querySelectorAll('h2, h3');
    if (headings.length === 0) {
      tocContainer.innerHTML = '<li style="color: #64748b; font-size: 0.85rem;">No sections found.</li>';
    } else {
      let tocHtml = '';
      headings.forEach((h, idx) => {
        const id = `report-heading-${idx}`;
        h.id = id;
        const isH3 = h.tagName.toLowerCase() === 'h3';
        const indentStyle = isH3 ? 'padding-left: 18px; font-size: 0.8rem;' : 'font-weight: 600; font-size: 0.85rem;';
        tocHtml += `
          <li>
            <a href="#${id}" class="toc-link" style="${indentStyle}" onclick="smoothScrollTo('${id}', event)">
              ${h.innerText}
            </a>
          </li>
        `;
      });
      tocContainer.innerHTML = tocHtml;
    }
  }
}

function smoothScrollTo(elementId, event) {
  if (event) event.preventDefault();
  const el = document.getElementById(elementId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function copyReportMarkdown() {
  if (!currentReportData || !currentReportData.markdown) return;
  navigator.clipboard.writeText(currentReportData.markdown).then(() => {
    showToast('Research Report copied to clipboard as Markdown!');
  });
}

function downloadReportMarkdown() {
  window.open('/api/export/markdown', '_blank');
}

function downloadBibtex() {
  window.open('/api/export/bibtex', '_blank');
}

function printReport() {
  window.print();
}
