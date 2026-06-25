"""
dag_transacciones.py
--------------------
DAG de Apache Airflow para pipeline de fraude
"""

from datetime import datetime, timedelta  # imports de tiempo y retries

from airflow import DAG  # clase principal del DAG
from airflow.operators.bash import BashOperator  # operador para comandos bash
from airflow.providers.postgres.operators.postgres import PostgresOperator  # operador SQL en postgres


# configuracion general del DAG
default_args = {
    "owner": "data_engineering",  # propietario del pipeline
    "depends_on_past": False,  # no depende de ejecuciones anteriores
    "email": ["fraude-alertas@banco.com"],  # correo de alertas
    "email_on_failure": True,  # notifica si falla
    "email_on_retry": False,  # no notifica en reintentos
    "retries": 2,  # numero de reintentos
    "retry_delay": timedelta(minutes=5),  # tiempo entre reintentos
    "execution_timeout": timedelta(minutes=30),  # timeout de tarea
}


# definicion del DAG principal
with DAG(
    dag_id="pipeline_fraude_diario",  # id del dag
    description="Pipeline ETL diario de fraude",  # descripcion
    schedule="30 23 * * *",  # ejecucion diaria 23:30
    start_date=datetime(2026, 1, 1),  # fecha inicio
    catchup=False,  # no ejecutar datos historicos
    default_args=default_args,  # argumentos generales
    tags=["fraude", "etl"],  # etiquetas del dag
) as dag:

    # tarea 1: validar existencia del archivo csv
    verificar_csv = BashOperator(
        task_id="verificar_archivo_csv",  # id de tarea
        bash_command="""
        FILE=data/transacciones_diarias.csv  # ruta del archivo

        if [ ! -f "$FILE" ]; then  # si no existe archivo
            echo "ERROR archivo no encontrado"  # mensaje error
            exit 1  # falla la tarea
        fi

        echo "archivo encontrado"  # confirma existencia
        """,
    )

    # tarea 2: ejecutar transformacion del pipeline
    transformacion_python = BashOperator(
        task_id="transformacion_python",  # id tarea
        bash_command="python src/pipeline.py",  # ejecuta ETL
    )

    # tarea 3: cargar datos a supabase
    carga_supabase = BashOperator(
        task_id="carga_supabase",  # id tarea
        bash_command="python src/cargar_supabase.py",  # carga postgres
    )

    # tarea 4: ejecutar consulta de anomalas en sql
    analisis_anomalias = PostgresOperator(
        task_id="analisis_anomalias_sql",  # id tarea
        postgres_conn_id="supabase_postgres",  # conexion airflow
        sql="sql/consulta_anomalias.sql",  # archivo sql
        autocommit=True,  # commit automatico
    )

    # orden de ejecucion del pipeline
    verificar_csv >> transformacion_python >> carga_supabase >> analisis_anomalias  # flujo secuencial