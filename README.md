# 📺 TV Monitor — Comparador Multicanal de Emisiones Televisivas

Aplicación profesional en **Python + Streamlit** para comparar archivos Excel de monitoreo televisivo entre múltiples canales. Detecta diferencias en acciones especiales, tandas publicitarias y horarios de programa con semaforización visual.

---

## 🚀 Características principales

- **Carga multiarchivo**: Soporta de 2 a 20 archivos Excel simultáneamente
- **Detección automática de canales** desde el nombre del archivo
- **Extracción inteligente del nombre del programa** (ignora horarios, EMS, duraciones)
- **Comparación multicanal** con semaforización (verde / amarillo / rojo)
- **3 pestañas especializadas**: Acciones Especiales, Tanda Publicitaria, Programa
- **Detalle en sidebar** al seleccionar una fila (Spot Id, Compañía, Marca, etc.)
- **Exclusión de autopromos** configurable por canal
- **Exportación** a Excel y CSV (resultados completos y solo diferencias)
- **Validaciones de consistencia** con alertas visuales
- **Optimizado** para archivos de +100,000 registros

---

## 📁 Estructura del proyecto

```
tv_monitor/
├── app.py                    # Punto de entrada principal de Streamlit
├── requirements.txt          # Dependencias del proyecto
├── README.md                 # Este archivo
├── .streamlit/
│   └── config.toml           # Configuración de Streamlit (opcional)
└── modules/
    ├── __init__.py
    ├── loader.py             # Carga y cache de archivos Excel
    ├── parser.py             # Extracción de nombres de programas
    ├── comparator.py         # Motor de comparación multicanal
    ├── validations.py        # Validaciones de consistencia
    ├── ui.py                 # Componentes de interfaz reutilizables
    └── exporter.py           # Exportación a Excel/CSV
```

---

## 📋 Columnas soportadas en los archivos Excel

| Columna        | Descripción                                  |
|----------------|----------------------------------------------|
| Programa       | Nombre del programa (con metadata de horario)|
| Spot Id        | Identificador único del spot                 |
| Inicio         | Hora de inicio del spot                      |
| Final          | Hora de fin del spot                         |
| Duración       | Duración del spot (HH:MM:SS)                 |
| Spot           | Nombre del spot                              |
| Tipo           | Tipo de spot                                 |
| Compañía       | Empresa anunciante                           |
| Marca          | Marca del producto                           |
| SubMarca       | Submarca                                     |
| Producto       | Producto específico                          |
| Tipo Bloque    | Categoría del bloque (Programa/Carrier/Break/Accion especial) |
| Posición       | Posición en el bloque                        |
| Fecha          | Fecha de emisión                             |
| Campaña        | Nombre de la campaña publicitaria            |
| Franja Horaria | Franja horaria del programa                  |
| Origen         | Origen del contenido                         |
| Nombre del Género | Género del programa                       |
| Testigo        | Número de testigo                            |
| Bloque         | Número de bloque                             |
| Seg. Truncados | Segundos truncados                           |
| Formato        | Formato del spot                             |

---

## 🛠️ Instalación local

### Prerequisitos
- Python 3.9 o superior
- pip actualizado

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/tv-monitor.git
cd tv-monitor

# 2. Crear entorno virtual (recomendado)
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Mac/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La aplicación abrirá automáticamente en `http://localhost:8501`

---

## ☁️ Despliegue en Streamlit Cloud

### Paso 1: Preparar el repositorio en GitHub

1. Crear un repositorio en GitHub (puede ser público o privado)
2. Subir todos los archivos del proyecto:

```bash
git init
git add .
git commit -m "Initial commit - TV Monitor v1.0"
git branch -M main
git remote add origin https://github.com/tu-usuario/tv-monitor.git
git push -u origin main
```

### Paso 2: Desplegar en Streamlit Cloud

1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. Iniciar sesión con tu cuenta de GitHub
3. Hacer clic en **"New app"**
4. Seleccionar:
   - **Repository**: `tu-usuario/tv-monitor`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Hacer clic en **"Deploy!"**

Streamlit Cloud instalará automáticamente las dependencias de `requirements.txt`.

### Configuración adicional (opcional)

Crear el archivo `.streamlit/config.toml` para personalizar el tema:

```toml
[theme]
primaryColor = "#1565c0"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8fafc"
textColor = "#1a202c"
font = "sans serif"

[server]
maxUploadSize = 200
```

---

## 📖 Guía de uso

### 1. Cargar archivos
- En el panel lateral, haz clic en **"Selecciona uno o más archivos Excel"**
- Carga todos los archivos de monitoreo (uno por canal)
- El nombre del canal se toma automáticamente del nombre del archivo

### 2. Seleccionar programa
- Usa el menú desplegable **"Seleccionar programa"**
- El sistema muestra todos los programas detectados en todos los canales
- Los nombres están limpios (sin horarios ni códigos EMS)

### 3. Configurar autopromos (opcional)
- Abre el panel **"Configuración de Autopromos"**
- Activa el checkbox del canal donde quieres excluir autopromos
- Los registros con `Producto = Autopromo` serán excluidos del análisis

### 4. Analizar las pestañas

#### ⚡ Acciones Especiales
- Muestra todos los spots de tipo `Accion especial`
- Columnas: ID, Inicio, Duración, Spot
- Semáforo: ✅ en todos | ⚠️ parcial | ❌ faltante
- **Clic en fila** → detalle completo en el panel lateral

#### 📢 Tanda Publicitaria
- Muestra spots tipo `Carrier` y `Break` (unificados)
- Columnas: ID, Inicio, Duración, Posición, Spot
- Mismo sistema de semaforización
- **Clic en fila** → detalle completo en el panel lateral

#### 🎬 Programa
- No muestra spots individuales
- Tabla: Canal | Inicio | Fin | Duración Total
- Gráfico de barras con duración por canal

### 5. Exportar resultados
- En cada pestaña hay un expander **"Exportar resultados"**
- Opciones: Excel completo, CSV completo, Solo diferencias

---

## 🔍 Lógica de extracción del nombre del programa

El sistema extrae el nombre limpio del programa eliminando:
- Horarios en formato `HH:MM:SS - HH:MM:SS`
- Bloques EMS `(EMS = XXXXXXXXXX - HH:MM:SS)`
- Cualquier texto posterior

**Ejemplo:**
```
Entrada:  FSI. MEXICO VS. SUDAFRICA SIMULCAST 12:30:01 - 15:09:05 (EMS = 1141933715 - 02:39:04)
Salida:   FSI. MEXICO VS. SUDAFRICA SIMULCAST
```

---

## 🚦 Sistema de semaforización

| Color  | Símbolo | Significado |
|--------|---------|-------------|
| 🟢 Verde  | ✅ En todos  | El spot existe en **todos** los canales |
| 🟡 Amarillo | ⚠️ Parcial | El spot existe en **algunos** canales |
| 🔴 Rojo  | ❌ Faltante  | El spot **falta** en uno o más canales |

---

## 🔧 Arquitectura técnica

```
Usuario
  │
  ▼
app.py (Streamlit UI)
  │
  ├── loader.py      → Lee Excel, cache con @st.cache_data, valida columnas
  ├── parser.py      → Regex para limpiar nombres de programa
  ├── comparator.py  → Comparación vectorizada con Pandas
  ├── validations.py → Alertas de inconsistencia
  ├── ui.py          → CSS, componentes, semaforización
  └── exporter.py    → Generación de Excel/CSV para descarga
```

### Optimizaciones de rendimiento
- `@st.cache_data` en la lectura de Excel (evita recargas)
- Operaciones vectorizadas de Pandas (sin loops Python)
- `dtype=str` en carga para evitar conversiones automáticas costosas
- Columna auxiliar `Tipo Bloque Norm` pre-computada

---

## 📝 Licencia

MIT License — libre para uso comercial y modificación.

---

## 🤝 Contribuciones

Los pull requests son bienvenidos. Para cambios mayores, abre primero un issue para discutir el cambio propuesto.

---

*Desarrollado con Python 3.9+, Streamlit, Pandas y OpenPyXL*
