document.addEventListener('DOMContentLoaded', () => {
    // Select elements
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    const btnModels = document.getElementById('btn-models');
    const modelsDropdown = document.getElementById('models-dropdown');
    const dropdownItems = document.querySelectorAll('.dropdown-item');

    const btnModelsBatch = document.getElementById('btn-models-batch');
    const modelsDropdownBatch = document.getElementById('models-dropdown-batch');
    const dropdownItemsBatch = document.querySelectorAll('.dropdown-item-batch');

    const indForm = document.getElementById('individual-form');
    const indInputs = indForm.querySelectorAll('input');
    const indUrl = document.getElementById('ind-url');
    const btnClearIndividual = document.getElementById('btn-clear-individual');
    const btnSaveUtm = document.getElementById('btn-save-utm');
    const btnCopyIndividual = document.getElementById('btn-copy-individual');
    const outputLink = document.getElementById('output-link');

    const savedEmptyState = document.getElementById('saved-empty-state');
    const savedListContainer = document.getElementById('saved-list-container');
    const savedCardsList = document.getElementById('saved-cards-list');
    const btnClearSaved = document.getElementById('btn-clear-saved');

    // Batch Tab elements
    const batchForm = document.getElementById('batch-form');
    const btnGenerateBatch = document.getElementById('btn-generate-batch');
    const batchResultsArea = document.getElementById('batch-results-area');
    const batchCount = document.getElementById('batch-count');
    const batchResultsList = document.getElementById('batch-results-list');
    const btnCopyAllBatch = document.getElementById('btn-copy-all-batch');
    const btnDownloadCsv = document.getElementById('btn-download-csv');

    // Persistent storage keys
    const SAVED_UTMS_KEY = 'ddm_saved_utms';

    let savedUTMs = JSON.parse(localStorage.getItem(SAVED_UTMS_KEY)) || [];

    // --- TAB SYSTEM ---
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));

            tab.classList.add('active');
            const target = tab.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
        });
    });

    // --- DROPDOWN CONTROL ---
    const toggleDropdown = (btn, dropdown) => {
        btn.classList.toggle('open');
        dropdown.classList.toggle('show');
    };

    const closeAllDropdowns = () => {
        btnModels.classList.remove('open');
        modelsDropdown.classList.remove('show');
        if (btnModelsBatch) btnModelsBatch.classList.remove('open');
        if (modelsDropdownBatch) modelsDropdownBatch.classList.remove('show');
    };

    btnModels.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(btnModels, modelsDropdown);
    });

    if (btnModelsBatch) {
        btnModelsBatch.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(btnModelsBatch, modelsDropdownBatch);
        });
    }

    document.addEventListener('click', closeAllDropdowns);

    // Apply Model to Individual Inputs
    dropdownItems.forEach(item => {
        item.addEventListener('click', () => {
            document.getElementById('ind-source').value = item.getAttribute('data-source');
            document.getElementById('ind-medium').value = item.getAttribute('data-medium');
            document.getElementById('ind-campaign').value = item.getAttribute('data-campaign');
            buildIndividualURL();
        });
    });

    // Apply Model to Batch Textareas (adds to the lists)
    dropdownItemsBatch.forEach(item => {
        item.addEventListener('click', () => {
            const addTextToTextarea = (id, text) => {
                const ta = document.getElementById(id);
                const current = ta.value.trim();
                if (current) {
                    ta.value = current + '\n' + text;
                } else {
                    ta.value = text;
                }
            };
            addTextToTextarea('batch-sources', item.getAttribute('data-source'));
            addTextToTextarea('batch-mediums', item.getAttribute('data-medium'));
            addTextToTextarea('batch-campaigns', item.getAttribute('data-campaign'));
        });
    });

    // --- CRIAÇÃO INDIVIDUAL LOGIC ---
    const buildIndividualURL = () => {
        // URL padrão do Render (pode ser customizada se preferir)
        let baseURL = indUrl.value.trim() || 'https://ddmpay-utm-api.onrender.com/acesso';
        
        if (!baseURL) {
            resetIndividualUI();
            return;
        }

        if (!/^https?:\/\//i.test(baseURL)) {
            baseURL = 'https://' + baseURL;
        }

        try {
            const url = new URL(baseURL);
            
            const params = {
                par1: document.getElementById('ind-source').value.trim(),   // ID/CPF do Aluno
                par2: document.getElementById('ind-medium').value.trim(),   // Canal (sms, whatsapp)
                par3: document.getElementById('ind-campaign').value.trim(), // Lote/Campanha
            };

            for (const [key, value] of Object.entries(params)) {
                if (value) {
                    url.searchParams.set(key, value);
                } else {
                    url.searchParams.delete(key);
                }
            }

            const finalUrl = url.toString();
            outputLink.textContent = finalUrl;
            outputLink.classList.add('active');

        } catch (e) {
            resetIndividualUI();
        }
    };

    const resetIndividualUI = () => {
        outputLink.textContent = 'Preencha os campos para gerar sua URL parametrizada';
        outputLink.classList.remove('active');
    };

    indInputs.forEach(input => {
        input.addEventListener('input', buildIndividualURL);
    });

    btnClearIndividual.addEventListener('click', () => {
        indForm.reset();
        buildIndividualURL();
        indUrl.focus();
    });

    btnCopyIndividual.addEventListener('click', () => {
        const link = outputLink.textContent;
        if (!link || !outputLink.classList.contains('active')) return;

        navigator.clipboard.writeText(link).then(() => {
            const originalText = outputLink.textContent;
            outputLink.textContent = 'URL Copiada!';
            
            setTimeout(() => {
                outputLink.textContent = originalText;
            }, 1500);
        });
    });

    // --- SAVED UTMS STORAGE & LIST ---
    const updateSavedList = () => {
        if (savedUTMs.length === 0) {
            savedEmptyState.classList.remove('d-none');
            savedListContainer.classList.add('d-none');
            return;
        }

        savedEmptyState.classList.add('d-none');
        savedListContainer.classList.remove('d-none');
        savedCardsList.innerHTML = '';

        [...savedUTMs].reverse().forEach((item, index) => {
            const trueIndex = savedUTMs.length - 1 - index;
            const card = document.createElement('div');
            card.className = 'saved-card';
            card.innerHTML = `
                <div class="saved-card-info">
                    <div class="saved-card-link" title="${item.fullUrl}">${item.fullUrl}</div>
                    <div class="saved-card-meta">
                        <span class="saved-card-tag src">${item.source}</span>
                        <span class="saved-card-tag">${item.medium}</span>
                        <span class="saved-card-tag">${item.campaign}</span>
                    </div>
                </div>
                <div class="saved-card-actions">
                    <button type="button" class="card-action-btn copy-saved" data-index="${trueIndex}" title="Copiar URL">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                    <button type="button" class="card-action-btn delete delete-saved" data-index="${trueIndex}" title="Remover URL">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>
            `;

            card.querySelector('.copy-saved').addEventListener('click', () => {
                navigator.clipboard.writeText(item.fullUrl).then(() => {
                    alert('URL copiada!');
                });
            });

            card.querySelector('.delete-saved').addEventListener('click', () => {
                savedUTMs.splice(trueIndex, 1);
                localStorage.setItem(SAVED_UTMS_KEY, JSON.stringify(savedUTMs));
                updateSavedList();
            });

            savedCardsList.appendChild(card);
        });
    };

    btnSaveUtm.addEventListener('click', () => {
        const link = outputLink.textContent;
        if (!link || !outputLink.classList.contains('active')) {
            alert('Por favor, crie uma URL parametrizada válida primeiro.');
            return;
        }

        const source = document.getElementById('ind-source').value.trim();
        const medium = document.getElementById('ind-medium').value.trim();
        const campaign = document.getElementById('ind-campaign').value.trim();

        // Avoid exact duplicate addition
        if (savedUTMs.some(item => item.fullUrl === link)) {
            alert('Esta URL já foi salva!');
            return;
        }

        savedUTMs.push({
            fullUrl: link,
            source,
            medium,
            campaign
        });

        localStorage.setItem(SAVED_UTMS_KEY, JSON.stringify(savedUTMs));
        updateSavedList();
        
        // Visual cue on save
        btnSaveUtm.textContent = 'Salva!';
        setTimeout(() => {
            btnSaveUtm.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg> <span>Salvar UTM</span>`;
        }, 1500);
    });

    btnClearSaved.addEventListener('click', () => {
        if (confirm('Deseja realmente limpar todas as URLs salvas?')) {
            savedUTMs = [];
            localStorage.setItem(SAVED_UTMS_KEY, JSON.stringify(savedUTMs));
            updateSavedList();
        }
    });

    // --- ABA CRIAÇÃO EM LOTE LOGIC ---
    let generatedBatchUrls = [];

    btnGenerateBatch.addEventListener('click', () => {
        const urls = document.getElementById('batch-urls').value.split('\n').map(x => x.trim()).filter(Boolean);
        const sources = document.getElementById('batch-sources').value.split('\n').map(x => x.trim()).filter(Boolean);
        const mediums = document.getElementById('batch-mediums').value.split('\n').map(x => x.trim()).filter(Boolean);
        const campaigns = document.getElementById('batch-campaigns').value.split('\n').map(x => x.trim()).filter(Boolean);

        if (urls.length === 0 || sources.length === 0 || mediums.length === 0 || campaigns.length === 0) {
            alert('Por favor, preencha os campos obrigatórios (URLs, Origens, Mídias e Campanhas).');
            return;
        }

        generatedBatchUrls = [];

        // Generate combinations (Cartesian Product)
        urls.forEach(rawUrl => {
            let cleanUrl = rawUrl;
            if (!/^https?:\/\//i.test(cleanUrl)) {
                cleanUrl = 'https://' + cleanUrl;
            }

            sources.forEach(src => {
                mediums.forEach(med => {
                    campaigns.forEach(cam => {
                        try {
                            const u = new URL(cleanUrl);
                            u.searchParams.set('par1', src); // Aluno
                            u.searchParams.set('par2', med); // Canal
                            u.searchParams.set('par3', cam); // Campanha

                            generatedBatchUrls.push(u.toString());
                        } catch (e) {
                            // Ignore individual invalid URL
                        }
                    });
                });
            });
        });

        // Display results
        if (generatedBatchUrls.length > 0) {
            batchResultsArea.classList.remove('d-none');
            batchCount.textContent = generatedBatchUrls.length;
            
            batchResultsList.innerHTML = '';
            generatedBatchUrls.forEach((link, idx) => {
                const div = document.createElement('div');
                div.className = 'batch-item';
                div.innerHTML = `
                    <span class="batch-item-url" title="${link}">${link}</span>
                    <button type="button" class="card-action-btn copy-single-batch" data-url="${link}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                `;

                div.querySelector('.copy-single-batch').addEventListener('click', () => {
                    navigator.clipboard.writeText(link).then(() => {
                        alert('URL copiada!');
                    });
                });

                batchResultsList.appendChild(div);
            });
        } else {
            alert('Não foi possível gerar as URLs. Verifique a formatação dos campos.');
        }
    });

    btnCopyAllBatch.addEventListener('click', () => {
        if (generatedBatchUrls.length === 0) return;
        const text = generatedBatchUrls.join('\n');
        navigator.clipboard.writeText(text).then(() => {
            alert('Todas as URLs copiadas para a área de transferência!');
        });
    });

    btnDownloadCsv.addEventListener('click', () => {
        if (generatedBatchUrls.length === 0) return;

        let csvContent = 'data:text/csv;charset=utf-8,URL Parametrizada\n';
        generatedBatchUrls.forEach(url => {
            csvContent += `"${url}"\n`;
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', 'ddm_urls_lote.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // --- INITIALIZE ---
    updateSavedList();
});
