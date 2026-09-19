# Guía de Verificación e Inspección del Archivo Binario (`verificacion.md`)

Este documento detalla exhaustivamente los **6 métodos independientes de verificación** disponibles para certificar la integridad estructural, matemática, visual y de bajo nivel de la matriz binaria generada (`matriz_100k.bin`).


## Resumen de Métodos Disponibles

| Método | Herramienta / Script | Tipo de Validación | Nivel de Inspección |
| :--- | :--- | :--- | :--- |
| **1. Automatizado** | `solucion_python/verificar_matriz.py` | Estructural, Fórmulas y Muestra Estadística | Lógico y Matemático |
| **2. Consola C++** | `solucion_vieja_cpp/mostrar_matriz.exe` | Coordenadas $(i, j)$ y Submatrices 2D | Acceso Directo $O(1)$ |
| **3. Gráfico BMP** | `solucion_python/exportar_bmp.py` | Imagen sin compresión (RGB / CMY) | Visual Humano |
| **4. Hexadecimal** | `inspeccionar_cabecera.py` / `Format-Hex` / `hexdump` | Volcado crudo de bytes y firma mágica | Forense de Bajo Nivel |
| **5. Procedural** | `solucion_python/visor_procedural_txt.py` | Proyección dinámica en Bloc de Notas | Mapeo y Paginación |
| **6. Web Estándar** | [HexEd.it](https://hexed.it/) y [myHDF5](https://myhdf5.hdfgroup.org/) | Visor de superbloques y Datasets HDF5 | Estándar Internacional |

---

## Método 1: Verificador Automatizado de Integridad

El script principal de validación lógica comprueba exhaustivamente la consistencia física del archivo sin necesidad de cargarlo a memoria RAM:

```powershell
python solucion_python/verificar_matriz.py
```

### Comprobaciones Realizadas:
1. **Detección Universal de Cabecera:**
   - Lee los primeros 8 bytes y comprueba si coincide con la firma canónica HDF5 (`\x89HDF\r\n\x1a\n`) de 64 bytes o la cabecera clásica de 16 bytes.
2. **Validación Físico-Matemática de Tamaño:**
   - Compara el tamaño real en bytes del archivo en el sistema de archivos contra el modelo matemático:
     $$\text{Tamaño Teórico} = 64\text{ B (cabecera)} + 100,000 \times (25,000\text{ B datos} + 1\text{ B centinela}) = 2,500,100,064\text{ bytes}$$
3. **Chequeo de Delimitadores Centinela:**
   - Realiza saltos algebraicos con `seek()` al byte 25,000 de múltiples filas aleatorias y verifica que el byte delimitador sea exactamente `0xFF` (`11111111` en binario = 255).
4. **Análisis Estadístico de Distribución Uniforme:**
   - Inspecciona una muestra de 500 filas completas (50,000,000 de celdas), calculando la frecuencia relativa de los valores generados para confirmar una distribución estocástica equilibrada (~33.3% para 0, 1 y 2).

---

## Método 2: Visor Interactivo por Consola (C++)

Permite interactuar directamente con el archivo binario mediante un menú en consola:

```powershell
# Compilar si aún no se ha hecho:
g++ -O2 solucion_vieja_cpp/mostrar_matriz.cpp -o solucion_vieja_cpp/mostrar_matriz.exe

# Ejecutar visor:
.\solucion_vieja_cpp\mostrar_matriz.exe
```

### Funcionalidades:
* **Consulta puntual $O(1)$:** Ingresa cualquier par `(fila, columna)` y obtiene el valor instantáneamente mediante un salto `seekg`.
* **Rango de columnas:** Imprime en una sola línea una secuencia continua de celdas de una fila elegida.
* **Ventana 2D:** Extrae una submatriz cuadrada o rectangular (ej. $10 \times 10$) centrada en cualquier coordenada.

---

## Método 3: Verificación Visual Gráfica en Imagen (BMP)

Exporta una ventana contigua de $1,000 \times 1,000$ celdas (1 millón de elementos) a una imagen Bitmap (`muestra_matriz.bmp`):

```powershell
# Paleta RGB (0 = Rojo, 1 = Verde, 2 = Azul)
python solucion_python/exportar_bmp.py rgb

# Paleta CMY (0 = Cyan, 1 = Magenta, 2 = Amarillo)
python solucion_python/exportar_bmp.py cmy
```

### Interpretación:
* Al abrir la imagen en cualquier visor de imágenes estándar (Fotos de Windows, Paint), se aprecia un patrón homogéneo de ruido estocástico.
* La ausencia de líneas o franjas atípicas certifica que no existen desalineamientos ni corrimientos de bits en las filas.

---

## Método 4: Inspección Física Hexadecimal y Forense en Terminal

Permite auditar los bytes crudos y la firma de la cabecera directamente desde la terminal del sistema operativo:

### A. Inspector en Python
Muestra el desglose de los 64 bytes de cabecera con offsets, valores hexadecimales y representación ASCII:
```powershell
python solucion_python/inspeccionar_cabecera.py matriz_100k.bin 64
```

### B. En Windows PowerShell nativo
```powershell
Get-Content -Path .\matriz_100k.bin -Encoding Byte -TotalCount 64 | Format-Hex
```

### C. En Linux / Git Bash / macOS
```bash
hexdump -C -n 64 matriz_100k.bin
```

#### Salida Esperada:
Los primeros 8 bytes deben corresponder a la firma canónica:
```text
00000000: 89 48 44 46 0D 0A 1A 0A  .HDF....
```

---

## Método 5: Proyección Procedural de Chunks en Bloc de Notas

Proyecta ventanas de texto plano con los valores numéricos decodificados (`.` = 0, `1` = 1, `#` = 2) hacia un archivo temporal `vista_matriz.txt`, abriendo automáticamente el Bloc de Notas (*Notepad*):

```powershell
# Iniciar navegador interactivo de chunks:
python solucion_python/visor_procedural_txt.py
```

* Permite navegar chunks mediante comandos de consola (`w`, `a`, `s`, `d`), actualizando en tiempo real la ventana visible en el Bloc de Notas.
* Alternativamente, en otra terminal de PowerShell se puede seguir la transmisión en vivo:
  ```powershell
  Get-Content .\vista_matriz.txt -Wait
  ```

---

## Método 6: Inspección y Visualización en Línea (Web)

### 1. [HexEd.it](https://hexed.it/)
* Editor hexadecimal web que funciona en el navegador sin subir el archivo entero a la nube.
* Arrastra `matriz_100k.bin` para auditar la firma `\x89HDF\r\n\x1a\n` y los patrones de bytes `0xFF` al final de las filas.

### 2. [myHDF5 (The HDF Group)](https://myhdf5.hdfgroup.org/)
* Visor web oficial del consorcio creador de HDF5.
* Para generar una muestra con el formato canónico `.h5` compatible:
  ```powershell
  python solucion_python/generar_hdf5_oficial.py 100 1000
  ```
* Sube `matriz_oficial.h5` a **myHDF5** para explorar interactivamente la estructura del Dataset, atributos y paginación en la nube.
