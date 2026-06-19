# DDMPay UTM — Documentação Técnica

**Projeto:** Rastreamento de disparos de cobrança (SMS/WhatsApp/RCS/E-mail) e medição de conversão em acordos/pagamentos — Grupo DDM.
**Status:** Funcional (ambiente local validado). Deploy de produção pendente de push.
**Última atualização:** 2026-06-18

---

## 1. Visão Geral

Ferramenta de marketing/cobrança que permite ao setor de planejamento:

1. **Gerar links rastreáveis** (UTM) com identificador do cliente, canal e campanha.
2. **Rastrear cliques** desses links (quem abriu, por qual canal, de qual campanha).
3. **Cruzar cliques com a base de acordos/pagamentos** já existente do DDMPay.
4. **Visualizar num dashboard** o funil: clicaram → fizeram acordo → pagaram, com valores em R$, segmentado por **campanha** e **canal**.

O diferencial: não exige nova tabela de conversões nem webhook. Cruza direto a base de produção existente (`devedorfisica`, `acordos`, `acordos_pagamentos`) via **VIEW SQL read-only**.

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.14 + Flask 3.x |
| Servidor produção | Gunicorn 21.2 (no Render) |
| Banco de dados | MySQL (charset misto: tabelas legadas em `latin1`) |
| Driver DB | mysql-connector-python 8.2 |
| Frontend | HTML estático + CSS puro + JavaScript vanilla |
| Gráficos | Chart.js 3.9.1 (CDN) |
| Fontes | Google Fonts (Inter, Outfit) |
| Hospedagem | Render (auto-deploy via GitHub) |
| Repositório | GitHub: `iaeautomacaoddm-lgtm/ddmpay-utm-api` |

### Dependências (`requirements.txt`)
```
flask==3.0.0
gunicorn==21.2.0
mysql-connector-python==8.2.0
```

---

## 3. Arquitetura / Fluxo de Dados

```
┌─────────────────────┐
│ Setor Planejamento  │  Acessa /utm → gera link rastreável
└──────────┬──────────┘
           │  link: .../acesso/?par1=CPF&par2=canal&par3=campanha
           ▼
┌─────────────────────────────────────────────┐
│ Cliente recebe o disparo (SMS/WhatsApp/etc)  │
│ e clica no link                              │
└──────────┬───────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│ https://ddmpay.ddmacordos.com/acesso/        │  ← DOMÍNIO DDMPAY
│  - grava clique na tabela links_ddmpay       │     (é quem PERSISTE o clique)
│  - redireciona o cliente p/ checkout DDMPay  │
└──────────┬───────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│ Cliente faz acordo / paga no DDMPay          │
│  → grava em acordos / acordos_pagamentos     │  (base de produção existente)
└──────────┬───────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│ VIEW vw_ddmpay_completo                      │  cruza par1(CPF) → devedor → acordo → pagamento
└──────────┬───────────────────────────────────┘
           ▼
┌─────────────────────────────────────────────┐
│ /dashboard (Flask + Chart.js)                │  lê /api/metricas → KPIs, gráficos, tabelas
└─────────────────────────────────────────────┘
```

### Parâmetros de rastreio (UTM)
| Param | Significado | Exemplo |
|-------|-------------|---------|
| `par1` | Identificador do cliente — **CPF (puro, só dígitos)** ou matrícula | `01924181223` |
| `par2` | Canal de disparo | `sms`, `whatsapp`, `rcs`, `email` |
| `par3` | Campanha / lote | `cobranca_maio_lote1` |

> ⚠️ **Importante:** `par1` deve ir como **CPF puro (11 dígitos, sem máscara)** para casar via índice com `devedorfisica.cpf`.

---

## 4. Estrutura de Arquivos

```
ddmpay-utm-api/
├── app.py                      # Aplicação Flask principal (PRODUÇÃO no Render)
├── dashboard.html              # Dashboard de métricas (Chart.js)
├── utm.html                    # Gerador de links UTM (individual + lote)
├── static/
│   ├── script.js               # Lógica do gerador UTM (gera/salva/exporta links)
│   └── style.css               # Estilos do gerador
├── api/
│   └── acesso.py               # [LEGADO] versão serverless Vercel (NÃO usada)
├── criar_tabelas_dashboard.sql # [LEGADO] plano abandonado (tabela conversoes etc)
├── requirements.txt
├── vercel.json                 # [LEGADO] config Vercel (deploy atual é Render)
├── README.md                   # desatualizado (descreve a versão Vercel antiga)
└── DOCUMENTACAO.md             # este arquivo
```

### Arquivos ativos vs legados
- **ATIVOS:** `app.py`, `dashboard.html`, `utm.html`, `static/*`, `requirements.txt`.
- **LEGADOS (ignorar):** `api/acesso.py`, `criar_tabelas_dashboard.sql`, `vercel.json`, `README.md`.
  Referem-se ao plano original (Vercel serverless + tabela `conversoes` + webhook n8n), **abandonado**.

---

## 5. Backend — `app.py`

Aplicação Flask. Conexão MySQL via env vars com fallback hardcoded.

### Configuração de banco
```python
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', '162.214.155.190'),
    'user': os.environ.get('MYSQL_USER', 'ddm_ia'),
    'password': os.environ.get('MYSQL_PASSWORD', '***'),
    'database': os.environ.get('MYSQL_DATABASE', 'ddm_ddmadv'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
}
```

### Endpoints

| Método | Rota | Função |
|--------|------|--------|
| GET | `/` | redireciona para `/dashboard` |
| GET | `/dashboard` | serve `dashboard.html` |
| GET | `/utm` | serve `utm.html` (gerador de links) |
| GET | `/acesso` | redireciona p/ checkout DDMPay (repassa os params). **Não grava** — o log é feito no domínio DDMPay |
| GET | `/health` | health check `{status: ok}` |
| GET | `/api/metricas` | **endpoint principal** — retorna JSON com todas as métricas |
| POST | `/webhook/pagamento` | [LEGADO] tenta gravar em `conversoes` (tabela inexistente) — sem efeito |

### `/api/metricas` — parâmetros
- `data_inicio` (YYYY-MM-DD, default: hoje − 30 dias)
- `data_fim` (YYYY-MM-DD, default: hoje)
- `dias` (int, default 30)

### `/api/metricas` — estrutura da resposta
```jsonc
{
  "periodo": { "data_inicio", "data_fim", "dias" },
  "metricas": {
    "total_cliques":         40,      // cliques com par1 no período
    "total_cliques_unicos":  9,       // par1 distintos (clientes únicos)
    "total_acordos":         3,       // usuários distintos com acordo
    "total_pagaram":         3,       // usuários distintos que pagaram
    "valor_total":           31991.57,// R$ pago (dedup por acordo)
    "ticket_medio":          10663.86,// valor_total / pagaram
    "por_canal":      { "SMS": 9, ... },              // cliques por canal (compat)
    "acordos_por_canal": { "SMS": 1, "Outro": 2 },    // usuários c/ acordo por canal
    "volume_por_canal":  { "SMS": 5334.48, ... },     // R$ pago por canal
    "por_canal_detalhe": {        // QUEBRA POR CANAL (par2)
      "SMS": { "cliques", "usuarios", "com_acordo", "pagaram", "valor_pago" }
    },
    "por_campanha": {             // QUEBRA POR CAMPANHA (par3)
      "teste_real": { "cliques", "usuarios", "com_acordo", "pagaram", "valor_pago" }
    },
    "acordos": [ /* últimos 20 acordos cruzados */ ],
    "tendencia_ultimos_7_dias": [ { "data", "cliques", "canal" } ]
  },
  "timestamp": "ISO-8601"
}
```

### Lógica de agregação
1. Query 1 — total de cliques e clientes únicos (sobre `links_ddmpay`, filtrado `url LIKE '%par1='`).
2. Query 2 — cliques por canal (compat).
3. Query 3 — tendência 7 dias (só cliques par1).
4. Query 4 — lê **`vw_ddmpay_completo`** e agrega em Python:
   - dedup de **valor pago por `nr_acordo`** (evita dobrar quando há cliques repetidos);
   - monta `por_canal_detalhe` e `por_campanha` (sets de `clique_id` / `par1` distintos);
   - flag de pagamento = `valor_pago > 0`.

---

## 6. Banco de Dados

- **Host:** `162.214.155.190` · **DB:** `ddm_ddmadv` · **User app:** `ddm_ia`
- **Permissões `ddm_ia`:** SELECT, CREATE VIEW, SHOW VIEW, TRIGGER.
  **Não tem:** CREATE TABLE, ALTER, DROP, INSERT, UPDATE.
  → Por isso a solução usa **VIEW** (não tabela). DDLs de tabela/DROP dependem do DBA (Jair).

### 6.1 Tabelas de produção usadas (somente leitura)

**`links_ddmpay`** — log de acessos do DDMPay (~173 mil linhas).
| Coluna | Tipo | Obs |
|--------|------|-----|
| id | int unsigned PK | |
| data_hora | datetime (indexado) | |
| url | text | contém `?par1=...&par2=...&par3=...` (extração via `SUBSTRING_INDEX`) |
| ip | varchar(45) | |
| user_agent | text | |

> O tráfego nativo do DDMPay usa `?c=ORIGEM&u=` (sem CPF). Nossos links rastreáveis usam `par1/par2/par3`. As métricas filtram `url LIKE '%par1='`.

**`devedorfisica`** — cadastro (~2,4 milhões). Usadas: `id` (PK), `cpf` (varchar 18, **latin1**, maioria 11 dígitos puros), `matricula` (latin1, formato irregular), `nome`.

**`acordos`** — acordos firmados. Usadas: `nr_acordo` (PK), `id_devedor` (FK→devedorfisica.id, indexado), `datacriacao`, `status` (código numérico, ex. `5`,`10`).

**`acordos_pagamentos`** — parcelas/pagamentos. Usadas: `acordo` (FK→acordos.nr_acordo, indexado), `valor`, `valor_pago`, `baixa_local` (data da baixa), `pix`, `vencimento`. Pago = `valor_pago > 0`.

### 6.2 Cadeia de cruzamento
```
links_ddmpay.url (par1 = CPF)
  → devedorfisica.cpf  → devedorfisica.id
  → acordos.id_devedor → acordos.nr_acordo
  → acordos_pagamentos.acordo  (SUM valor_pago)
```

### 6.3 VIEW em produção — `vw_ddmpay_completo` (read-only)

Cruza clique × devedor × acordo, com pagamento agregado por acordo.

**Colunas:** `clique_id, clique_data, par1, canal, lote, devedor_id, nome, nr_acordo, acordo_data, acordo_status, tem_acordo, valor_pago, valor_acordo, data_ultima_baixa, pago`.

**Pontos-chave de implementação:**
- Extração de par1/2/3 da `url` via `TRIM(SUBSTRING_INDEX(...))`.
- Join com `devedorfisica` por **CPF** (`CONVERT(... USING latin1)`) e fallback por **matrícula**.
- **GOTCHA de collation (resolvido):** `cpf`/`matricula` são `latin1` e `url` é `utf8mb4`. Sem o `CONVERT(... USING latin1)`, o MySQL ignora o índice e faz varredura de 2,2 M de linhas (**~59 s**). Com o CONVERT, usa índice → **~0,4 s**.
- Filtro `url LIKE '%par1='` e `par1 <> ''`.
- `GROUP BY (clique, devedor, acordo)` com `SUM(valor_pago)`, `MAX(baixa_local)`.

> ⚠️ Existem 4 VIEWs antigas de iteração (`vw_ddmpay_funil`, `_v2`, `_v3`, `_v4`) que **devem ser removidas pelo DBA** (`ddm_ia` não tem DROP). A VIEW válida é **`vw_ddmpay_completo`**.

```sql
-- limpeza (rodar com usuário admin)
DROP VIEW ddm_ddmadv.vw_ddmpay_funil;
DROP VIEW ddm_ddmadv.vw_ddmpay_funil_v2;
DROP VIEW ddm_ddmadv.vw_ddmpay_funil_v3;
DROP VIEW ddm_ddmadv.vw_ddmpay_funil_v4;
```

---

## 7. Frontend

### 7.1 Gerador de UTM — `utm.html` + `static/script.js`
- Dois modos: **Individual** e **Em Lote** (produto cartesiano de identificadores × canais × campanhas).
- Campos: URL destino, par1 (CPF/matrícula), par2 (canal), par3 (campanha).
- Modelos rápidos de canal (WhatsApp/SMS/RCS/E-mail).
- Salva links no `localStorage` (chave `ddm_saved_utms`); copiar, remover, exportar CSV.

> ✅ **URL-base padrão:** `https://ddmpay.ddmacordos.com/acesso/` (domínio DDMPay) — é quem **grava** o clique em `links_ddmpay`. Não usar a URL do Render como destino do link, pois `/acesso` no Render apenas redireciona (não persiste).

### 7.2 Dashboard — `dashboard.html`
- Auto-refresh a cada 30 s; filtros de data e canal.
- **KPIs:** Clientes Únicos, Cliques no Link, Acordos Gerados, Pagamentos DDMPay (R$), Taxa de Acordos, Ticket Médio.
- **Gráficos (Chart.js):** tendência 7 dias, acordos por canal (doughnut), volume R$ por canal (barras), funil.
- **Tabelas:** Últimos Acordos; Desempenho por Campanha (par3); Desempenho por Canal (par2) — cada linha com cliques / usuários únicos / com acordo / pagaram / valor pago.
- **Taxa de Acordos** = usuários com acordo ÷ usuários únicos que clicaram.
- **Sem dados mockados** (o gerador de números aleatórios da tendência foi removido).

---

## 8. Deploy

- **Plataforma:** Render (Web Service). Auto-deploy a cada push na branch `main` do GitHub.
- **Comando:** `gunicorn app:app` (entrypoint `app.py`).
- **Variáveis de ambiente** (recomendado configurar no Render em vez de hardcode): `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_PORT`.

### URLs de produção
| URL | Função |
|-----|--------|
| `https://ddmpay-utm-api.onrender.com/utm` | Gerador de links |
| `https://ddmpay-utm-api.onrender.com/dashboard` | Dashboard |
| `https://ddmpay.ddmacordos.com/acesso/?par1=...&par2=...&par3=...` | Rastreio + redirect (grava `links_ddmpay`) |

### Rodar localmente
```bash
pip install -r requirements.txt
python app.py            # serve em http://127.0.0.1:5000
```

---

## 9. Como Testar (ponta a ponta)

1. Acessar um link real (CPF que existe na base):
   `https://ddmpay.ddmacordos.com/acesso/?par1=01924181223&par2=sms&par3=teste_real`
2. Conferir o clique gravado:
   ```sql
   SELECT id, data_hora, url FROM ddm_ddmadv.links_ddmpay
   WHERE url LIKE '%par1=%' ORDER BY id DESC LIMIT 20;
   ```
3. Conferir o cruzamento:
   ```sql
   SELECT * FROM ddm_ddmadv.vw_ddmpay_completo WHERE par1 = '01924181223';
   ```
4. Abrir o dashboard com o período cobrindo a data do clique.

---

## 10. Segurança / Boas Práticas (pendências)
- 🔴 **Credenciais hardcoded** em `app.py` e `api/acesso.py` (e mencionadas no README). Migrar 100% para env vars no Render e **remover do código/histórico**.
- Banco acessível por IP externo com o usuário `ddm_ia` — manter privilégios mínimos (já é só leitura + view).
- `/webhook/pagamento` legado deveria ser removido (sem efeito, gera ruído de log).

---

## 11. Regras do Projeto
- Proibido `DELETE`/alterações destrutivas no banco.
- Mexer apenas em tabelas/views criadas para este projeto.
- `ddm_ia` é leitura + `CREATE VIEW`; qualquer DDL de tabela/DROP é feito pelo DBA.
- Sempre apresentar plano e aguardar aprovação antes de editar arquivos.

---

## 12. Roadmap / Pendências
1. **Deploy de produção** (push para `main` → Render). Atualmente alterações estão só locais.
2. **DBA dropar** as 4 VIEWs antigas (seção 6.3).
3. **Distribuir links reais** (par1 = CPF puro) pelo setor de planejamento, apontando para o domínio DDMPay.
4. (Opcional) Decodificar `acordos.status` (códigos numéricos) para exibir o status do acordo.
5. Mover credenciais para variáveis de ambiente e limpar o histórico do repositório.
6. (Performance) `/api/metricas` leva ~5 s por causa do `LIKE '%par1='` sobre 173 k linhas (curinga à esquerda não usa índice). Avaliar coluna derivada/índice funcional se o volume crescer.

---

## 13. Histórico
- Plano original (Vercel serverless + tabela `conversoes` + webhook n8n) **abandonado** — `ddm_ia` não pode criar tabela; arquitetura migrou para **VIEW de cruzamento** sobre a base existente.
- Registro detalhado da implementação: `../REGISTRO_SESSAO_2026-06-18.txt`.
