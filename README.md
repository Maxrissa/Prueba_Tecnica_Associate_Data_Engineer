#  Pipeline de Detección de Anomalías de Fraude

## Descripción

Este proyecto implementa un pipeline ETL para procesar un archivo diario de transacciones de tarjetas de crédito.

El objetivo es limpiar la información recibida, aplicar las reglas de negocio proporcionadas, almacenar los datos en una base de datos PostgreSQL mediante Supabase y realizar una consulta SQL para detectar posibles anomalías de gasto.

---

# Fase 1 – Diseño del flujo

## Justificación de las reglas de calidad

Antes de realizar cualquier análisis es importante asegurarnos que la información tenga una buena calidad. Si los datos contienen errores o inconsistencias, los resultados obtenidos también serán incorrectos.

Las reglas implementadas cumplen ese propósito:

### Eliminación de registros duplicados

Se eliminan las transacciones duplicadas utilizando `id_transaccion` como identificador único. Esto evita contar una misma operación más de una vez.

### Tratamiento de valores nulos

Cuando una transacción fue rechazada y el monto aparece vacío, se reemplaza por **0.0**. De esta manera se evita trabajar con valores nulos y se representa correctamente que la transacción no generó un cargo.

### Clasificación de montos inusuales

Se crea la columna **es_monto_inusual**, la cual toma el valor **True** únicamente cuando:

- el monto es mayor a **1500 USD**
- el tipo de comercio es **internacional**

En cualquier otro caso el valor es **False**.

Esta columna facilita futuros análisis sin necesidad de volver a calcular la condición.

### Análisis únicamente sobre transacciones aprobadas

Para identificar anomalías de gasto únicamente se consideran las transacciones con estado **aprobada**.

Las transacciones pendientes o rechazadas no representan gastos reales y por lo tanto no deben formar parte del análisis.

---

# Arquitectura del pipeline

```text
                 transacciones_diarias.csv
                           │
                           ▼
                Extracción (Python + Pandas)
                           │
                           ▼
                  Transformación de datos
          ┌──────────────────────────────────┐
          │ • Eliminar duplicados            │
          │ • Corregir valores nulos         │
          │ • Crear es_monto_inusual         │
          └──────────────────────────────────┘
                           │
                           ▼
             Carga en Supabase (PostgreSQL)
                           │
                           ▼
        Consulta SQL (CTEs + Window Functions)
                           │
                           ▼
          Detección de anomalías de gasto
```

## Tecnologías utilizadas

- Python
- Pandas
- Supabase
- PostgreSQL
- SQL

---

# Estructura del proyecto

```text
Prueba_Tecnica_Associate_Data_Engineer/

├── data/
│   └── transacciones_diarias.csv
│
├── src/
│   ├── pipeline.py
│   └── cargar_supabase.py
│
├── sql/
│   ├── schema.sql
│   └── consulta_anomalias.sql
│
├── airflow/
│   └── dag_transacciones.py
│
├── images/
│   └── consulta_sql.png
│
├── requirements.txt
│
└── README.md
```

---

# Ejecución del proyecto

## 1. Instalamos las dependencias

```bash
pip install -r requirements.txt
```

## 2. Configuramos Supabase

1. Creamos un proyecto en Supabase.
2. Obtenemos las credenciales de conexión.
3. Creamos el archivo `.env` con las variables necesarias.

## 3. Creamos la tabla

Desde el **SQL Editor** de Supabase ejecutamos el contenido del archivo:

```text
sql/schema.sql
```

## 4. Ejecutamos el pipeline

```bash
python pipeline.py
```

El pipeline realiza las siguientes actividades:

- Lee el archivo CSV.
- Elimina registros duplicados.
- Corrige valores nulos.
- Genera la columna `es_monto_inusual`.
- Carga los datos procesados en Supabase.

## 5. Ejecutamos la consulta SQL

Abrimos el **SQL Editor** de Supabase y ejecutamos:

```text
sql/consulta_anomalias.sql
```

La consulta utiliza **CTEs** y la función **LAG()** para comparar cada transacción aprobada con la inmediatamente anterior del mismo cliente e identificar aquellas cuyo monto sea al menos cinco veces mayor.

---

# Orquestación con Apache Airflow

El archivo `dag_transacciones.py` contiene la propuesta de automatización del pipeline.

La ejecución está programada para todos los días a las **11:30 PM**.

Flujo de ejecución:

```text
Transformación
      │
      ▼
Carga a Supabase
      │
      ▼
Consulta SQL
```

Cada tarea depende de que la anterior finalice correctamente.

---

# Evidencia

La carpeta `images/` contiene la captura de pantalla de la ejecución de la consulta SQL en Supabase y los resultados obtenidos.

---
