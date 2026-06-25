"""
cargar_supabase.py


Para cargar Subpabase hacemos uso del archivo .env con:
    SUPABASE_URL=https://<project>.supabase.co
    SUPABASE_KEY=<service_key>
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

#  Cargamos las variables de entorno 
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PARQUET_PATH = os.getenv("PARQUET_PATH", "data/transacciones_limpias.parquet")


# CONEXION


def conectar_supabase() -> Client:
    """Crea y devuelve el cliente de Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Faltan las variables de entorno SUPABASE_URL y/o SUPABASE_KEY.\n"
            "Crea un archivo .env en la raíz del proyecto con esas credenciales."
        )
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[SUPABASE] Conexión establecida correctamente.")
    return client


# CARGA

def cargar_a_supabase(
    df: pd.DataFrame,
    client: Client,
    tabla: str = "transacciones_limpias",
    lote: int = 500,
) -> None:
    """
    Cargamos el DataFrame procesado a la tabla de Supabase en lotes.

    Parametros
    ----------
    df     : DataFrame ya transformado (resultado de pipeline.py).
    client : Cliente de Supabase autenticado.
    tabla  : Nombre de la tabla destino (por defecto 'transacciones_limpias').
    lote   : Numero de filas por lote de inserción (por defecto 500).
    """
    df_carga = df.copy()

    # PostgreSQL espera timestamps en formato ISO string
    df_carga["fecha_hora"] = df_carga["fecha_hora"].astype(str)

    # Supabase que requiere booleanos Python nativos (no numpy.bool_)
    df_carga["es_monto_inusual"] = df_carga["es_monto_inusual"].astype(bool)

    registros = df_carga.to_dict(orient="records")
    total     = len(registros)

    print(f"[CARGA] Insertando {total} registros en la tabla '{tabla}'...")

    for i in range(0, total, lote):
        fragmento = registros[i : i + lote]
        client.table(tabla).insert(fragmento).execute()
        print(f"  → Lote {i // lote + 1}: {len(fragmento)} filas insertadas.")

    print("[CARGA] Carga completa.")


# PUNTO DE ENTRADA

def main():

    print("║   CARGA A SUPABASE - TRANSACCIONES LIMPIAS   ")
   

    if not os.path.exists(PARQUET_PATH):
        raise FileNotFoundError(
            f"No se encontró el archivo Parquet: {PARQUET_PATH}\n"
            "Ejecuta primero: python src/pipeline.py"
        )

    print(f"[CARGA] Leyendo archivo Parquet: {PARQUET_PATH}")
    df_limpio = pd.read_parquet(PARQUET_PATH)
    print(f"  → {len(df_limpio)} registros listos para cargar.\n")

    supabase = conectar_supabase()
    cargar_a_supabase(df_limpio, supabase)

    print("\n Carga finalizada.")


if __name__ == "__main__":
    main()
