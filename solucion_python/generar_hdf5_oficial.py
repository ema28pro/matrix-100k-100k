# Laboratorio 1: Generador Matriz con Formato y Cabecera Oficial HDF5 (.h5 / .bin)
# Utiliza la MISMA logica que generar_matriz.py:
#   - Celdas de 2 bits (valores posibles: 0, 1, 2)
#   - Empaquetamiento de 4 celdas por byte (COLS // 4)
#   - 1 byte separador centinela 0xFF (11111111) al final de cada fila
#   - Generacion progresiva en disco por bloques/chunks (Demand Paging)
#   - Contenedor y Cabecera 100% estandar oficial HDF5 (compatible con myHDF5 y HDFView)

import os
import sys
import time
import h5py
import numpy as np

ROWS = 100_000
COLS = 100_000
CHUNK = 1_000
ARCHIVO_DEFECTO = "matriz_100k.h5"

def generar_matriz_hdf5(filas=None, cols=None, archivo_salida=None):
    if filas is None:
        filas = ROWS
    if cols is None:
        cols = COLS
    if archivo_salida is None:
        archivo_salida = ARCHIVO_DEFECTO

    # Ajuste para empaquetamiento exacto de 2 bits (4 celdas por byte)
    if cols % 4 != 0:
        cols = ((cols // 4) + 1) * 4

    bytes_datos_fila = cols // 4
    ancho_fila = bytes_datos_fila + 1  # Datos + 1 byte separador 0xFF

    print("=================================================================")
    print(" GENERADOR MATRIZ CON CABECERA ESTANDAR OFICIAL HDF5")
    print(" (2-Bits por celda + Separador 0xFF + Header HDF5 oficial)")
    print("=================================================================")
    print(f"Destino:                 {os.path.abspath(archivo_salida)}")
    print(f"Dimensiones de Matriz:   {filas:,} filas x {cols:,} columnas")
    print(f"Codificacion:            2 bits por celda (valores: 0, 1, 2)")
    print(f"Empaquetamiento:         4 celdas por byte ({bytes_datos_fila:,} bytes de datos por fila)")
    print(f"Separador de Fin Fila:   1 byte centinela 0xFF (11111111 = 255)")
    print(f"Ancho total por fila:    {ancho_fila:,} bytes en disco")
    print(f"Tamano de lote (Chunk):  {CHUNK:,} filas por escritura a disco\n")

    inicio = time.time()
    rng = np.random.default_rng()

    # 1. Crear el contenedor con cabecera estandar HDF5 oficial
    with h5py.File(archivo_salida, "w") as f:
        # Metadatos del Laboratorio (legibles en myHDF5)
        f.attrs["estandar"] = "HDF5 Oficial"
        f.attrs["filas"] = filas
        f.attrs["columnas"] = cols
        f.attrs["bits_por_celda"] = 2
        f.attrs["separador_fin_fila"] = "0xFF (11111111 = 255)"
        f.attrs["ancho_fila_bytes"] = ancho_fila
        f.attrs["descripcion"] = "Matriz de 100k x 100k con celdas de 2 bits y delimitador centinela 0xFF"

        # Dataset que almacena exactamente las filas binarias (25,000 B datos + 1 B separador 0xFF)
        chunk_filas = min(CHUNK, filas)
        dset = f.create_dataset(
            "matriz_binaria",
            shape=(filas, ancho_fila),
            dtype=np.uint8,
            chunks=(chunk_filas, ancho_fila),
            compression="gzip",
            compression_opts=1
        )

        # 2. Generacion progresiva en bloques (sin cargar la matriz completa en RAM)
        for i in range(0, filas, CHUNK):
            n_filas = min(CHUNK, filas - i)
            bloque = rng.integers(0, 3, size=(n_filas, cols), dtype=np.uint8)

            # Empaquetamos 4 celdas de 2 bits por cada byte
            v = bloque.reshape(n_filas, -1, 4)
            datos_bytes = (v[:, :, 0] << 6) | (v[:, :, 1] << 4) | (v[:, :, 2] << 2) | v[:, :, 3]

            # Columna separadora 0xFF (11111111)
            sep_col = np.full((n_filas, 1), 0xFF, dtype=np.uint8)

            # Fila completa con su byte separador al final
            fila_completa = np.hstack([datos_bytes, sep_col])

            # Volcar el chunk directamente a disco en el contenedor HDF5
            dset[i:i + n_filas, :] = fila_completa

            if (i // CHUNK) % 10 == 0 or (i + n_filas) == filas:
                progreso = ((i + n_filas) / filas) * 100
                print(f"  -> Lote guardado: filas {i + n_filas:,} / {filas:,} ({progreso:.1f}%)")

    duracion = time.time() - inicio
    tamano_disco = os.path.getsize(archivo_salida)
    print(f"\n[OK] Generacion exitosa en {duracion:.2f} segundos.")
    print(f"Tamano final en disco: {tamano_disco:,} bytes (~{tamano_disco / 1e6:.2f} MB)")
    print(f"Archivo listo: {os.path.abspath(archivo_salida)}")
    print("Ya puedes arrastrar este archivo a https://myhdf5.hdfgroup.org/ sin errores!")

if __name__ == "__main__":
    # Permite personalizar filas y columnas por linea de comandos:
    # Ejemplo: python generar_hdf5_oficial.py 100 100000 matriz_100k.h5
    n_filas = int(sys.argv[1]) if len(sys.argv) > 1 else ROWS
    n_cols = int(sys.argv[2]) if len(sys.argv) > 2 else COLS
    salida = sys.argv[3] if len(sys.argv) > 3 else ARCHIVO_DEFECTO
    generar_matriz_hdf5(n_filas, n_cols, salida)
