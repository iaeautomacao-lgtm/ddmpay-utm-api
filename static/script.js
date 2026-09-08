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
    const destinationLink = document.getElementById('destination-link');

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
    let currentTrackingId = '';
    let currentTrackingSignature = '';

    const buildTrackingId = () => {
        return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    };

    const base64UrlEncode = (value) => {
        const bytes = new TextEncoder().encode(value);
        let binary = '';
        bytes.forEach(byte => binary += String.fromCharCode(byte));
        return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
    };

    const getPublicBaseUrl = () => `${window.location.origin}`;

    const buildShortLink = ({ par1, par2, par3, tid }) => {
        const payload = [par1, par2, par3, tid];
        return `${getPublicBaseUrl()}/l/${base64UrlEncode(JSON.stringify(payload))}`;
    };

    const buildDestinationLink = (baseURL, { par1, par2, par3, tid }) => {
        const url = new URL(baseURL);
        url.searchParams.set('par1', par1);
        url.searchParams.set('par2', par2);
        url.searchParams.set('par3', par3);
        url.searchParams.set('tid', tid);
        return url.toString();
    };

    const resolveShortLink = async (baseURL, payload) => {
        const fallback = {
            shortUrl: buildShortLink(payload),
            destinationUrl: buildDestinationLink(baseURL, payload)
        };

        try {
            const response = await fetch('/api/short-link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) return fallback;
            const data = await response.json();
            if (!data.short_url || !data.destination_url) return fallback;

            return {
                shortUrl: data.short_url,
                destinationUrl: data.destination_url
            };
        } catch (e) {
            return fallback;
        }
    };

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
            document.getElementById('ind-medium').value = item.getAttribute('data-medium');
            buildIndividualURL();
        });
    });

    // Apply Model to Batch Textareas (adds to the lists)
    dropdownItemsBatch.forEach(item => {
        item.addEventListener('click', () => {
            const addTextToTextarea = (id, text) => {
                if (!text) return;
                const ta = document.getElementById(id);
                const current = ta.value.trim();
                if (current) {
                    ta.value = current + '\n' + text;
                } else {
                    ta.value = text;
                }
            };
            addTextToTextarea('batch-mediums', item.getAttribute('data-medium'));
        });
    });

    // --- CRIAÇÃO INDIVIDUAL LOGIC ---
    const buildIndividualURL = async () => {
        // URL padrão do DDMPay (domínio que GRAVA o clique em links_ddmpay)
        let baseURL = indUrl.value.trim() || 'https://ddmpay.ddmacordos.com/acesso/';
        
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
                par1: document.getElementById('ind-source').value.trim(),
                par2: document.getElementById('ind-medium').value.trim(),
                par3: document.getElementById('ind-campaign').value.trim(),
            };

            if (!params.par1 || !params.par2 || !params.par3) {
                resetIndividualUI();
                return;
            }

            const signature = `${url.origin}${url.pathname}|${params.par1}|${params.par2}|${params.par3}`;
            if (signature !== currentTrackingSignature) {
                currentTrackingSignature = signature;
                currentTrackingId = buildTrackingId();
            }

            const payload = { ...params, tid: currentTrackingId };
            outputLink.textContent = 'Gerando URL curta...';
            outputLink.classList.remove('active');

            const result = await resolveShortLink(url.toString(), payload);

            outputLink.textContent = result.shortUrl;
            outputLink.classList.add('active');
            if (destinationLink) {
                destinationLink.textContent = result.destinationUrl;
                destinationLink.title = result.destinationUrl;
            }

        } catch (e) {
            resetIndividualUI();
        }
    };

    const resetIndividualUI = () => {
        outputLink.textContent = 'Preencha os campos para gerar sua URL curta';
        outputLink.classList.remove('active');
        if (destinationLink) {
            destinationLink.textContent = 'Preencha os campos para visualizar o destino.';
            destinationLink.removeAttribute('title');
        }
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
                    <div class="saved-card-link" title="${item.destinationUrl || ''}">${item.destinationUrl || ''}</div>
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
            destinationUrl: destinationLink ? destinationLink.textContent : '',
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

    btnGenerateBatch.addEventListener('click', async () => {
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
        for (const rawUrl of urls) {
            let cleanUrl = rawUrl;
            if (!/^https?:\/\//i.test(cleanUrl)) {
                cleanUrl = 'https://' + cleanUrl;
            }

            for (const src of sources) {
                for (const med of mediums) {
                    for (const cam of campaigns) {
                        try {
                            const u = new URL(cleanUrl);
                            const payload = {
                                par1: src,
                                par2: med,
                                par3: cam,
                                tid: buildTrackingId()
                            };

                            generatedBatchUrls.push(await resolveShortLink(u.toString(), payload));
                        } catch (e) {
                            // Ignore individual invalid URL
                        }
                    }
                }
            }
        }

        // Display results
        if (generatedBatchUrls.length > 0) {
            batchResultsArea.classList.remove('d-none');
            batchCount.textContent = generatedBatchUrls.length;
            
            batchResultsList.innerHTML = '';
            generatedBatchUrls.forEach((item, idx) => {
                const div = document.createElement('div');
                div.className = 'batch-item';
                div.innerHTML = `
                    <span class="batch-item-url" title="${item.destinationUrl}">${item.shortUrl}</span>
                    <button type="button" class="card-action-btn copy-single-batch" data-url="${item.shortUrl}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                `;

                div.querySelector('.copy-single-batch').addEventListener('click', () => {
                    navigator.clipboard.writeText(item.shortUrl).then(() => {
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
        const text = generatedBatchUrls.map(item => item.shortUrl).join('\n');
        navigator.clipboard.writeText(text).then(() => {
            alert('Todas as URLs copiadas para a área de transferência!');
        });
    });

    btnDownloadCsv.addEventListener('click', () => {
        if (generatedBatchUrls.length === 0) return;

        let csvContent = 'data:text/csv;charset=utf-8,URL Curta,Destino Final\n';
        generatedBatchUrls.forEach(item => {
            csvContent += `"${item.shortUrl}","${item.destinationUrl}"\n`;
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
