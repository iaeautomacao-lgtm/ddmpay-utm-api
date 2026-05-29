-- ============================================================================
-- SCRIPT DE CRIAÇÃO DE TABELAS - DASHBOARD DE MÉTRICAS
-- Motor Inteligente de Recuperação de Débitos
-- Data: 2026-05-29
-- ============================================================================

-- Usar database correto
USE ddm_ddmadv;

-- ============================================================================
-- 1. TABELA DE CAMPANHAS
-- ============================================================================
CREATE TABLE IF NOT EXISTS campanhas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(200) NOT NULL UNIQUE,
    descricao TEXT,
    canal ENUM('sms', 'whatsapp', 'email', 'rcs', 'outro') NOT NULL,
    data_inicio DATETIME NOT NULL,
    data_fim DATETIME NOT NULL,
    meta_conversoes INT DEFAULT 0,
    budget DECIMAL(12,2) DEFAULT 0.00,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_canal (canal),
    INDEX idx_ativo (ativo),
    INDEX idx_data_inicio (data_inicio)
);

-- ============================================================================
-- 2. TABELA DE CONVERSÕES (Pagamentos Confirmados)
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    link_id INT,
    cliente_id VARCHAR(100) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    status ENUM('pendente', 'pago', 'cancelado', 'falhado') DEFAULT 'pendente',
    data_pagamento DATETIME,
    data_cancelamento DATETIME,
    canal VARCHAR(50),
    campanha_id INT,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campanha_id) REFERENCES campanhas(id) ON DELETE SET NULL,
    INDEX idx_cliente_id (cliente_id),
    INDEX idx_status (status),
    INDEX idx_data_pagamento (data_pagamento),
    INDEX idx_canal (canal),
    INDEX idx_campanha_id (campanha_id),
    INDEX idx_created_at (created_at)
);

-- ============================================================================
-- 3. TABELA DE MÉTRICAS DIÁRIAS (Aggregações)
-- ============================================================================
CREATE TABLE IF NOT EXISTS metricas_diarias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data DATE NOT NULL,
    canal VARCHAR(50),
    campanha_id INT,
    total_cliques INT DEFAULT 0,
    total_conversoes INT DEFAULT 0,
    total_cancelamentos INT DEFAULT 0,
    valor_total DECIMAL(12,2) DEFAULT 0.00,
    taxa_conversao FLOAT DEFAULT 0.0,
    roi FLOAT DEFAULT 0.0,
    custo_disparo DECIMAL(12,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_data_canal_campanha (data, canal, campanha_id),
    FOREIGN KEY (campanha_id) REFERENCES campanhas(id) ON DELETE SET NULL,
    INDEX idx_data (data),
    INDEX idx_canal (canal),
    INDEX idx_campanha_id (campanha_id),
    INDEX idx_taxa_conversao (taxa_conversao)
);

-- ============================================================================
-- 4. TABELA DE LOGS DE WEBHOOK (Auditoria)
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo_evento VARCHAR(50) NOT NULL, -- 'pagamento', 'clique', 'cancelamento'
    cliente_id VARCHAR(100),
    dados_recebidos JSON,
    processado BOOLEAN DEFAULT FALSE,
    erro_processamento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tipo_evento (tipo_evento),
    INDEX idx_cliente_id (cliente_id),
    INDEX idx_processado (processado),
    INDEX idx_created_at (created_at)
);

-- ============================================================================
-- 5. TABELA DE PERFORMACE POR OPERADOR (Futuro)
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_operador (
    id INT PRIMARY KEY AUTO_INCREMENT,
    operador_id VARCHAR(100) NOT NULL,
    data DATE NOT NULL,
    total_contatos INT DEFAULT 0,
    total_conversoes INT DEFAULT 0,
    valor_total DECIMAL(12,2) DEFAULT 0.00,
    taxa_conversao FLOAT DEFAULT 0.0,
    meta_diaria INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_operador_data (operador_id, data),
    INDEX idx_operador_id (operador_id),
    INDEX idx_data (data)
);

-- ============================================================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Para queries de dashboard em tempo real
CREATE INDEX idx_conversoes_status_data ON conversoes(status, data_pagamento);
CREATE INDEX idx_metricas_data_canal ON metricas_diarias(data, canal);

-- ============================================================================
-- DADOS INICIAIS DE EXEMPLO (Opcional - comentado)
-- ============================================================================

/*
INSERT INTO campanhas (nome, descricao, canal, data_inicio, data_fim, meta_conversoes)
VALUES 
  ('Cobrança Maio 2026 - SMS', 'Campanha de SMS para cobrança de maio', 'sms', '2026-05-01', '2026-05-31', 500),
  ('Cobrança Maio 2026 - WhatsApp', 'Campanha de WhatsApp para cobrança de maio', 'whatsapp', '2026-05-01', '2026-05-31', 800),
  ('Cobrança Maio 2026 - Email', 'Campanha de E-mail para cobrança de maio', 'email', '2026-05-01', '2026-05-31', 300);
*/

-- ============================================================================
-- VIEWS ÚTEIS PARA DASHBOARD
-- ============================================================================

-- View de Resumo por Canal
CREATE OR REPLACE VIEW v_resumo_por_canal AS
SELECT 
    COALESCE(m.canal, 'TOTAL') as canal,
    SUM(m.total_cliques) as total_cliques,
    SUM(m.total_conversoes) as total_conversoes,
    SUM(m.valor_total) as valor_total,
    ROUND(AVG(m.taxa_conversao), 2) as taxa_conversao_media,
    ROUND(AVG(m.roi), 2) as roi_medio,
    COUNT(DISTINCT m.data) as dias_campanha
FROM metricas_diarias m
WHERE m.data >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY m.canal WITH ROLLUP
ORDER BY total_cliques DESC;

-- View de Performance por Campanha
CREATE OR REPLACE VIEW v_performance_campanha AS
SELECT 
    c.nome as campanha,
    c.canal,
    COUNT(DISTINCT DATE(co.data_pagamento)) as dias_ativa,
    SUM(CASE WHEN co.status = 'pago' THEN 1 ELSE 0 END) as conversoes,
    COUNT(*) as total_registros,
    SUM(CASE WHEN co.status = 'pago' THEN co.valor ELSE 0 END) as valor_total,
    ROUND(SUM(CASE WHEN co.status = 'pago' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as taxa_conversao
FROM campanhas c
LEFT JOIN conversoes co ON c.id = co.campanha_id
WHERE c.ativo = TRUE
GROUP BY c.id, c.nome, c.canal
ORDER BY conversoes DESC;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
