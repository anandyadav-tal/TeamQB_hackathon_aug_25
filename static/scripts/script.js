const form = document.getElementById('jira-form');
const analyzeBtn = document.getElementById('analyze-btn');
const btnText = document.getElementById('btn-text');
const loader = document.getElementById('loader');
const resultsDiv = document.getElementById('results');
const errorDiv = document.getElementById('error-message');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ticketDescription = document.getElementById('jira-ticket').value;

    btnText.textContent = 'Analyzing...';
    loader.classList.remove('hidden');
    analyzeBtn.disabled = true;
    resultsDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    resultsDiv.innerHTML = '';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticket: ticketDescription }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) { throw new Error(data.error); }

        await displayResults(data);

    } catch (error) {
        displayError(error.message);
    } finally {
        btnText.textContent = 'Analyze Requirement';
        loader.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

function displayError(message) {
    errorDiv.innerHTML = `<p><strong class="font-semibold">Error:</strong> ${message}</p>`;
    errorDiv.classList.remove('hidden');
}

async function displayResults(data) {
    const devView = data?.developer_view || {};
    const qaView = data?.qa_view || {};
    const pmView = data?.product_manager_view || {};

    const complexityColors = {
        'Low': 'bg-green-100 text-green-800',
        'Medium': 'bg-yellow-100 text-yellow-800',
        'High': 'bg-red-100 text-red-800',
    };

    const diagramAnalysis = devView?.diagram_analysis || {};
    const diagramHtml = diagramAnalysis.is_required
        ? `<div class="mermaid" id="mermaid-diagram">${diagramAnalysis.mermaid_script || ''}</div>`
        : `<p class="text-gray-600">${diagramAnalysis.mermaid_script || 'No diagram was generated.'}</p>`;

    resultsDiv.innerHTML = `
                <div class="card">
                    <div class="border-b border-gray-200 mb-4">
                        <nav class="-mb-px flex space-x-6" aria-label="Tabs">
                            <button data-tab="dev" class="tab-button active">Developer View</button>
                            <button data-tab="qa" class="tab-button">QA View</button>
                            <button data-tab="pm" class="tab-button">Product Manager View</button>
                        </nav>
                    </div>

                    <!-- Developer Content -->
                    <div data-content="dev" class="tab-content active">
                        <div class="space-y-6">
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Complexity Analysis</h3>
                                <div class="flex items-center">
                                    <span class="font-semibold mr-2">Development:</span>
                                    <span class="complexity-badge ${complexityColors[devView.complexity] || 'bg-gray-100 text-gray-800'}">${devView.complexity || 'N/A'}</span>
                                </div>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Potential Blockers & Risks</h3>
                                <ul class="list-disc list-inside space-y-2 text-gray-600">
                                    ${(devView.potential_blockers || []).map(b => `<li>${b}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Execution Flow Diagram</h3>
                                ${diagramHtml}
                            </div>
                        </div>
                    </div>

                    <!-- QA Content -->
                    <div data-content="qa" class="tab-content">
                        <div class="space-y-6">
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Complexity Analysis</h3>
                                <div class="flex items-center">
                                    <span class="font-semibold mr-2">QA:</span>
                                    <span class="complexity-badge ${complexityColors[qaView.complexity] || 'bg-gray-100 text-gray-800'}">${qaView.complexity || 'N/A'}</span>
                                </div>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 class="font-semibold text-gray-800 mb-2">Functional Test Cases</h3>
                                    <ul class="list-disc list-inside space-y-2 text-gray-600">
                                        ${((qaView.required_testing || {}).functional_tests || []).map(t => `<li>${t}</li>`).join('')}
                                    </ul>
                                </div>
                                <div>
                                    <h3 class="font-semibold text-gray-800 mb-2">Edge Cases to Consider</h3>
                                    <ul class="list-disc list-inside space-y-2 text-gray-600">
                                        ${((qaView.required_testing || {}).edge_cases || []).map(e => `<li>${e}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Product Manager Content -->
                    <div data-content="pm" class="tab-content">
                        <div class="space-y-6">
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Clarifying Questions</h3>
                                <ul class="list-disc list-inside space-y-2 text-gray-600">
                                    ${(pmView.clarifying_questions || []).map(q => `<li>${q}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-800 mb-2">Acceptance Criteria Review</h3>
                                ${(pmView.acceptance_criteria_review || []).map(ac => `
                                    <div class="mb-3 pb-3 border-b border-gray-200 last:border-b-0">
                                        <p class="font-semibold text-gray-700"><strong>Criteria:</strong> ${ac.criteria || 'N/A'}</p>
                                        <p class="text-gray-600 mt-1"><strong>Suggestion:</strong> ${ac.suggestion || 'N/A'}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
    resultsDiv.classList.remove('hidden');

    if (diagramAnalysis.is_required) {
        const mermaidDiv = document.getElementById('mermaid-diagram');
        if (mermaidDiv) {
            try {
                const { svg } = await window.mermaid.render('mermaid-svg', diagramAnalysis.mermaid_script || '');
                mermaidDiv.innerHTML = svg;
            } catch (e) {
                mermaidDiv.innerHTML = `<p class="text-red-600">Error rendering diagram: ${e.message}</p><pre class="bg-gray-100 p-2 rounded">${diagramAnalysis.mermaid_script || ''}</pre>`;
                console.error("Mermaid rendering error:", e);
            }
        }
    }
}

// Event Delegation for Tabs
resultsDiv.addEventListener('click', (e) => {
    if (e.target.matches('.tab-button')) {
        const tabName = e.target.dataset.tab;
        if (tabName) {
            switchTab(tabName);
        }
    }
});

function switchTab(tabName) {
    // Deactivate all buttons and content
    document.querySelectorAll('.tab-button').forEach(button => button.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Activate the clicked button and corresponding content
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.querySelector(`[data-content="${tabName}"]`).classList.add('active');
}