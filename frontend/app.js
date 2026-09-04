document.addEventListener('DOMContentLoaded', () => {
    const btnAnalyze = document.getElementById('btn-analyze');
    const incidentsContainer = document.getElementById('incidents-container');
    const noiseContainer = document.getElementById('noise-container');
    
    let currentData = { incidents: [], noise: [] };

    btnAnalyze.addEventListener('click', async () => {
        btnAnalyze.textContent = 'Analyzing...';
        btnAnalyze.disabled = true;

        try {
            const res = await fetch('/api/analyze', { method: 'POST' });
            if (!res.ok) throw new Error('Analysis failed');
            
            const data = await res.json();
            currentData = { incidents: data.incidents, noise: data.noise_alerts };
            
            updateDashboard(data);
            renderIncidents(data.incidents);
            renderNoise(data.noise_alerts);
            
        } catch (err) {
            console.error(err);
            alert('Error running analysis. Check console.');
        } finally {
            btnAnalyze.textContent = 'Start Triage Pipeline';
            btnAnalyze.disabled = false;
        }
    });

    function updateDashboard(data) {
        document.getElementById('stat-alerts').textContent = 
            data.incidents.reduce((sum, inc) => sum + inc.alerts.length, 0) + data.noise_alerts.length;
        document.getElementById('stat-incidents').textContent = data.incidents.length;
        document.getElementById('stat-noise').textContent = data.noise_alerts.length;
        
        const escalations = data.incidents.filter(i => i.recommendation?.requires_escalation).length;
        document.getElementById('stat-escalations').textContent = escalations;
    }

    function renderIncidents(incidents) {
        incidentsContainer.innerHTML = '';
        if (incidents.length === 0) {
            incidentsContainer.innerHTML = '<div class="empty-state">No incidents found.</div>';
            return;
        }

        incidents.forEach((inc, index) => {
            const isEscalated = inc.recommendation?.requires_escalation;
            
            const card = document.createElement('div');
            card.className = `incident-card ${inc.priority}`;
            card.innerHTML = `
                <div class="card-header-flex">
                    <span class="badge ${inc.priority}">${inc.priority}</span>
                    <span class="timestamp">${formatTime(inc.created_at)}</span>
                </div>
                <h3 style="margin-bottom: 0.5rem">${inc.incident_id}</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem;">
                    Affected: ${inc.affected_devices.join(', ')}
                </p>
                <div>
                    <span class="badge outline">${inc.alerts.length} ALERTS</span>
                    ${isEscalated ? '<span class="escalated-badge">ESCALATED</span>' : ''}
                </div>
            `;
            
            card.addEventListener('click', () => openModal(index));
            incidentsContainer.appendChild(card);
        });
    }

    function renderNoise(noise) {
        noiseContainer.innerHTML = '';
        if (noise.length === 0) {
            noiseContainer.innerHTML = '<div class="empty-state">No noise detected.</div>';
            return;
        }

        noise.forEach(alert => {
            const card = document.createElement('div');
            card.className = `noise-card`;
            card.innerHTML = `
                <div class="card-header-flex">
                    <span class="badge outline" style="color: var(--text-secondary)">${alert.severity}</span>
                    <span class="timestamp">${formatTime(alert.timestamp)}</span>
                </div>
                <div style="font-family: monospace; font-size: 0.85rem; margin-top: 0.5rem;">
                    ${alert.device_id}: ${alert.alert_type}
                </div>
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">
                    ${alert.message}
                </p>
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

    function openModal(index) {
        const inc = currentData.incidents[index];
        const rec = inc.recommendation;

        document.getElementById('modal-title').textContent = inc.incident_id;
        document.getElementById('modal-priority').className = `badge ${inc.priority}`;
        document.getElementById('modal-priority').textContent = inc.priority;
        
        document.getElementById('modal-devices').textContent = inc.affected_devices.join(', ');
        
        document.getElementById('modal-alert-count').textContent = inc.alerts.length;
        const alertList = document.getElementById('modal-alerts-list');
        alertList.innerHTML = '';
        inc.alerts.forEach(a => {
            const li = document.createElement('li');
            li.textContent = `[${formatTime(a.timestamp)}] ${a.severity} - ${a.device_id}: ${a.message}`;
            alertList.appendChild(li);
        });

        // AI Recommendation
        document.getElementById('modal-confidence').textContent = rec ? `${Math.round(rec.confidence * 100)}% Confidence` : 'N/A';
        document.getElementById('modal-action').textContent = rec ? rec.recommended_action : 'No recommendation available.';
        
        const escAlert = document.getElementById('escalation-alert');
        if (rec && rec.requires_escalation) {
            escAlert.classList.remove('hidden');
            document.getElementById('escalation-reason').textContent = rec.escalation_reason || 'Unknown reason';
        } else {
            escAlert.classList.add('hidden');
        }

        const evList = document.getElementById('modal-evidence');
        evList.innerHTML = '';
        if (rec && rec.evidence_citations && rec.evidence_citations.length > 0) {
            rec.evidence_citations.forEach(cit => {
                const li = document.createElement('li');
                li.textContent = cit;
                evList.appendChild(li);
            });
        } else {
            evList.innerHTML = '<li>No citations provided.</li>';
        }

        document.getElementById('modal-runbook').textContent = rec && rec.runbook_id ? rec.runbook_id : 'None';

        modal.classList.remove('hidden');
    }

    function formatTime(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch {
            return isoString;
        }
    }
});
