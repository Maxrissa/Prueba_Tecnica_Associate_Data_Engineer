CREATE TABLE IF NOT EXISTS transacciones_limpias (

id_transaccion TEXT PRIMARY KEY,

id_cliente TEXT NOT NULL,

fecha_hora TIMESTAMPTZ NOT NULL,

monto_usd NUMERIC(12,2)
    CHECK (monto_usd >= 0),

tipo_comercio TEXT
    CHECK (
        tipo_comercio IN (
            'nacional',
            'internacional'
        )
    ),

estado_transaccion TEXT
    CHECK (
        estado_transaccion IN (
            'aprobada',
            'rechazada',
            'pendiente'
        )
    ),

es_monto_inusual BOOLEAN NOT NULL DEFAULT FALSE

);

CREATE INDEX IF NOT EXISTS idx_cliente_fecha
ON transacciones_limpias (
id_cliente,
fecha_hora
);

CREATE INDEX IF NOT EXISTS idx_estado
ON transacciones_limpias (
estado_transaccion
);