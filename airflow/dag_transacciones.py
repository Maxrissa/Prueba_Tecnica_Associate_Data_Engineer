"""
dag_transacciones.py
────────────────────
DAG de Apache Airflow que orquesta el pipeline diario de detección
de anomalías de gasto del área de prevención de fraude.

Programación: todos los días a las 11:30 PM (23:30)
Dependencia estricta: la carga a la BD y la consulta SQL
solo se ejecutan si la transformación Python finalizó con éxito.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator


# ── Argumentos por defecto del DAG ────────────────────────────────────────────
default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,                      # no depende de ejecuciones anteriores
    "email": ["fraude-alertas@banco.com"],
    "email_on_failure": True,                      # notificar si falla
    "email_on_retry": False,
    "retries": 2,                                  # reintentar 2 veces ante fallo
    "retry_delay": timedelta(minutes=5),           # esperar 5 min entre reintentos
    "execution_timeout": timedelta(minutes=30),    # máximo 30 min por tarea
}


# ── Definición del DAG ─────────────────────────────────────────────────────────
with DAG(
    dag_id="pipeline_fraude_diario",
    description="Pipeline ETL diario: CSV crudo → limpieza → Supabase → análisis de anomalías",
    schedule="30 23 * * *",                        # 23:30 todos los días
    start_date=datetime(2026, 1, 1),
    catchup=False,                                 # no ejecutar fechas pasadas
    tags=["fraude", "etl", "diario"],
    default_args=default_args,
) as dag:

    # ── TAREA 1: Descargar / verificar que el CSV esté disponible ─────────────
    verificar_csv = BashOperator(
        task_id="verificar_archivo_csv",
        bash_command=(
            "FILE=/opt/airflow/fraude_pipeline/data/transacciones_diarias.csv; "
            "if [ ! -f \"$FILE\" ]; then "
            "  echo 'ERROR: Archivo no encontrado: $FILE'; exit 1; "
            "else "
            "  echo \"Archivo encontrado: $(wc -l < $FILE) líneas.\"; "
            "fi"
        ),
    )

    # ── TAREA 2: Transformación Python (reglas de negocio 1, 2 y 3) ──────────
    #   Se importa la función main() del script modularizado.
    def ejecutar_transformacion():
        """Wrapper que importa y ejecuta el pipeline de transformación."""
        import sys
        sys.path.insert(0, "/opt/airflow/fraude_pipeline/src")
        from pipeline import extraer_datos, transformar

        CSV_PATH = "/opt/airflow/fraude_pipeline/data/transacciones_diarias.csv"
        df_crudo  = extraer_datos(CSV_PATH)
        df_limpio = transformar(df_crudo)

        # Persistir el resultado en Parquet para la siguiente tarea
        salida = "/opt/airflow/fraude_pipeline/data/transacciones_limpias.parquet"
        df_limpio.to_parquet(salida, index=False)
        print(f"[AIRFLOW] DataFrame limpio guardado en: {salida}")

    transformacion_python = PythonOperator(
        task_id="transformacion_python",
        python_callable=ejecutar_transformacion,
    )

    # ── TAREA 3: Carga a Supabase (PostgreSQL) ────────────────────────────────
    def ejecutar_carga():
        """Carga el Parquet intermedio a Supabase."""
        import sys, pandas as pd
        sys.path.insert(0, "/opt/airflow/fraude_pipeline/src")
        from cargar_supabase import conectar_supabase, cargar_a_supabase

        salida = "/opt/airflow/fraude_pipeline/data/transacciones_limpias.parquet"
        df_limpio = pd.read_parquet(salida)

        supabase = conectar_supabase()
        cargar_a_supabase(df_limpio, supabase)

    carga_supabase = PythonOperator(
        task_id="carga_supabase",
        python_callable=ejecutar_carga,
    )

    # ── TAREA 4: Consulta SQL analítica de anomalías ──────────────────────────
    #   Usa la conexión "supabase_postgres" configurada en Airflow Connections.
    analisis_anomalias = PostgresOperator(
        task_id="analisis_anomalias_sql",
        postgres_conn_id="supabase_postgres",          # configurar en Airflow UI
        sql="sql/consulta_anomalias.sql",              # relativo al folder airflow/dags/
        autocommit=True,
    )

    # ── DEPENDENCIAS: define el orden de ejecución ────────────────────────────
    #
    #   verificar_csv → transformacion_python → carga_supabase → analisis_anomalias
    #
    #   Si cualquier tarea falla, las siguientes NO se ejecutan.
    verificar_csv >> transformacion_python >> carga_supabase >> analisis_anomalias
