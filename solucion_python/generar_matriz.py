import numpy as np
import os
import time
import sys
import struct

ROWS = 100_000
COLS = 100_000
CHUNK = 1_000
ARCHIVO = "matriz_100k.bin"

# Firma y especificación estándar HDF5 (Superblock format)
HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'  # 8 bytes canónicos
HDF5_HEADER_SIZE = 64              # Cabecera fija de 64 bytes

def empaquetar_cabecera_hdf5(filas, cols, bytes_datos, ancho_total):
    # Formato: 8s (Magic) + B (ver) + B (bits/celda) + B (tiene_sep) + B (val_sep) + I (flags)
    #          + Q (filas) + Q (cols) + Q (bytes_datos) + Q (ancho_total) + 16s (reservado) = 64 bytes
    return struct.pack(
        '<8sBBBBIQQQQ16s',
        HDF5_MAGIC,
        2,              # Versión de formato
        2,              # Bits por celda (valores 0..2)
        1,              # Indicador de separador de fila activo (True)
        0xFF,           # Byte separador (11111111 = 255)
        0,              # Flags / alineamiento
        filas,
        cols,
        bytes_datos,
        ancho_total,
        b'\x00' * 16    # Padding reservado
    )

def generar_matriz():
    rng = np.random.default_rng()

    bytes_datos_fila = COLS // 4      # 25,000 bytes
    ancho_fila = bytes_datos_fila + 1  # 25,001 bytes (con separador 0xFF)
    tamano_esperado = HDF5_HEADER_SIZE + (ROWS * ancho_fila)

    print("=================================================================")
    print(" GENERADOR MATRIZ EN DISCO (Estandar Header HDF5 + 2-Bits + 0xFF)")
    print("=================================================================")
    print(f"Firma Cabecera: HDF5 (\\x89HDF\\r\\n\\x1a\\n) [{HDF5_HEADER_SIZE} bytes]")
    print(f"Dimensiones: {ROWS:,} x {COLS:,}")
    print("Celdas: Enteros de 2 bits (valores posibles: 0, 1, 2)")
    print("Separador de fin de fila: 1 byte con valor 11111111 (0xFF = 255)")
    print(f"Estructura por fila: {bytes_datos_fila:,} B datos + 1 B separador = {ancho_fila:,} B")
    print(f"Tamano total esperado: {tamano_esperado:,} bytes (~{tamano_esperado / 1e9:.2f} GB)")
    print(f"Destino: {os.path.abspath(ARCHIVO)}\n")

    inicio = time.time()

    with open(ARCHIVO, "wb") as f:
        # 1. Escribir Cabecera estándar HDF5 de 64 bytes
        cabecera_bytes = empaquetar_cabecera_hdf5(ROWS, COLS, bytes_datos_fila, ancho_fila)
        f.write(cabecera_bytes)

        # 2. Generación por lotes (Chunks)
        for i in range(0, ROWS, CHUNK):
            n_filas = min(CHUNK, ROWS - i)
            bloque = rng.integers(0, 3, size=(n_filas, COLS), dtype=np.uint8)

            # Empaquetamos 4 celdas por byte
            v = bloque.reshape(n_filas, -1, 4)
            datos_bytes = (v[:, :, 0] << 6) | (v[:, :, 1] << 4) | (v[:, :, 2] << 2) | v[:, :, 3]

            # Columna separadora 0xFF (11111111)
            sep_col = np.full((n_filas, 1), 0xFF, dtype=np.uint8)

            # Escribir fila completa de 25,001 bytes por bloque a disco
            fila_completa = np.hstack([datos_bytes, sep_col])
            fila_completa.tofile(f)

            if (i // CHUNK) % 10 == 0 or (i + n_filas) == ROWS:
                print(f"  Fila generada: {i + n_filas:,} / {ROWS:,} ({(i + n_filas)/ROWS*100:.1f}%)")

    duracion = time.time() - inicio
    tamano_real = os.path.getsize(ARCHIVO)
    print(f"\nGeneracion exitosa en {duracion:.1f} s")
    print(f"Tamano final en disco: {tamano_real:,} bytes ({tamano_real / 1e9:.2f} GB)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ROWS = int(sys.argv[1])
    generar_matriz()