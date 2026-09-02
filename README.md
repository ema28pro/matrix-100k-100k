# Laboratorio 1: Matriz de 100,000 x 100,000 en Disco Duro
**Asignatura:** Estructuras de Datos  
**Estudiante:** Emanuel Lopez Franco   

---

## 1. Descripción del Problema y Solución Desarrollada

El objetivo de este laboratorio consiste en crear, almacenar en almacenamiento secundario (disco duro) y consultar de forma eficiente una matriz de **100,000 x 100,000** elementos (10 mil millones de celdas en total).

### Arquitectura de la Solución (Cabecera Estándar HDF5 + Enteros 2-Bits + Separador `11111111`):
Para cumplir con los requerimientos académicos del laboratorio:
1. **Cabecera Estándar HDF5 (64 bytes):**
   - **Firma Mágica Canónica (8 bytes):** `\x89HDF\r\n\x1a\n` (`0x89, 'H', 'D', 'F', '\r', '\n', 0x1A, '\n'`), estándar internacional de HDF5 (*Hierarchical Data Format 5*) para almacenamiento científico y matricial.
   - **Metadatos de Estructura (8 bytes):** Versión del superbloque (`2`), bits por celda (`2`), bandera de separador activo (`1`), valor centinela (`0xFF`), flags de alineamiento.
   - **Dimensiones y Registros en 64 bits (32 bytes):** `uint64_t FILAS` (100,000), `uint64_t COLUMNAS` (100,000), `uint64_t BYTES_DATOS_FILA` (25,000), `uint64_t ANCHO_TOTAL_FILA` (25,001).
   - **Alineamiento de Caché (16 bytes):** Relleno reservado para totalizar exactamente **64 bytes** (alineado con el tamaño de línea de caché L1/L2 del CPU).
2. **Celdas en Enteros de 2 Bits:** Cada celda almacena valores en el rango **[0, 2]** usando 2 bits (`00`=0, `01`=1, `10`=2). Esto permite empaquetar **4 celdas por cada byte**, ocupando $100,000 / 4 = \mathbf{25,000\text{ bytes de datos por fila}}$.
3. **Separador de Fin de Fila:** Al final de cada fila se escribe **un byte entero centinela con valor `11111111` (`0xFF` = 255)** como delimitador de fila.
4. **Ancho Físico por Fila:** 25,000 bytes de datos + 1 byte de separador = **25,001 bytes por fila**.
5. **Tamaño Total en Disco:** 64 bytes cabecera HDF5 + ($100,000 \times 25,001$) = **2,500,100,064 bytes (~2.33 GiB / 2.50 GB)**.

> [!NOTE]
> **Observación Teórica sobre Registros de Longitud Fija:**  
> Según los principios de diseño de sistemas de archivos y motores de bases de datos para registros de tamaño fijo (*Fixed-Length Records*), el desplazamiento hacia cualquier fila es puramente algebraico en tiempo $O(1)$, por lo cual en entornos de producción los separadores de fila son omitibles para ahorrar almacenamiento. No obstante, para satisfacer el diseño del laboratorio con delimitadores explícitos que garanticen la separación de filas sin colisión con los datos, se implementa el byte centinela `11111111` (`0xFF`).  
> Consulta la [Bitácora de Solución](docs/bitacora_solucion.md) para ver la evolución completa de las variantes previas exploradas.

---

## 2. Resolución de los 3 Desafíos de Ingeniería

| Desafío | Problema Común | Solución Implementada |
| :--- | :--- | :--- |
| **1. Consumo Excesivo de RAM** | Intentar alojar la matriz entera en memoria RAM (`int` = **40 GB**, `byte` = **10 GB**) causaría un colapso inmediato (*Out of Memory / Crash*). | **La matriz NUNCA se crea completa en RAM y TAMPOCO se carga completa en RAM al consultarse:**<br>• **Al crear:** Se procesa y vuelca progresivamente por pequeños bloques (~12.5 MB) directamente a disco (*Out-of-Core Processing*).<br>• **Al consultar:** Se lee bajo demanda (*Demand Paging*) en tiempo $O(1)$ con `seekg`, trayendo únicamente el byte o fragmento pedido sin cargar el archivo a memoria.<br>• **Compactación:** Empaquetamiento de celdas a nivel de bits (2 bits = 4 celdas/byte, 1 bit = 8 celdas/byte). |
| **2. Escritura Lenta a Disco** | Escribir celda por celda o byte por byte genera millones de llamadas al Kernel (*syscalls*), tardando horas. | **Buffered Chunked I/O:** Se transfieren bloques completos de **12.5 MB** por cada operación de escritura `write()`, aprovechando al máximo el ancho de banda secuencial del almacenamiento. |
| **3. Optimización en la Manipulación, Creación, Almacenamiento y Lectura de Datos** | Sin optimización, generar tardaría horas, el archivo pesaría decenas de gigabytes, y consultar una celda requeriría escanear linealmente en $O(N)$. | • **Creación:** Generación progresiva en bloques contiguos de ~12.5 MB (500 a 1,000 filas) usando buffers estáticos en BSS / memoria contigua, evitando miles de *mallocs*.<br>• **Almacenamiento:** Formato binario ultracompacto (2 bits/celda = 4 celdas/byte, o 1 bit/celda) con cabecera autodescriptiva alineada a 64 bytes. Reduce el almacenamiento de 40 GB a solo ~2.33 GiB.<br>• **Manipulación:** Mapeo 2D $\to$ 1D puro y extracción de submatrices/ventanas arbitrarias o exportación a mapas de bits (BMP con paletas RGB/CMY) sin tocar el resto de la matriz.<br>• **Lectura:** Acceso aleatorio $O(1)$ instantáneo (*Demand Paging*) con cálculo de offset directo y `seekg()`, sin escaneos secuenciales. |

---

## 3. Estructura del Repositorio

```text
lab 1/
├── README.md                                         # Documentación principal del proyecto
├── requirements.txt                                  # Dependencias de Python (numpy)
│
├── docs/                                             # Documentación técnica y evolución
│   ├── bitacora_solucion.md                          # Bitácora de evolución de ideas y análisis técnico
│   ├── indicaciones.md                               # Enunciado original
│   └── segunda parte.md                              # Criterios de entrega
│
├── solucion_python/                                  # Implementación Actual y Herramientas
│   ├── generar_matriz.py                             # Generador oficial con Cabecera Estándar HDF5 (2-bits + separador 0xFF)
│   ├── generar_matriz_pequena.py                     # Generador de matriz pequeña de control (con filas de '2's para verificación)
│   ├── verificar_matriz.py                           # Verificador universal (detecta cabecera HDF5 o clásica de 16B)
│   ├── exportar_bmp.py                               # Renderizador BMP universal (paletas RGB, CMY y Grises)
│   ├── inspeccionar_cabecera.py                      # Visor forense de cabecera y bytes crudos (.hex() y ASCII)
│   ├── visor_procedural_txt.py                       # Visor procedural y proyector de chunks en tiempo real para Notepad
│   ├── variante1_sin_header_sin_separador.py         # Variante 1: Flujo continuo sin cabecera ni separadores
│   ├── variante2_separador_cero.py                   # Variante 2: Matriz de 1s con separador bit '0'
│   └── variante3_int2bits_separador_byte.py          # Variante 3: Prototipo experimental de enteros 2-bits con 0xFF
│
├── solucion_vieja_cpp/                               # Implementación Previa en C++ (Versión Anterior de Referencia)
│   ├── crear_matriz.cpp                              # Generador C++ con Paging BSS y 1 bit por celda (Cabecera clásica de 16B)
│   ├── mostrar_matriz.cpp                            # Menú interactivo O(1) con seekg para matriz de 1 bit
│   └── mat.cpp                                       # Script monolítico de prueba rápida
│
└── matriz_100k.bin                                   # Archivo binario generado (~2.33 GiB, en .gitignore)
```

---

## 4. Formato del Archivo Binario (`matriz_100k.bin`)

```text
+-----------------------+--------------------------+-----------------------------------------------------------------+
| Bytes 0 a 7           | Bytes 8 a 63             | Bytes 64 a 2,500,100,063                                        |
| Firma Mágica HDF5     | Metadatos Estructurados  | Datos de la Matriz + Separadores de Fila                        |
| "\x89HDF\r\n\x1a\n"   | Filas, Cols, Anchos      | 100,000 filas * (25,000 B datos + 1 B separador 0xFF)           |
+-----------------------+--------------------------+-----------------------------------------------------------------+
Total exacto en disco = 64 bytes cabecera HDF5 + 2,500,100,000 bytes = 2,500,100,064 bytes (~2.33 GiB / 2.50 GB).
```

### Algoritmo de Indexación Directa $O(1)$:
Para consultar la celda `(fila, columna)`:
1. **Ancho total por fila:** `25,000 (datos) + 1 (separador 0xFF) = 25,001 bytes`
2. **Offset en disco:** `64 + (fila * 25001) + (columna // 4)`
3. **Posición dentro del byte:** `columna % 4`
4. **Desplazamiento (Shift):** `(3 - posición) * 2`
5. **Valor de la celda:** `(byte_leido >> Shift) & 3`

---

## 5. Guía de Ejecución

### Opción A: Solución Principal en Python (Estándar HDF5 + 2-Bits + 0xFF)

```powershell
# 1. Instalar dependencias requeridas:
pip install -r requirements.txt

# 2. Generar la matriz binaria en disco (100,000 x 100,000):
python solucion_python/generar_matriz.py

# (Opcional) Generar una matriz pequeña de prueba/control (ej. 10 filas x 32 cols con filas de '2's):
python solucion_python/generar_matriz_pequena.py 10 32

# 3. Verificar integridad, dimensiones y separadores 0xFF:
python solucion_python/verificar_matriz.py

# 4. Exportar muestra visual a BMP con opción de color (RGB o CMY):
python solucion_python/exportar_bmp.py rgb   # Paleta RGB (0=Rojo, 1=Verde, 2=Azul)
python solucion_python/exportar_bmp.py cmy   # Paleta CMY (0=Cyan, 1=Magenta, 2=Amarillo)

# 5. Navegar chunks de números puros en el Bloc de Notas:
python solucion_python/visor_procedural_txt.py
```

---

### Opción B: Solución Anterior en C++ (`solucion_vieja_cpp`)

```powershell
# 1. Compilar los ejecutables de C++:
g++ -O2 solucion_vieja_cpp/crear_matriz.cpp -o solucion_vieja_cpp/crear_matriz.exe
g++ -O2 solucion_vieja_cpp/mostrar_matriz.cpp -o solucion_vieja_cpp/mostrar_matriz.exe

# 2. Generar la matriz de 1 bit:
.\solucion_vieja_cpp\crear_matriz.exe

# 3. Abrir el menú interactivo para consultar celdas:
.\solucion_vieja_cpp\mostrar_matriz.exe
```

---

## 6. Métodos de Verificación del Contenido del Archivo

Para garantizar que el archivo binario generado es íntegro, cumple con las dimensiones y no contiene corrupción, el repositorio provee **4 métodos de verificación independientes**:

### Método 1: Verificador Automatizado de Integridad ([`verificar_matriz.py`](solucion_python/verificar_matriz.py))
Ejecuta una inspección estructural completa del archivo:
```powershell
python solucion_python/verificar_matriz.py
```
- **Detección Universal:** Identifica automáticamente si el archivo tiene cabecera HDF5 (64B) o clásica (16B).
- **Validación Físico-Matemática:** Compara el tamaño real en bytes en disco contra la fórmula teórica exacta ($64 + 100,000 \times 25,001$ o $16 + 100,000 \times 12,500$).
- **Chequeo de Delimitadores Centinela:** Inspecciona los bytes separadores de fila al final de múltiples filas para certificar que contengan `0xFF` (`11111111`).
- **Análisis Estadístico de Celdas:** Lee una muestra amplia (500 filas = 50 millones de celdas) y reporta la frecuencia relativa de cada valor para verificar la distribución uniforme (~33.3% para cada valor 0, 1 y 2).

### Método 2: Visor Interactivo por Consola ([`mostrar_matriz.cpp`](solucion_vieja_cpp/mostrar_matriz.cpp))
Permite consultar cualquier punto de la matriz en tiempo real:
```powershell
.\solucion_vieja_cpp\mostrar_matriz.exe
```
- **Consulta por Coordenada:** Introduce `fila` y `columna` arbitrarias para leer el valor exacto de la celda en $O(1)$.
- **Segmentos de Fila:** Permite inspeccionar un rango contiguo de columnas dentro de cualquier fila.
- **Ventanas 2D:** Extrae e imprime una submatriz en consola (ej. 5 filas x 10 columnas) desde cualquier origen $(i, j)$.

### Método 3: Verificación Visual Gráfica en Imagen ([`exportar_bmp.py`](solucion_python/exportar_bmp.py))
Renderiza una ventana de $1,000 \times 1,000$ celdas directamente a un archivo de imagen `muestra_matriz.bmp` para inspección humana:
```powershell
# Paleta RGB / RVG (0 = Rojo, 1 = Verde, 2 = Azul)
python solucion_python/exportar_bmp.py rgb

# Paleta CMY (0 = Cyan, 1 = Magenta, 2 = Amarillo)
python solucion_python/exportar_bmp.py cmy
```
- Permite abrir la imagen resultante en cualquier visor (Paint, Fotos de Windows) para comprobar visualmente la distribución estocástica (*ruido homogéneo*) sin sesgos espaciales.

### Método 4: Inspección Física Hexadecimal y Forense en Terminal
Permite verificar los bytes crudos, la firma mágica y la cabecera directamente sobre el archivo en disco:

```powershell
# A. Usando el inspector en Python (muestra .hex(), bytes espaciados y volcado hexdump):
python solucion_python/inspeccionar_cabecera.py matriz_100k.bin 64

# B. En Windows PowerShell: Inspeccionar los primeros 64 bytes nativamente con Format-Hex:
Get-Content -Path .\matriz_100k.bin -Encoding Byte -TotalCount 64 | Format-Hex

# C. En Linux / Git Bash: Inspeccionar la cabecera en hexadecimal y caracteres ASCII:
hexdump -C -n 64 matriz_100k.bin
```

### Método 5: Proyección Procedural de Chunks en Bloc de Notas ([`visor_procedural_txt.py`](solucion_python/visor_procedural_txt.py))
Genera y proyecta fragmentos/ventanas 2D de la matriz formateadas en texto plano (`vista_matriz.txt`), abriendo automáticamente el Bloc de Notas (*Notepad*) y actualizándose en tiempo real:
```powershell
# Iniciar visor en modo stream (actualiza la ventana en vivo cada segundo):
python solucion_python/visor_procedural_txt.py stream 20 1.0

# O seguir el streaming en vivo desde PowerShell:
Get-Content .\vista_matriz.txt -Wait
```
- Muestra una regla de columnas, coordenadas absolutas de la matriz, leyenda de celdas (`.` = 0, `1` = 1, `#` = 2) y telemetría del chunk en tiempo de ejecución.
