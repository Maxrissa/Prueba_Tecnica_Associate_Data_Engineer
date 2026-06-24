-- ============================================================
-- ANÁLISIS DE ANOMALÍAS DE GASTO
-- Banco - Área de Prevención de Fraude
-- ============================================================
-- Objetivo: Identificar clientes cuya transaccion actual sea
--           al menos 5 veces mayor a su transacción inmediatamente
--           anterior.
--
-- Regla de Negocio 4 aplicada:
--   Solo se evalúaran transacciones con estado_transaccion = 'aprobada'.
--   Las pendientes y rechazadas quedan excluidas del cálculo.



--  CTE 1: filtrar solo transacciones aprobadas 
WITH aprobadas AS (
    SELECT
        id_transaccion,
        id_cliente,
        fecha_hora,
        monto_usd,
        tipo_comercio,
        es_monto_inusual
    FROM transacciones_limpias
    WHERE estado_transaccion = 'aprobada'
),

--  CTE 2: calcular el monto de la transaccion anterior por cliente 
con_anterior AS (
    SELECT
        id_transaccion,
        id_cliente,
        fecha_hora,
        monto_usd,
        tipo_comercio,
        es_monto_inusual,
        -- Window Function: monto de la transacción inmediatamente anterior
        -- del mismo cliente, ordenada por fecha
        LAG(monto_usd) OVER (
            PARTITION BY id_cliente
            ORDER BY fecha_hora
        ) AS monto_anterior
    FROM aprobadas
),

-- ── CTE 3: calcular el ratio y marcar las anomalias ───────────────────────
anomalias AS (
    SELECT
        id_transaccion,
        id_cliente,
        fecha_hora,
        monto_usd          AS monto_actual,
        monto_anterior,
        ROUND(
            (monto_usd / NULLIF(monto_anterior, 0))::numeric, 2
        )                  AS ratio_vs_anterior,
        es_monto_inusual
    FROM con_anterior
    -- Solo interesara cuando haya una transaccion anterior con la que comparar
    WHERE monto_anterior IS NOT NULL
      -- Regla de deteccion: transaccion actual >= 5x la anterior
      AND monto_usd >= (5 * monto_anterior)
)

--  RESULTADO FINAL 
SELECT
    id_cliente,
    id_transaccion,
    fecha_hora,
    monto_anterior,
    monto_actual,
    ratio_vs_anterior,
    es_monto_inusual,
    -- Etiqueta descriptiva de la alerta
    CASE
        WHEN es_monto_inusual = TRUE
        THEN ' ALERTA CRÍTICA: monto inusual + salto brusco'
        ELSE '  ALERTA: salto brusco detectado'
    END AS nivel_alerta
FROM anomalias
ORDER BY ratio_vs_anterior DESC, fecha_hora;
