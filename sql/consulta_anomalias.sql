-- ============================================================
-- ANALISIS DE ANOMALIAS DE GASTO
-- Banco - Prevencion de Fraude
-- ============================================================

-- objetivo: detectar transacciones donde el monto actual
-- es al menos 5 veces mayor que la anterior del mismo cliente

-- regla de negocio 4:
-- solo se consideran transacciones aprobadas

-- ============================================================

-- CTE 1: filtrar solo transacciones aprobadas
WITH aprobadas AS (
    SELECT
        id_transaccion,  -- id unico de la transaccion
        id_cliente,      -- id del cliente
        fecha_hora,      -- fecha y hora de la transaccion
        monto_usd,       -- monto de la transaccion en USD
        tipo_comercio,   -- tipo de comercio (nacional/internacional)
        es_monto_inusual -- bandera de monto inusual
    FROM transacciones_limpias
    WHERE estado_transaccion = 'aprobada'  -- regla 4: solo aprobadas
),

-- CTE 2: obtener transaccion anterior por cliente
con_anterior AS (
    SELECT
        id_transaccion,  -- id de transaccion actual
        id_cliente,      -- id del cliente
        fecha_hora,      -- fecha de la transaccion
        monto_usd,       -- monto actual
        tipo_comercio,   -- tipo de comercio
        es_monto_inusual,-- flag de monto inusual

        -- lag obtiene el valor de la transaccion anterior del mismo cliente
        LAG(monto_usd) OVER (
            PARTITION BY id_cliente   -- separa por cliente
            ORDER BY fecha_hora       -- orden cronologico
        ) AS monto_anterior
    FROM aprobadas
),

-- CTE 3: calcular anomalias de salto de gasto
anomalias AS (
    SELECT
        id_transaccion,  -- id de transaccion
        id_cliente,      -- id cliente
        fecha_hora,      -- fecha transaccion

        monto_usd AS monto_actual,  -- renombrar monto actual
        monto_anterior,             -- monto previo del cliente

        -- calcular ratio entre monto actual y anterior
        ROUND(
            (monto_usd / NULLIF(monto_anterior, 0))::numeric,
            2
        ) AS ratio_vs_anterior,

        es_monto_inusual  -- indicador de monto inusual
    FROM con_anterior

    -- eliminar primeras transacciones sin comparacion
    WHERE monto_anterior IS NOT NULL

      -- regla de negocio: detectar saltos >= 5 veces
      AND (monto_usd / NULLIF(monto_anterior, 0)) >= 5
)

-- resultado final
SELECT
    id_cliente,         -- cliente afectado
    id_transaccion,     -- transaccion detectada
    fecha_hora,         -- fecha evento
    monto_anterior,     -- valor previo
    monto_actual,       -- valor actual
    ratio_vs_anterior,  -- multiplicador de incremento

    es_monto_inusual,   -- flag de monto inusual

    -- etiqueta de alerta
    CASE
        WHEN es_monto_inusual = TRUE
        THEN 'ALERTA CRITICA: monto inusual + salto brusco'
        ELSE 'ALERTA: salto brusco detectado'
    END AS nivel_alerta

FROM anomalias

-- ordenar de mayor a menor impacto
ORDER BY ratio_vs_anterior DESC, fecha_hora;