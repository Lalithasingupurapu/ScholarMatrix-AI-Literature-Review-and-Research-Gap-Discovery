// ==========================================================================
// Citation & Conceptual Network Graph Renderer (Powered by Vis.js)
// ==========================================================================

let networkInstance = null;
let currentGraphData = null;
let isPhysicsEnabled = true;

function renderCitationGraph(graphData) {
  currentGraphData = graphData;
  const container = document.getElementById('citation-graph-canvas');
  if (!container) return;

  const nodes = new vis.DataSet(graphData.nodes || []);
  const edges = new vis.DataSet(graphData.edges || []);

  const data = { nodes, edges };

  const options = {
    nodes: {
      shape: 'dot',
      scaling: {
        min: 16,
        max: 42,
        label: {
          min: 12,
          max: 16,
          drawThreshold: 10,
          maxVisible: 20
        }
      },
      font: {
        color: '#f8fafc',
        size: 13,
        face: 'Inter, system-ui, sans-serif',
        strokeWidth: 2,
        strokeColor: '#090d16'
      },
      borderWidth: 2,
      shadow: {
        enabled: true,
        color: 'rgba(0,0,0,0.5)',
        size: 8,
        x: 0,
        y: 4
      }
    },
    edges: {
      width: 1.5,
      selectionWidth: 3,
      arrows: {
        to: { enabled: true, scaleFactor: 0.7 }
      },
      smooth: {
        type: 'continuous',
        roundness: 0.2
      }
    },
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -45,
        centralGravity: 0.015,
        springLength: 95,
        springConstant: 0.06,
        damping: 0.5
      },
      maxVelocity: 40,
      minVelocity: 0.75,
      stabilization: {
        enabled: true,
        iterations: 150
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: true,
      dragView: true
    }
  };

  if (networkInstance) {
    networkInstance.destroy();
  }

  networkInstance = new vis.Network(container, data, options);

  // Update stats & legends
  updateGraphMetadata(graphData);

  // Node click handler
  networkInstance.on('click', function (params) {
    if (params.nodes.length > 0) {
      const selectedId = params.nodes[0];
      const selectedNode = (graphData.nodes || []).find(n => n.id === selectedId);
      if (selectedNode) {
        openPaperInspector(selectedNode, graphData);
      }
    } else {
      closePaperInspector();
    }
  });
}

function updateGraphMetadata(graphData) {
  const statsEl = document.getElementById('graph-stats-display');
  if (statsEl && graphData.stats) {
    statsEl.innerHTML = `
      <span><strong>${graphData.stats.total_nodes || 0}</strong> Papers Analyzed</span>
      <span>•</span>
      <span><strong>${graphData.stats.total_edges || 0}</strong> Citations & Semantic Connections</span>
      <span>•</span>
      <span><strong>${graphData.stats.clusters_count || 1}</strong> Thematic Clusters</span>
    `;
  }

  const legendEl = document.getElementById('graph-clusters-legend');
  if (legendEl && graphData.stats && graphData.stats.clusters) {
    legendEl.innerHTML = graphData.stats.clusters.map((c, i) => {
      const colors = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"];
      const col = colors[i % colors.length];
      return `
        <div class="legend-pill">
          <span class="legend-color-dot" style="background: ${col}"></span>
          <span>${c.name} (${c.size})</span>
        </div>
      `;
    }).join('');
  }
}

function openPaperInspector(node, graphData) {
  const inspector = document.getElementById('graph-inspector');
  if (!inspector) return;

  const connectedEdges = (graphData.edges || []).filter(e => e.from === node.id || e.to === node.id);
  const connectedNodeIds = new Set(connectedEdges.map(e => e.from === node.id ? e.to : e.from));
  const connectedPapers = (graphData.nodes || []).filter(n => connectedNodeIds.has(n.id));

  inspector.style.display = 'block';
  inspector.innerHTML = `
    <div class="inspector-header">
      <span class="paper-venue-badge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">
        ${node.cluster_name || 'Thematic Cluster'}
      </span>
      <button class="close-inspector-btn" onclick="closePaperInspector()">✕</button>
    </div>

    <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: #ffffff;">
      ${node.full_title}
    </h3>

    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px;">
      ${(node.authors || []).join(', ')} (${node.year})
    </div>

    <div style="display: flex; gap: 8px; margin-bottom: 16px;">
      <span class="paper-cite-badge">★ ${node.citations} Citations</span>
      <span class="paper-venue-badge">${node.venue || 'ArXiv'}</span>
    </div>

    <div style="margin-bottom: 16px;">
      <h4 style="font-size: 0.78rem; text-transform: uppercase; color: #64748b; margin-bottom: 6px;">Abstract</h4>
      <p style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">
        ${node.abstract}
      </p>
    </div>

    <div style="margin-bottom: 16px;">
      <h4 style="font-size: 0.78rem; text-transform: uppercase; color: #64748b; margin-bottom: 8px;">Connected Papers in Graph (${connectedPapers.length})</h4>
      <div style="display: flex; flex-direction: column; gap: 6px;">
        ${connectedPapers.map(cp => `
          <div style="font-size: 0.8rem; background: rgba(30, 41, 59, 0.6); padding: 6px 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
            <div style="font-weight: 600; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${cp.full_title}</div>
            <div style="color: #64748b; font-size: 0.75rem;">${cp.label} • ${cp.citations} citations</div>
          </div>
        `).join('')}
      </div>
    </div>

    <div style="margin-top: 20px;">
      <a href="${node.pdf_url || node.url || '#'}" target="_blank" class="cta-btn" style="padding: 9px 16px; font-size: 0.85rem;">
        Open Paper Manuscript ↗
      </a>
    </div>
  `;
}

function closePaperInspector() {
  const inspector = document.getElementById('graph-inspector');
  if (inspector) {
    inspector.style.display = 'none';
  }
}

function toggleGraphPhysics() {
  if (!networkInstance) return;
  isPhysicsEnabled = !isPhysicsEnabled;
  networkInstance.setOptions({ physics: { enabled: isPhysicsEnabled } });
  const btn = document.getElementById('physics-toggle-btn');
  if (btn) {
    btn.innerHTML = isPhysicsEnabled ? '⚡ Physics: On' : '⏸ Physics: Off';
    btn.classList.toggle('active', isPhysicsEnabled);
  }
}

function resetGraphView() {
  if (networkInstance) {
    networkInstance.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
  }
}
