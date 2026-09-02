# Laboratorio 1: Generador de Matriz en Formato Estándar Oficial HDF5 (.h5)
# Compatible 100% con visores oficiales como myHDF5 (https://myhdf5.hdfgroup.org/) y HDFView.
# Utiliza chunks en disco para cumplir con el requisito de no cargar la matriz completa en RAM.

import os
import sys
import time
import h5py
import numpy as np

ARCHIVO_H5 = "matriz_oficial.h5"

def generar_hdf5_oficial(filas=100, cols=100000, chunk_filas=100, chunk_cols=1000):
    print("=================================================================")
    print(" GENERADOR MATRIZ EN FORMATO OFICIAL HDF5 (.h5)")
    print(" (Compatible con myHDF5 y HDFView)")
    print("=================================================================")
    print(f"Destino:         {os.path.abspath(ARCHIVO_H5)}")
    print(f"Dimensiones:     {filas:,} filas x {cols:,} columnas ({filas * cols:,} celdas)")
    print(f"Tamano de Chunk: {chunk_filas} x {chunk_cols} celdas (paginacion en disco)")
    print(f"Tipo de dato:    Enteros uint8 (valores: 0, 1, 2)\n")

    inicio = time.time()
    rng = np.random.default_rng(42)

    # Creamos el contenedor HDF5 oficial
    with h5py.File(ARCHIVO_H5, "w") as f:
        # Metadatos / Atributos de nivel superior
        f.attrs["descripcion"] = "Matriz de laboratorio en almacenamiento secundario"
        f.attrs["autor"] = "ema28pro"
        f.attrs["fecha"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Dataset paginado por chunks en disco (Demand Paging O(1))
        dset = f.create_dataset(
            "matriz",
            shape=(filas, cols),
            dtype=np.uint8,
            chunks=(min(filas, chunk_filas), min(cols, chunk_cols)),
            compression="gzip",       # Compresion estandar HDF5
            compression_opts=4
        )

        # Generacion por bloques (Streaming a disco sin llenar RAM)
        print("Escribiendo bloques a disco...")
        filas_por_lote = min(filas, 1000)
        for i in range(0, filas, filas_por_lote):
            bloque_filas = min(filas_por_lote, filas - i)
            # Generamos datos aleatorios entre 0 y 2
            datos_bloque = rng.integers(0, 3, size=(bloque_filas, cols), dtype=np.uint8)
            dset[i:i + bloque_filas, :] = datos_bloque
            print(f"  -> Filas {i:,} a {i + bloque_filas - 1:,} volcadas a HDF5...")

    tamano_disco = os.path.getsize(ARCHIVO_H5)
    duracion = time.time() - inicio

    print(f"\n[OK] Archivo oficial HDF5 generado exitosamente en {duracion:.2f} segundos.")
    print(f"Tamano en disco: {tamano_disco:,} bytes (~{tamano_disco / 1e6:.2f} MB)")
    print(f"Ya puedes arrastrar '{ARCHIVO_H5}' directamente a:")
    print("https://myhdf5.hdfgroup.org/ para explorarlo sin errores!")

if __name__ == "__main__":
    n_filas = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    n_cols = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    generar_hdf5_oficial(n_filas, n_cols)
