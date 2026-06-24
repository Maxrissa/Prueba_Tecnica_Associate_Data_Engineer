-- ============================================================
-- SCHEMA: Tabla principal en Supabase (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS transacciones_limpias (
    id_transaccion     TEXT        PRIMARY KEY,
    id_cliente         TEXT        NOT NULL,
    fecha_hora         TIMESTAMPTZ NOT NULL,
    monto_usd          NUMERIC(12, 2),
    tipo_comercio      TEXT,
    estado_transaccion TEXT,
    es_monto_inusual   BOOLEAN     NOT NULL DEFAULT FALSE
);

-- creamos el indice para acelerar las consultas por cliente y fecha
CREATE INDEX IF NOT EXISTS idx_cliente_fecha
    ON transacciones_limpias (id_cliente, fecha_hora);

-- creamos el indice para filtrar rápidamente por estado
CREATE INDEX IF NOT EXISTS idx_estado
    ON transacciones_limpias (estado_transaccion);
