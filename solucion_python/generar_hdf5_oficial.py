# Laboratorio 1: Generador Matriz con Formato y Cabecera Oficial HDF5 (.bin / .h5)
# Compatible al 100% con visores web oficiales como myHDF5 (https://myhdf5.hdfgroup.org/)
# Incluye dos Datasets:
#   1. 'matriz' -> Dimensiones completas (ROWS x COLS) con valores reales directos (0, 1, 2)
#   2. 'matriz_empaquetada_2bits' -> Formato fisico en bytes (ROWS x 25,001) con separador 0xFF

import os
import sys
import time
import h5py
import numpy as np

ROWS = 100
COLS = 100_000
CHUNK = 1_000
ARCHIVO_DEFECTO = "matriz_100k.bin"

def generar_matriz_hdf5(filas=None, cols=None, archivo_salida=None):
    if filas is None:
        filas = ROWS
    if cols is None:
        cols = COLS
    if archivo_salida is None:
        archivo_salida = ARCHIVO_DEFECTO

    # Ajuste para que las columnas sean multiplo de 4 para empaquetado de 2 bits
    if cols % 4 != 0:
        cols = ((cols // 4) + 1) * 4

    bytes_datos_fila = cols // 4
    ancho_fila = bytes_datos_fila + 1  # 25,000 B datos + 1 B separador 0xFF

    print("=================================================================")
    print(" GENERADOR MATRIZ OFICIAL HDF5 (100,000 Columnas Nativas + 2-Bits)")
    print("=================================================================")
    print(f"Destino:                 {os.path.abspath(archivo_salida)}")
    print(f"Dimensiones Reales:      {filas:,} filas x {cols:,} columnas")
    print(f"Valores en celdas:       0, 1 y 2 (tipo uint8)")
    print(f"Dataset 1 ('matriz'):    {filas:,} x {cols:,} celdas (visualizable en myHDF5)")
    print(f"Dataset 2 ('empaquetado'):{filas:,} x {ancho_fila:,} bytes (2-bits + separador 0xFF)")
    print(f"Tamano de lote (Chunk):  {CHUNK:,} filas por escritura\n")

    inicio = time.time()
    rng = np.random.default_rng(42)

    # 1. Crear el contenedor con cabecera estandar HDF5 oficial
    with h5py.File(archivo_salida, "w") as f:
        # Atributos de metadatos de nivel superior
        f.attrs["estandar"] = "HDF5 Oficial (NASA / The HDF Group)"
        f.attrs["filas"] = filas
        f.attrs["columnas"] = cols
        f.attrs["valores_permitidos"] = "0, 1, 2"
        f.attrs["bits_por_celda"] = 2
        f.attrs["separador_fin_fila"] = "0xFF (11111111 = 255)"
        f.attrs["ancho_empaquetado_bytes"] = ancho_fila
        f.attrs["descripcion"] = "Matriz 100k x 100k con celdas de 2 bits en almacenamiento secundario"

        chunk_filas = min(CHUNK, filas)
        chunk_cols_dset = min(1000, cols)

        # DATASET 1: La matriz con sus columnas completas para que el sitio web muestre las 100,000 columnas y 0, 1, 2
        dset_visual = f.create_dataset(
            "matriz",
            shape=(filas, cols),
            dtype=np.uint8,
            chunks=(chunk_filas, chunk_cols_dset),
            compression="gzip",
            compression_opts=1
        )

        # DATASET 2: La representacion fisica empaquetada a 2 bits con el byte separador 0xFF al final
        dset_empaquetado = f.create_dataset(
            "matriz_empaquetada_2bits_0xFF",
            shape=(filas, ancho_fila),
            dtype=np.uint8,
            chunks=(chunk_filas, ancho_fila),
            compression="gzip",
            compression_opts=1
        )

        # 2. Generacion progresiva en bloques (Demand Paging sin saturar RAM)
        for i in range(0, filas, CHUNK):
            n_filas = min(CHUNK, filas - i)
            # Generamos celdas con valores 0, 1, 2
            bloque = rng.integers(0, 3, size=(n_filas, cols), dtype=np.uint8)

            # Volcamos al Dataset 1 (Matriz de 100,000 columnas directas)
            dset_visual[i:i + n_filas, :] = bloque

            # Empaquetamos a 2 bits (4 celdas por byte) para el Dataset 2
            v = bloque.reshape(n_filas, -1, 4)
            datos_bytes = (v[:, :, 0] << 6) | (v[:, :, 1] << 4) | (v[:, :, 2] << 2) | v[:, :, 3]
            sep_col = np.full((n_filas, 1), 0xFF, dtype=np.uint8)
            fila_empaquetada = np.hstack([datos_bytes, sep_col])

            # Volcamos al Dataset 2
            dset_empaquetado[i:i + n_filas, :] = fila_empaquetada

            progreso = ((i + n_filas) / filas) * 100
            print(f"  -> Filas {i + n_filas:,} / {filas:,} guardadas ({progreso:.1f}%)")

    duracion = time.time() - inicio
    tamano_disco = os.path.getsize(archivo_salida)
    print(f"\n[OK] Generacion exitosa en {duracion:.2f} segundos.")
    print(f"Tamano en disco: {tamano_disco:,} bytes (~{tamano_disco / 1e6:.2f} MB)")
    print(f"Archivo listo: {os.path.abspath(archivo_salida)}")
    print("Ya puedes arrastrarlo a https://myhdf5.hdfgroup.org/ !")

if __name__ == "__main__":
    n_filas = int(sys.argv[1]) if len(sys.argv) > 1 else ROWS
    n_cols = int(sys.argv[2]) if len(sys.argv) > 2 else COLS
    salida = sys.argv[3] if len(sys.argv) > 3 else ARCHIVO_DEFECTO
    generar_matriz_hdf5(n_filas, n_cols, salida)
