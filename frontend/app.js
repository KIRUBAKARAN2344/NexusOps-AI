document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const btnAnalyze = document.getElementById('btn-analyze');
    const incidentsContainer = document.getElementById('incidents-container');
    const noiseContainer = document.getElementById('noise-container');
    const topologyContainer = document.getElementById('topology-container');
    const canvas = document.getElementById('network-canvas');
    const ctx = canvas.getContext('2d');
    
    // Status Elements
    const lastRefresh = document.getElementById('last-refresh');
    const incidentCountBadge = document.getElementById('incident-count-badge');
    const noiseCountBadge = document.getElementById('noise-count-badge');
    
    let currentData = { incidents: [], noise: [] };
    let topologyData = { nodes: [], links: [] };
    
    // Initialize Clock
    setInterval(() => {
        document.getElementById('clock').textContent = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    }, 1000);

    // Initialize Topology
    fetchTopology();

    // Command Palette Logic
    window.openCommandPalette = () => {
        document.getElementById('cmd-palette-modal').classList.remove('hidden');
        document.getElementById('cmd-input').focus();
    };
    
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openCommandPalette();
        }
        if (e.key === 'Escape') {
            document.getElementById('cmd-palette-modal').classList.add('hidden');
        }
    });

    document.getElementById('cmd-palette-modal').addEventListener('click', (e) => {
        if(e.target.id === 'cmd-palette-modal') e.target.classList.add('hidden');
    });

    // Pipeline Logic
    btnAnalyze.addEventListener('click', async () => {
        const btnText = btnAnalyze.querySelector('.btn-text');
        btnText.textContent = 'EXECUTING PIPELINE...';
        btnAnalyze.disabled = true;

        // Reset Pipeline UI
        const steps = document.querySelectorAll('.pipeline-step');
        steps.forEach(s => { s.classList.remove('active'); s.classList.remove('done'); });
        
        try {
            // Simulate Pipeline progress for visual effect before fetch
            await animatePipelineStep('ingest', 300);
            await animatePipelineStep('normalize', 300);
            await animatePipelineStep('correlate', 400);
            
            // Actual fetch
            const res = await fetch('/api/analyze', { method: 'POST' });
            if (!res.ok) throw new Error('Analysis failed');
            
            await animatePipelineStep('prioritize', 200);
            await animatePipelineStep('retrieve', 400);
            await animatePipelineStep('reason', 600);
            await animatePipelineStep('cite', 300);

            const data = await res.json();
            currentData = { incidents: data.incidents, noise: data.noise_alerts };
            
            updateDashboard(data);
            renderIncidents(data.incidents);
            renderNoise(data.noise_alerts);
            
            lastRefresh.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
            
            // Re-render topology to show incident highlights
            renderTopology();

        } catch (err) {
            console.error(err);
            alert('Error running analysis. Check console.');
        } finally {
            btnText.textContent = 'START TRIAGE PIPELINE';
            btnAnalyze.disabled = false;
        }
    });

    async function animatePipelineStep(stepName, duration) {
        const step = document.querySelector(`.pipeline-step[data-step="${stepName}"]`);
        if (step) {
            step.classList.add('active');
            await new Promise(r => setTimeout(r, duration));
            step.classList.remove('active');
            step.classList.add('done');
        }
    }

    async function fetchTopology() {
        try {
            const res = await fetch('/api/topology');
            if (res.ok) {
                topologyData = await res.json();
                resizeCanvas();
                window.addEventListener('resize', resizeCanvas);
                renderTopology();
            }
        } catch (e) {
            console.warn('Topology fetch failed:', e);
        }
    }

    function resizeCanvas() {
        if (!topologyContainer) return;
        canvas.width = topologyContainer.clientWidth;
        canvas.height = topologyContainer.clientHeight;
        renderTopology();
    }

    function renderTopology() {
        if (!ctx || topologyData.nodes.length === 0) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const width = canvas.width;
        const height = canvas.height;
        
        // Simple force-directed / circular layout for hackathon
        const radius = Math.min(width, height) / 2.5;
        const centerX = width / 2;
        const centerY = height / 2;
        
        const nodes = topologyData.nodes;
        const links = topologyData.links;
        
        // Find affected devices
        const affectedDevices = new Set();
        currentData.incidents.forEach(inc => {
            inc.affected_devices.forEach(d => affectedDevices.add(d));
        });

        // Position nodes
        const nodePositions = {};
        nodes.forEach((node, i) => {
            const angle = (i / nodes.length) * 2 * Math.PI;
            nodePositions[node.device_id] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
                data: node
            };
        });

        // Draw Links
        links.forEach(link => {
            const source = nodePositions[link.source];
            const target = nodePositions[link.target];
            if (source && target) {
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                
                // Highlight links between affected devices
                if (affectedDevices.has(link.source) || affectedDevices.has(link.target)) {
                    ctx.strokeStyle = 'rgba(255, 51, 102, 0.4)';
                    ctx.lineWidth = 2;
                } else {
                    ctx.strokeStyle = 'rgba(30, 45, 74, 0.5)';
                    ctx.lineWidth = 1;
                }
                ctx.stroke();
            }
        });

        // Draw Nodes
        Object.values(nodePositions).forEach(node => {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
            
            if (affectedDevices.has(node.data.device_id)) {
                ctx.fillStyle = '#ff3366';
                ctx.shadowColor = '#ff3366';
                ctx.shadowBlur = 15;
            } else {
                ctx.fillStyle = '#00e5ff';
                ctx.shadowColor = 'transparent';
                ctx.shadowBlur = 0;
            }
            
            ctx.fill();
            
            // Label
            ctx.fillStyle = '#8ba0c1';
            ctx.font = '10px JetBrains Mono';
            ctx.textAlign = 'center';
            ctx.fillText(node.data.device_id, node.x, node.y + 20);
        });
    }

    function updateDashboard(data) {
        document.getElementById('stat-alerts').textContent = 
            data.incidents.reduce((sum, inc) => sum + inc.alerts.length, 0) + data.noise_alerts.length;
        document.getElementById('stat-incidents').textContent = data.incidents.length;
        document.getElementById('stat-noise').textContent = data.noise_alerts.length;
        
        let p1Count = 0;
        let escalations = 0;
        let groundable = 0;
        
        data.incidents.forEach(i => {
            if (i.priority === 'P1') p1Count++;
            if (i.recommendation?.requires_escalation) escalations++;
            if (i.recommendation?.runbook_id && !i.recommendation?.requires_escalation) groundable++;
        });

        document.getElementById('stat-p1').textContent = p1Count;
        document.getElementById('stat-escalations').textContent = escalations;
        
        if (data.incidents.length > 0) {
            document.getElementById('stat-grounding').textContent = Math.round((groundable / data.incidents.length) * 100) + '%';
        }
        
        incidentCountBadge.textContent = data.incidents.length;
        noiseCountBadge.textContent = data.noise_alerts.length;
    }

    function renderIncidents(incidents) {
        incidentsContainer.innerHTML = '';
        if (incidents.length === 0) {
            incidentsContainer.innerHTML = '<div class="empty-state"><div class="empty-icon">⚲</div><p>No active incidents.</p></div>';
            return;
        }

        incidents.forEach((inc, index) => {
            const card = document.createElement('div');
            card.className = `incident-card ${inc.priority}`;
            
            const alertsCount = inc.alerts.length;
            const escalated = inc.recommendation?.requires_escalation;
            
            card.innerHTML = `
                <div class="card-header-flex">
                    <span class="badge ${inc.priority}">${inc.priority}</span>
                    <span>${formatTime(inc.created_at)}</span>
                </div>
                <h4>${inc.incident_id}</h4>
                <p>Assets: ${inc.affected_devices.join(', ')}</p>
                <div style="display:flex; gap:0.5rem;">
                    <span class="badge outline-muted">${alertsCount} SIGNALS</span>
                    ${escalated ? '<span class="badge P1">ESCALATED</span>' : ''}
                </div>
            `;
            
            card.addEventListener('click', () => openIncidentModal(index));
            incidentsContainer.appendChild(card);
        });
    }

    function renderNoise(noise) {
        noiseContainer.innerHTML = '';
        if (noise.length === 0) {
            noiseContainer.innerHTML = '<div class="empty-state"><p>No isolated signals.</p></div>';
            return;
        }

        noise.forEach(alert => {
            const card = document.createElement('div');
            card.className = `noise-card`;
            card.innerHTML = `
                <div class="noise-header">
                    <span class="badge outline-muted">${alert.severity}</span>
                    <span>${formatTime(alert.timestamp)}</span>
                </div>
                <div style="font-family: var(--font-mono); margin-bottom: 0.25rem; color: var(--cyan-accent);">
                    ${alert.device_id}
                </div>
                <div class="noise-msg">${alert.message}</div>
            `;
            noiseContainer.appendChild(card);
        });
    }

    // Modal Logic
    const modal = document.getElementById('incident-modal');
    const closeBtn = document.querySelector('.close-btn');

    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    window.copyHandoff = function() {
        const reason = document.getElementById('escalation-reason').textContent;
        const text = `NOC ESCALATION HANDOFF:\nIncident: ${document.getElementById('modal-title').textContent}\nPriority: ${document.getElementById('modal-priority').textContent}\nAffected: ${document.getElementById('modal-devices').textContent}\nReason: ${reason}`;
        navigator.clipboard.writeText(text);
        alert('Handoff summary copied to clipboard.');
    };

    function openIncidentModal(index) {
        const inc = currentData.incidents[index];
        const rec = inc.recommendation;

        document.getElementById('modal-title').textContent = inc.incident_id;
        document.getElementById('modal-priority').className = `badge ${inc.priority}`;
        document.getElementById('modal-priority').textContent = inc.priority;
        
        // Tags
        const tagsContainer = document.getElementById('modal-devices');
        tagsContainer.innerHTML = '';
        inc.affected_devices.forEach(d => {
            const span = document.createElement('span');
            span.className = 'asset-tag';
            span.textContent = d;
            tagsContainer.appendChild(span);
        });
        
        document.getElementById('modal-alert-count').textContent = inc.alerts.length;
        
        // Signals list
        const alertList = document.getElementById('modal-alerts-list');
        alertList.innerHTML = '';
        inc.alerts.forEach(a => {
            const div = document.createElement('div');
            div.className = 'signal-item';
            div.innerHTML = `
                <div class="signal-item-header">
                    <span>${a.severity}</span>
                    <span>${formatTime(a.timestamp)}</span>
                </div>
                <div class="signal-item-body">${a.device_id}: ${a.message}</div>
            `;
            alertList.appendChild(div);
        });

        // AI Recommendation
        if (rec) {
            document.getElementById('modal-confidence').textContent = `${Math.round(rec.confidence * 100)}% Confidence`;
            document.getElementById('modal-action').textContent = rec.recommended_action;
        } else {
            document.getElementById('modal-confidence').textContent = 'N/A';
            document.getElementById('modal-action').textContent = 'No recommendation available.';
        }
        
        // Escalation
        const escAlert = document.getElementById('escalation-alert');
        if (rec && rec.requires_escalation) {
            escAlert.classList.remove('hidden');
            document.getElementById('escalation-reason').textContent = rec.escalation_reason || 'Unknown reason';
        } else {
            escAlert.classList.add('hidden');
        }

        // Trace runbook status
        const rbStatus = document.getElementById('trace-runbook-status');
        if(rec && rec.runbook_id) {
            rbStatus.textContent = '✓';
            rbStatus.style.color = 'var(--success)';
        } else {
            rbStatus.textContent = '✗';
            rbStatus.style.color = 'var(--danger)';
        }

        // Evidence
        const evList = document.getElementById('modal-evidence');
        evList.innerHTML = '';
        if (rec && rec.evidence_citations && rec.evidence_citations.length > 0) {
            rec.evidence_citations.forEach(cit => {
                const li = document.createElement('li');
                li.textContent = cit;
                evList.appendChild(li);
            });
        } else {
            evList.innerHTML = '<li>No citations mapped.</li>';
        }

        document.getElementById('modal-runbook').textContent = (rec && rec.runbook_id) ? rec.runbook_id : 'None';

        // Timeline
        const timeline = document.getElementById('modal-timeline');
        timeline.innerHTML = '';
        // Fake timeline based on alerts
        if(inc.alerts.length > 0) {
            const firstAlert = inc.alerts[0];
            addTimelineItem(timeline, firstAlert.timestamp, 'Initial Signal Detected', true);
            addTimelineItem(timeline, inc.created_at, 'Incident Correlated', true);
            addTimelineItem(timeline, new Date().toISOString(), 'AI Triage Complete', true);
            if(rec && rec.requires_escalation) {
                addTimelineItem(timeline, new Date().toISOString(), 'Escalation Triggered', false);
            }
        }

        modal.classList.remove('hidden');
    }

    function addTimelineItem(container, time, title, active) {
        const div = document.createElement('div');
        div.className = `timeline-item ${active ? 'active' : ''}`;
        div.innerHTML = `
            <span class="timeline-time">${formatTime(time)}</span>
            <div class="timeline-title">${title}</div>
        `;
        container.appendChild(div);
    }

    function formatTime(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + d.getMilliseconds().toString().padStart(3, '0');
        } catch {
            return isoString;
        }
    }

    // Navigation Logic
    function switchView(viewName) {
        document.body.setAttribute('data-active-view', viewName);
        
        document.querySelectorAll('#sidebar-nav .nav-item').forEach(item => {
            if(item.dataset.target === viewName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        if (viewName === 'topology' || viewName === 'overview') {
            setTimeout(resizeCanvas, 50);
        }
    }

    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '') || 'overview';
        switchView(hash);
    });

    const initialHash = window.location.hash.replace('#', '') || 'overview';
    switchView(initialHash);
});
