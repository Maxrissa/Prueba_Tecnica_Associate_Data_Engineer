"""
pipeline.py
───────────
Pipeline de Datos - Prevención de Fraude
Banco: Detección de Anomalías de Gasto

Descripcion: Script modularizado que carga el CSV crudo, aplica
             las reglas de negocio (1, 2 y 3) y persiste el resultado
             en Parquet para que la fase de carga lo pueda cargar
"""

import os
import pandas as pd
from dotenv import load_dotenv

# Cargamos variables de entorno 
load_dotenv()

CSV_PATH = os.getenv("CSV_PATH", "data/transacciones_diarias.csv")
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"No se encontro el archivo: {CSV_PATH}")

# FASE 1 – EXTRACCION


def extraer_datos(ruta_csv: str) -> pd.DataFrame:
    """
    Carga el archivo CSV crudo y devuelve un DataFrame.
    Convierte fecha_hora a tipo datetime para operaciones ordenadas.
    """
    print(f"[EXTRACCIÓN] Leyendo archivo: {ruta_csv}")
    df = pd.read_csv(ruta_csv)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    print(f"  → {len(df)} registros cargados.")
    return df


# FASE 2 – TRANSFORMACION (Aqui se aplocan las reglas de Negocio 1, 2 y 3)

def regla_1_eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regla 1: Eliminar registros duplicados por id_transaccion.
    Se conserva la primera ocurrencia y se descartan las demas.
    """
    antes = len(df)
    df = df.drop_duplicates(subset=["id_transaccion"], keep="first")
    despues = len(df)
    print(f"[REGLA 1] Duplicados eliminados: {antes - despues} filas. Quedan {despues}.")
    return df


def regla_2_tratar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regla 2: Si monto_usd es nulo Y estado_transaccion == 'rechazada',
    asignar monto_usd = 0.0.
    """
    mascara = df["monto_usd"].isnull() & (df["estado_transaccion"] == "rechazada")
    df.loc[mascara, "monto_usd"] = 0.0
    print(f"[REGLA 2] Nulos en rechazadas corregidos: {mascara.sum()} registros.")
    return df


def regla_3_clasificar_monto_inusual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Regla 3: es_monto_inusual = True si monto_usd > 1500 Y tipo_comercio == 'internacional'.
    En cualquier otro caso es False.
    """
    df["es_monto_inusual"] = (
        (df["monto_usd"] > 1500) & (df["tipo_comercio"] == "internacional")
    )
    inusuales = df["es_monto_inusual"].sum()
    print(f"[REGLA 3] Transacciones marcadas como inusuales: {inusuales}.")
    return df


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orquesta la aplicacion de todas las reglas de transformacion en orden.
    """
    print("\n inicio de la transformacion ")
    df = regla_1_eliminar_duplicados(df)
    df = regla_2_tratar_nulos(df)
    df = regla_3_clasificar_monto_inusual(df)
    print(" fin de la transformacion \n")
    return df


# PUNTO DE ENTRADA (solo transformación + Parquet)


def main():
  
    print(" PIPELINE - TRANSFORMACIÓN DE TRANSACCIONES        ")
   

    df_crudo  = extraer_datos(CSV_PATH)
    df_limpio = transformar(df_crudo)

    salida = "data/transacciones_limpias.parquet"
    df_limpio.to_parquet(salida, index=False)
    print(f"[PIPELINE] DataFrame limpio guardado en: {salida}")
    print("\n Transformación finalizada.")


if __name__ == "__main__":
    main()
