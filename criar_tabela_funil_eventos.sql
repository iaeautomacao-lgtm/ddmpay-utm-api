USE ddm_ddmadv;

CREATE TABLE IF NOT EXISTS ddmpay_funil_eventos (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    tid VARCHAR(40) NULL,
    par1 VARCHAR(100) NULL,
    par2 VARCHAR(50) NULL,
    par3 VARCHAR(200) NULL,
    etapa ENUM('click', 'cpf_view', 'cpf_submit', 'payment_view', 'payment_start', 'paid') NOT NULL,
    etapa_label VARCHAR(80) NOT NULL,
    pagina_url TEXT NULL,
    metadata JSON NULL,
    ip VARCHAR(45) NULL,
    user_agent TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tid (tid),
    INDEX idx_par1 (par1),
    INDEX idx_par2 (par2),
    INDEX idx_par3 (par3),
    INDEX idx_etapa (etapa),
    INDEX idx_created_at (created_at)
);

-- Permissao necessaria para o usuario da aplicacao, se ele ainda nao tiver INSERT:
-- GRANT SELECT, INSERT ON ddm_ddmadv.ddmpay_funil_eventos TO 'ddm_ia'@'%';
