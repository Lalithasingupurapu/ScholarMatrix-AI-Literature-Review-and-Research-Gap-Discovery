// ==========================================================================
// ScholarMatrix AI - Main Application Orchestrator
// ==========================================================================

let activeMode = 'online';
let uploadedPdfs = [];
let fullReviewState = null;
let currentPaperFilter = '';

document.addEventListener('DOMContentLoaded', () => {
  // Purge any legacy graph tabs or canvas if browser held cached HTML
  document.querySelectorAll('[data-tab="graph"], #tab-graph, #citation-graph-canvas, .graph-container-wrapper').forEach(el => el.remove());

  initPresets();
  initRangeSlider();
  initDropzone();
  initTabs();
});

// Preset Topics & Questions
const PRESETS = {
  rag: {
    topic: "Retrieval-Augmented Generation (RAG)",
    question: "How can RAG reduce AI hallucinations?",
    startYear: 2021,
    endYear: 2026,
    papers: 20
  },
  diffusion: {
    topic: "Diffusion Models for Medical Imaging",
    question: "Can latent diffusion reduce MRI acquisition artifacts and reconstruction noise?",
    startYear: 2021,
    endYear: 2026,
    papers: 15
  },
  cot: {
    topic: "Chain-of-Thought Reasoning in LLMs",
    question: "How does step-by-step reasoning affect mathematical problem-solving faithfulness?",
    startYear: 2022,
    endYear: 2026,
    papers: 15
  },
  hybrid_search: {
    topic: "Sparse-Dense Hybrid Search & Vector Databases",
    question: "What are the retrieval accuracy trade-offs between BM25 and neural cross-encoders?",
    startYear: 2021,
    endYear: 2026,
    papers: 15
  }
};

function initPresets() {
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-preset');
      const data = PRESETS[key];
      if (data) {
        document.getElementById('input-topic').value = data.topic;
        document.getElementById('input-question').value = data.question;
        document.getElementById('input-start-year').value = data.startYear;
        document.getElementById('input-end-year').value = data.endYear;
        document.getElementById('input-num-papers').value = data.papers;
        document.getElementById('range-val-badge').innerText = data.papers;

        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    });
  });
}

function initRangeSlider() {
  const slider = document.getElementById('input-num-papers');
  const badge = document.getElementById('range-val-badge');
  if (slider && badge) {
    slider.addEventListener('input', (e) => {
      badge.innerText = e.target.value;
    });
  }
}

function setSourceMode(mode) {
  activeMode = mode;
  document.querySelectorAll('.mode-tab').forEach(tab => {
    tab.classList.toggle('active', tab.getAttribute('data-mode') === mode);
  });

  const onlinePanel = document.getElementById('panel-online-search');
  const pdfPanel = document.getElementById('panel-pdf-upload');

  if (mode === 'online') {
    if (onlinePanel) onlinePanel.style.display = 'block';
    if (pdfPanel) pdfPanel.style.display = 'none';
  } else if (mode === 'pdf') {
    if (onlinePanel) onlinePanel.style.display = 'none';
    if (pdfPanel) pdfPanel.style.display = 'block';
    loadExistingUploadedPdfs();
  }
}

async function loadExistingUploadedPdfs() {
  if (uploadedPdfs.length > 0) {
    renderUploadedChips();
    return;
  }
  try {
    const res = await fetch('/api/uploaded-pdfs');
    if (res.ok) {
      const data = await res.json();
      if (data.papers && data.papers.length > 0) {
        uploadedPdfs = data.papers;
        renderUploadedChips();
      }
    }
  } catch (e) {
    console.warn("Could not fetch existing uploads:", e);
  }
}

function initDropzone() {
  const dropzone = document.getElementById('pdf-dropzone');
  const fileInput = document.getElementById('file-input');
  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('button')) return;
    fileInput.click();
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFilesUpload(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
    }
  });
}

async function handleFilesUpload(files) {
  const formData = new FormData();
  let validPdfs = 0;
  for (let i = 0; i < files.length; i++) {
    if (files[i].name.toLowerCase().endsWith('.pdf')) {
      formData.append('files', files[i]);
      validPdfs++;
    }
  }

  if (validPdfs === 0) {
    showToast('Please select valid PDF documents.', 'error');
    return;
  }

  showToast(`Uploading and parsing ${validPdfs} PDF(s)...`);

  try {
    const res = await fetch('/api/upload-pdfs', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to parse uploaded PDFs');
    }
    const data = await res.json();
    uploadedPdfs = uploadedPdfs.concat(data.papers || []);

    // Deduplicate by normalized title
    const seen = new Set();
    uploadedPdfs = uploadedPdfs.filter(p => {
      const t = (p.title || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      if (!t || seen.has(t)) return false;
      seen.add(t);
      return true;
    });

    renderUploadedChips();
    showToast(`Successfully parsed ${data.uploaded_count} PDF paper(s)!`);

    // Adjust paper count slider to match uploaded papers
    const numSlider = document.getElementById('input-num-papers');
    const rangeBadge = document.getElementById('range-val-badge');
    if (numSlider && rangeBadge) {
      numSlider.value = Math.max(5, Math.min(uploadedPdfs.length, 40));
      rangeBadge.innerText = numSlider.value;
    }

    if (activeMode === 'pdf') {
      showToast('PDFs are ready. Generating the literature review...');
      await startReviewGeneration();
    }
  } catch (err) {
    console.error(err);
    showToast('Error parsing PDF documents: ' + err.message, 'error');
  }
}

function renderUploadedChips() {
  const listEl = document.getElementById('uploaded-files-list');
  if (!listEl) return;
  if (uploadedPdfs.length === 0) {
    listEl.innerHTML = '';
    return;
  }

  listEl.innerHTML = `
    <div style="width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
      <span style="font-size: 0.85rem; font-weight: 700; color: #34d399; display: flex; align-items: center; gap: 6px;">
        <span>✓</span> ${uploadedPdfs.length} Research Paper PDF(s) Loaded & Ready
      </span>
      <button class="pill-button" onclick="clearUploadedPdfs(event)" style="font-size: 0.72rem; padding: 2px 8px;">
        ✕ Clear
      </button>
    </div>
    <div style="display: flex; flex-wrap: wrap; gap: 8px; width: 100%;">
      ${uploadedPdfs.map(p => `
        <div class="uploaded-file-chip" title="${escapeHtml(p.title)}">
          <span>📄</span>
          <span style="font-weight: 600;">${escapeHtml(p.title.length > 38 ? p.title.substring(0, 38) + '...' : p.title)}</span>
          <span style="color: #94a3b8; font-size: 0.75rem;">(${p.year})</span>
        </div>
      `).join('')}
    </div>
  `;
}

function clearUploadedPdfs(e) {
  if (e) e.stopPropagation();
  uploadedPdfs = [];
  renderUploadedChips();
  showToast('Uploaded PDFs list cleared.');
}

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabTarget = btn.getAttribute('data-tab');
      switchTab(tabTarget);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabId}`);
  });
}

// Full Literature Review Pipeline Trigger
async function startReviewGeneration() {
  const topic = document.getElementById('input-topic').value.trim();
  const question = document.getElementById('input-question').value.trim();
  const startYear = parseInt(document.getElementById('input-start-year').value) || 2021;
  const endYear = parseInt(document.getElementById('input-end-year').value) || 2026;
  const numPapers = parseInt(document.getElementById('input-num-papers').value) || 20;

  if (activeMode === 'pdf' && uploadedPdfs.length === 0) {
    await loadExistingUploadedPdfs();
    if (uploadedPdfs.length === 0) {
      showToast('Please upload at least one PDF research paper first.', 'error');
      return;
    }
  }

  if (!topic) {
    showToast('Please enter a research topic.', 'error');
    return;
  }

  // Show progress card and animate steps
  const progressCard = document.getElementById('progress-card');
  const generateBtn = document.getElementById('generate-btn');
  if (progressCard) progressCard.style.display = 'block';
  if (generateBtn) {
    generateBtn.disabled = true;
    generateBtn.innerHTML = `<span class="spinner"></span> Synthesizing Review...`;
  }

  // Animate progress steps
  animateProgressSteps();

  try {
    const payload = {
      topic: topic,
      research_question: question,
      start_year: startYear,
      end_year: endYear,
      num_papers: numPapers,
      mode: activeMode,
      uploaded_papers: activeMode === 'pdf' ? uploadedPdfs : null
    };

    const res = await fetch('/api/generate-full-review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || ('Server returned ' + res.status));
    }
    const data = await res.json();
    fullReviewState = data;
    if (activeMode === 'pdf' && data.meta) {
      document.getElementById('input-topic').value = data.meta.topic;
      document.getElementById('input-question').value = data.meta.research_question;
    }

    // Complete all progress steps
    completeAllSteps();

    // Render all 5 modules!
    renderAllOutputs(data);

    showToast(`Literature review successfully compiled for "${topic}"!`);
  } catch (err) {
    console.error('Review generation failed:', err);
    showToast('Generation failed: ' + err.message, 'error');
  } finally {
    if (generateBtn) {
      generateBtn.disabled = false;
      if (activeMode === 'pdf') {
        generateBtn.innerHTML = `<span>📑</span> <span>Generate Review from Uploaded PDFs</span>`;
      } else {
        generateBtn.innerHTML = `<span>✨</span> <span>Generate Literature Review</span>`;
      }
    }
    setTimeout(() => {
      if (progressCard) progressCard.style.display = 'none';
    }, 1400);
  }
}

function animateProgressSteps() {
  const steps = document.querySelectorAll('.step-item');
  steps.forEach((s, idx) => {
    s.classList.remove('active', 'completed');
    setTimeout(() => {
      if (idx > 0) steps[idx - 1].classList.replace('active', 'completed');
      s.classList.add('active');
    }, idx * 450);
  });
}

function completeAllSteps() {
  document.querySelectorAll('.step-item').forEach(s => {
    s.classList.remove('active');
    s.classList.add('completed');
  });
}

function renderAllOutputs(data) {
  // 1. Research Papers List
  renderPapersList(data.papers_list || []);

  // 2. Literature-Review Matrix
  if (typeof renderLiteratureMatrix === 'function') {
    renderLiteratureMatrix(data.literature_matrix || []);
  }

  // 3. In-Depth Research Gaps & Evidence
  if (typeof renderResearchGaps === 'function') {
    renderResearchGaps(data.research_gaps || []);
  }

  // 4. Synthesized Academic Research Report
  if (typeof renderResearchReport === 'function') {
    renderResearchReport(data.research_report || {});
  }

  // Update tab counters
  updateTabCount('papers', (data.papers_list || []).length);
  updateTabCount('matrix', (data.literature_matrix || []).length);
  updateTabCount('gaps', (data.research_gaps || []).length);
}

function updateTabCount(tabId, count) {
  const badge = document.getElementById(`count-badge-${tabId}`);
  if (badge) badge.innerText = count;
}

// Output 1: Papers List Renderer
function renderPapersList(papers) {
  const grid = document.getElementById('papers-grid');
  if (!grid) return;

  if (papers.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #64748b; padding: 40px;">No papers retrieved.</div>`;
    return;
  }

  grid.innerHTML = papers.map((p, idx) => `
    <div class="paper-card" id="paper-card-${p.id}">
      <div class="paper-meta-row">
        <span class="paper-venue-badge">${escapeHtml(p.venue || 'ArXiv / Conference')}</span>
        <span class="paper-cite-badge">${p.citation_count == null ? 'Citations unavailable' : `★ ${p.citation_count} Citations`}</span>
      </div>

      <h3 class="paper-title">${escapeHtml(p.title)}</h3>
      <div class="paper-authors">
        ${(p.authors || []).slice(0, 4).map(a => escapeHtml(a)).join(', ') || 'Author details unavailable'}${(p.authors || []).length > 4 ? ' et al.' : ''} (${p.year || 'Year unavailable'})
      </div>

      <p class="paper-abstract" id="abstract-text-${idx}">
        ${escapeHtml(p.abstract || 'Abstract not available from the selected source.')}
      </p>

      <div class="paper-footer">
        <button class="toggle-abstract-btn" onclick="toggleAbstract(${idx}, this)">
          Expand Abstract ▼
        </button>
        <a href="${p.pdf_url || p.url || '#'}" target="_blank" class="paper-link-btn">
          View Manuscript ↗
        </a>
      </div>
    </div>
  `).join('');

  const countBadge = document.getElementById('papers-count-badge');
  if (countBadge) countBadge.innerText = `${papers.length} Papers Found`;
}

function toggleAbstract(idx, btn) {
  const textEl = document.getElementById(`abstract-text-${idx}`);
  if (!textEl) return;
  const isExpanded = textEl.classList.toggle('expanded');
  btn.innerText = isExpanded ? 'Collapse Abstract ▲' : 'Expand Abstract ▼';
}

function filterPapersList() {
  const searchInput = document.getElementById('papers-search-input');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  if (!fullReviewState || !fullReviewState.papers_list) return;

  const filtered = fullReviewState.papers_list.filter(p => {
    if (!query) return true;
    return (
      (p.title || '').toLowerCase().includes(query) ||
      (p.authors || []).some(a => a.toLowerCase().includes(query)) ||
      (p.abstract || '').toLowerCase().includes(query) ||
      (p.venue || '').toLowerCase().includes(query)
    );
  });

  renderPapersList(filtered);
}

// Toast notification helper
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; pointer-events: none;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'error' ? 'rgba(239, 68, 68, 0.95)' : 'rgba(30, 41, 59, 0.95)';
  const border = type === 'error' ? '#ef4444' : '#6366f1';
  toast.style.cssText = `background: ${bg}; color: white; border: 1px solid ${border}; padding: 12px 20px; border-radius: 10px; font-size: 0.9rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); backdrop-filter: blur(10px); transition: all 0.3s ease; transform: translateY(10px); opacity: 0; pointer-events: auto;`;
  toast.innerText = message;
  toastContainer.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
