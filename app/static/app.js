document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
  }

  let currentDossier = null;

  // DOM Elements
  const searchForm = document.getElementById("search-form");
  const searchInput = document.getElementById("search-input");
  const searchBtn = document.getElementById("search-btn");
  const loadingState = document.getElementById("loading-state");
  const errorState = document.getElementById("error-state");
  const errorMessage = document.getElementById("error-message");
  const dossierView = document.getElementById("dossier-view");
  const btnCopyCrm = document.getElementById("btn-copy-crm");

  // Quick Examples Click Handlers
  document.querySelectorAll(".quick-example").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        searchInput.value = query;
        performSearch(query);
      }
    });
  });

  // Search Form Submit Handler
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (query) {
      performSearch(query);
    }
  });

  // Tab Navigation Handler
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabTarget = btn.getAttribute("data-tab");

      // Set active tab button styling
      document.querySelectorAll(".tab-btn").forEach((b) => {
        b.classList.remove("active", "border-blue-500", "text-blue-400");
        b.classList.add("border-transparent", "text-slate-400");
      });
      btn.classList.add("active", "border-blue-500", "text-blue-400");
      btn.classList.remove("border-transparent", "text-slate-400");

      // Show targeted tab content
      document.querySelectorAll(".tab-content").forEach((c) => {
        c.classList.add("hidden");
      });
      const targetEl = document.getElementById(tabTarget);
      if (targetEl) {
        targetEl.classList.remove("hidden");
      }
    });
  });

  // Copy Markdown for CRM Handler
  if (btnCopyCrm) {
    btnCopyCrm.addEventListener("click", async () => {
      if (!currentDossier) return;

      try {
        const resp = await fetch("/api/dossier/export/markdown", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dossier: currentDossier }),
        });

        if (resp.ok) {
          const data = await resp.json();
          await navigator.clipboard.writeText(data.markdown);

          const origText = btnCopyCrm.innerHTML;
          btnCopyCrm.innerHTML = `<i data-lucide="check" class="w-4 h-4 text-emerald-400"></i><span>Copiado para CRM!</span>`;
          if (window.lucide) lucide.createIcons();

          setTimeout(() => {
            btnCopyCrm.innerHTML = origText;
            if (window.lucide) lucide.createIcons();
          }, 2500);
        }
      } catch (err) {
        alert("Erro ao copiar Markdown do CRM.");
      }
    });
  }

  // Perform OSINT Search Call
  async function performSearch(query) {
    // Show Loading, Hide Dossier & Error
    loadingState.classList.remove("hidden");
    errorState.classList.add("hidden");
    dossierView.classList.add("hidden");
    searchBtn.disabled = true;

    try {
      const resp = await fetch("/api/dossier/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "Erro ao consultar base de dados OSINT.");
      }

      const dossier = await resp.json();
      currentDossier = dossier;

      renderDossier(dossier);

      loadingState.classList.add("hidden");
      dossierView.classList.remove("hidden");
    } catch (err) {
      loadingState.classList.add("hidden");
      errorMessage.textContent = err.message || "Erro inesperado ao gerar dossiê.";
      errorState.classList.remove("hidden");
    } finally {
      searchBtn.disabled = false;
    }
  }

  // Render Dossier UI
  function renderDossier(dossier) {
    const meta = dossier.metadata || {};
    const company = dossier.company_profile || {};
    const playbook = dossier.sales_playbook || {};
    const digital = dossier.digital_footprint || {};
    const tech = digital.tech_stack || {};
    const osint = dossier.osint_brazuca || {};

    // Header Badges & Lead Info
    document.getElementById("lead-name").textContent = company.nome_fantasia || company.razao_social || meta.lead_name;
    document.getElementById("lead-cnpj").textContent = company.cnpj_formatted || meta.cnpj;
    document.getElementById("lead-location").textContent = `${company.municipio || 'N/A'}/${company.uf || ''}`;
    document.getElementById("lead-capital").textContent = company.capital_social_formatted || "R$ 0,00";

    const badgeSit = document.getElementById("badge-situacao");
    badgeSit.textContent = (company.situacao_cadastral || "Ativa").toUpperCase();
    if ((company.situacao_cadastral || "").toLowerCase().includes("ativa")) {
      badgeSit.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    } else {
      badgeSit.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30";
    }

    document.getElementById("badge-porte").textContent = company.porte || "Demais";
    document.getElementById("badge-matriz").textContent = company.matriz_filial || "Matriz";

    // TAB 1: Resumo & Playbook
    document.getElementById("summary-text").innerHTML = formatMarkdownBold(dossier.executive_summary || "");

    renderList("list-icebreakers", playbook.icebreakers, "check-circle", "text-emerald-400");
    renderList("list-painpoints", playbook.pain_points, "flame", "text-amber-400");
    renderList("list-pitch", playbook.pitch_angles, "arrow-right", "text-indigo-400");
    renderList("list-risks", playbook.risk_flags, "shield-alert", "text-rose-400");

    // TAB 2: Dados Corporativos
    document.getElementById("company-razao").textContent = company.razao_social || "Não informada";
    document.getElementById("company-fantasia").textContent = company.nome_fantasia || company.razao_social || "Não informada";
    document.getElementById("company-data-abertura").textContent = company.data_inicio_atividade || "Não informada";
    document.getElementById("company-natureza").textContent = company.natureza_juridica || "Não informada";
    document.getElementById("company-telefone").textContent = company.ddd_telefone || "Não informado";
    document.getElementById("company-email").textContent = company.email || "Não informado";

    const endStr = `${company.logradouro || ''}, ${company.numero || ''} ${company.complemento || ''} - ${company.bairro || ''}, ${company.municipio || ''}/${company.uf || ''} - CEP: ${company.cep || ''}`;
    document.getElementById("company-endereco").textContent = endStr;

    // CNAE
    const cnaeP = company.atividade_principal || {};
    document.getElementById("company-cnae-principal").textContent = `${cnaeP.code || ''} - ${cnaeP.description || ''}`;

    const secEl = document.getElementById("company-cnae-secundarias");
    secEl.innerHTML = "";
    if (company.cnaes_secundarios && company.cnaes_secundarios.length > 0) {
      company.cnaes_secundarios.forEach((c) => {
        const item = document.createElement("div");
        item.className = "p-2 bg-slate-900/60 border border-slate-800 rounded-lg text-slate-300 font-mono";
        item.textContent = `${c.code} - ${c.description}`;
        secEl.appendChild(item);
      });
    } else {
      secEl.innerHTML = "<p class='text-slate-500 italic'>Nenhuma atividade secundária registrada.</p>";
    }

    // QSA List
    const qsaList = company.qsa || [];
    document.getElementById("count-qsa").textContent = `${qsaList.length} membro(s)`;
    const qsaContainer = document.getElementById("qsa-list");
    qsaContainer.innerHTML = "";

    if (qsaList.length > 0) {
      qsaList.forEach((s) => {
        const card = document.createElement("div");
        card.className = "p-4 bg-slate-900 border border-slate-700/80 rounded-xl space-y-1.5";
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-100 text-sm">${s.nome}</span>
            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">${s.qualificacao}</span>
          </div>
          <p class="text-xs text-slate-400">
            ${s.cpf_cnpj ? `<strong>CPF/CNPJ:</strong> ${s.cpf_cnpj}` : ''}
            ${s.faixa_etaria ? ` • <strong>Faixa Etária:</strong> ${s.faixa_etaria}` : ''}
          </p>
        `;
        qsaContainer.appendChild(card);
      });
    } else {
      qsaContainer.innerHTML = "<p class='text-slate-400 text-sm italic col-span-2'>Quadro de Sócios não disponível publicamente para este CNPJ.</p>";
    }

    // TAB 3: Digital & Tech Stack
    document.getElementById("tech-domain").textContent = digital.domain || "Não encontrado";
    document.getElementById("tech-email-provider").textContent = tech.email_provider || "Desconhecido";
    document.getElementById("tech-web-hosting").textContent = tech.web_hosting || "Desconhecido";

    const badgeContainer = document.getElementById("tech-badges");
    badgeContainer.innerHTML = "";
    if (tech.detected_services && tech.detected_services.length > 0) {
      tech.detected_services.forEach((service) => {
        const b = document.createElement("span");
        b.className = "px-3 py-1 bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-medium rounded-full text-xs flex items-center gap-1.5";
        b.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i> ${service}`;
        badgeContainer.appendChild(b);
      });
    } else {
      badgeContainer.innerHTML = "<p class='text-slate-400 text-xs italic'>Nenhum serviço ou CRM detectado via DNS público.</p>";
    }

    // RDAP Info
    const rdap = digital.rdap || {};
    const rdapEl = document.getElementById("rdap-info");
    if (rdap.registered) {
      rdapEl.innerHTML = `
        <p><strong>Titular do Domínio:</strong> ${rdap.owner || 'Não divulgado'} (${rdap.owner_id || 'N/A'})</p>
        <p><strong>Nameservers:</strong> ${(rdap.nameservers || []).join(', ') || 'N/A'}</p>
        <p><strong>Criado em:</strong> ${rdap.created_at || 'N/A'} | <strong>Expira em:</strong> ${rdap.expires_at || 'N/A'}</p>
      `;
    } else {
      rdapEl.innerHTML = `<p class="text-slate-400 italic">${rdap.notes || 'Consulta RDAP não aplicável ou domínio não registrado no .br.'}</p>`;
    }

    // TAB 4: OSINT Brazuca & Dorks
    const osintContainer = document.getElementById("osint-categories");
    osintContainer.innerHTML = "";

    if (osint.categories && osint.categories.length > 0) {
      osint.categories.forEach((cat) => {
        const block = document.createElement("div");
        block.className = "bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 space-y-4";

        let resourcesHtml = "";
        cat.resources.forEach((res) => {
          resourcesHtml += `
            <a href="${res.url}" target="_blank" rel="noopener noreferrer" class="p-3.5 bg-slate-900 hover:bg-slate-900/80 border border-slate-700 rounded-xl flex items-start justify-between gap-4 group transition">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-blue-400 text-sm group-hover:underline">${res.name}</span>
                  <span class="px-2 py-0.5 bg-slate-800 text-slate-300 text-[10px] uppercase font-bold rounded border border-slate-700">${res.tag}</span>
                </div>
                <p class="text-xs text-slate-400">${res.notes}</p>
              </div>
              <i data-lucide="external-link" class="w-4 h-4 text-slate-500 group-hover:text-blue-400 shrink-0 mt-1 transition"></i>
            </a>
          `;
        });

        block.innerHTML = `
          <div>
            <h4 class="text-base font-bold text-slate-100">${cat.title}</h4>
            <p class="text-xs text-slate-400 mt-0.5">${cat.description}</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">${resourcesHtml}</div>
        `;
        osintContainer.appendChild(block);
      });
    }

    if (window.lucide) {
      lucide.createIcons();
    }
  }

  // Helper List Renderer
  function renderList(elementId, items, iconName, iconColorClass) {
    const el = document.getElementById(elementId);
    el.innerHTML = "";
    if (items && items.length > 0) {
      items.forEach((item) => {
        const li = document.createElement("li");
        li.className = "flex items-start gap-2 bg-slate-900/50 p-3 rounded-xl border border-slate-800/80";
        li.innerHTML = `
          <i data-lucide="${iconName}" class="w-4 h-4 ${iconColorClass} shrink-0 mt-0.5"></i>
          <span>${formatMarkdownBold(item)}</span>
        `;
        el.appendChild(li);
      });
    } else {
      el.innerHTML = "<li class='text-slate-500 italic text-xs'>Nenhum item mapeado.</li>";
    }
  }

  // Helper to format **bold** markdown to HTML
  function formatMarkdownBold(text) {
    if (!text) return "";
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }
});
