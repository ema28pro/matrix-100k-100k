# Laboratorio 1: Generador de Matriz Binaria Pequena de Control y Verificacion
# Genera un archivo 'matriz_100k.bin' con dimensiones reducidas (ej. 20 filas x 40 columnas)
# Incluye:
#   - Fila 0 (inicio): Fila completa llena de valores '2'.
#   - Filas intermedias: Datos aleatorios con '2' al inicio y al final de la fila.
#   - Fila N-1 (final): Fila completa llena de valores '2'.
# Estructura: Cabecera Estandar HDF5 (64B) + celdas de 2 bits + byte separador 0xFF.

import os
import sys
import struct
import numpy as np

ARCHIVO = "matriz_100k.bin"
HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'

def generar_matriz_pequena(filas=20, cols=40):
    # Asegurar que las columnas sean multiplo de 4 para empaquetamiento perfecto de 2 bits
    if cols % 4 != 0:
        cols = ((cols // 4) + 1) * 4

    bytes_datos_fila = cols // 4
    ancho_fila = bytes_datos_fila + 1  # Datos + byte separador 0xFF
    tamano_esperado = 64 + (filas * ancho_fila)

    print("=================================================================")
    print(" GENERADOR DE MATRIZ PEQUENA DE CONTROL (Verificacion Visual)")
    print("=================================================================")
    print(f"Dimensiones:          {filas} filas x {cols} columnas")
    print(f"Bytes datos por fila: {bytes_datos_fila} bytes ({cols} celdas @ 2 bits)")
    print(f"Separador de fila:    1 byte centinela 0xFF (11111111)")
    print(f"Ancho total fila:     {ancho_fila} bytes")
    print(f"Tamano cabecera HDF5: 64 bytes")
    print(f"Tamano total en disco:{tamano_esperado:,} bytes")
    print(f"Destino:              {os.path.abspath(ARCHIVO)}\n")

    # 1. Construir la matriz en memoria
    # Generamos datos aleatorios en el rango [0, 2]
    rng = np.random.default_rng(42)
    matriz = rng.integers(0, 3, size=(filas, cols), dtype=np.uint8)

    # Regla solicitada: Fila de '2's al inicio y al final
    matriz[0, :] = 2           # Fila inicial completa llena de '2'
    matriz[filas - 1, :] = 2   # Fila final completa llena de '2'

    # En filas intermedias, colocar '2' al inicio y al final de la fila
    matriz[:, 0] = 2           # Primera columna con '2'
    matriz[:, cols - 1] = 2    # Ultima columna con '2'

    # 2. Empaquetar a 2 bits (4 celdas por byte)
    # Nota: Cuatro celdas con valor 2 (10b) producen el byte 10101010b = 0xAA
    v = matriz.reshape(filas, -1, 4)
    datos_empaquetados = (v[:, :, 0] << 6) | (v[:, :, 1] << 4) | (v[:, :, 2] << 2) | v[:, :, 3]

    # Columna separadora 0xFF
    sep_col = np.full((filas, 1), 0xFF, dtype=np.uint8)
    filas_con_separador = np.hstack([datos_empaquetados, sep_col])

    # 3. Empaquetar Cabecera Estándar HDF5 de 64 bytes
    cabecera_hdf5 = struct.pack(
        '<8sBBBBIQQQQ16s',
        HDF5_MAGIC,
        2,                  # Version de superbloque
        2,                  # Bits por celda
        1,                  # Separador activo (True)
        0xFF,               # Byte separador (11111111)
        0,                  # Flags
        filas,
        cols,
        bytes_datos_fila,
        ancho_fila,
        b'\x00' * 16        # Padding
    )

    # 4. Escribir a disco
    with open(ARCHIVO, "wb") as f:
        f.write(cabecera_hdf5)
        filas_con_separador.tofile(f)

    print("[OK] Matriz pequena generada exitosamente.")
    print("\n--- Vista Previa en Matriz (Valores 0, 1, 2) ---")
    for r in range(filas):
        fila_str = "".join(str(x) for x in matriz[r])
        print(f"Fila {r:02d}: {fila_str}")

    print("\n--- Comprobacion Hexadecimal en Fila 0 y Ultima Fila ---")
    print(f"Fila  0 (puros 2): Datos = 0xAA x {bytes_datos_fila} bytes + Separador = 0xFF")
    print(f"Fila {filas - 1:2d} (puros 2): Datos = 0xAA x {bytes_datos_fila} bytes + Separador = 0xFF")

if __name__ == "__main__":
    n_filas = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    n_cols = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    generar_matriz_pequena(n_filas, n_cols)
