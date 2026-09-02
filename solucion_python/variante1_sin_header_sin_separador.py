"""
===============================================================================
VARIANTE 1: Matriz Raw sin Cabecera ni Separadores de Fila
===============================================================================
Motivación de Elección de Tipo de Dato:
- Si se usaran enteros de 4 bytes (int), la matriz pesaría 40 GB (inmanejable en RAM).
- Si se usaran caracteres o bytes de 1 byte (char/uint8), pesaría ~10 GB.
- Por ello, se eligió representación binaria pura (1 bit por celda, 8 celdas por byte),
  reduciendo el tamaño a solo ~1.16 GB (1.25 GB).

Ventajas:
- Acceso aleatorio directo O(1): se puede saltar y consultar cualquier celda (r, c)
  instantáneamente calculando offset = (r * COLS + c) // 8 con f.seek().

La Caída en Cuenta (Limitación):
- Al analizar el archivo generado, nos dimos cuenta de que físicamente en disco era
  únicamente una línea continua / vector unidimensional plano de 10 mil millones de bits.
- No cumplía formalmente con la definición de matriz en archivo (sin header ni marcas de fin de fila),
  lo que motivó la creación de la Variante 2.
===============================================================================
"""

import os
import time
import numpy as np

ROWS = 100_000
COLS = 100_000
CHUNK = 1_000
ARCHIVO = "matriz_variante1_raw.bin"

def generar_variante1(limite_filas=ROWS):
    rng = np.random.default_rng(seed=42)
    print("=== [VARIANTE 1] Generación Raw (Sin Cabecera, Sin Separador) ===")
    print(f"Dimensiones objetivo: {limite_filas} x {COLS}")
    print(f"Archivo de salida: {ARCHIVO}")
    
    inicio = time.time()
    with open(ARCHIVO, "wb") as f:
        # Nota: NO se escribe ningún encabezado ni metadato
        for i in range(0, limite_filas, CHUNK):
            n_filas = min(CHUNK, limite_filas - i)
            bloque = rng.integers(0, 2, size=(n_filas, COLS), dtype=np.uint8)
            # Empaquetamos 8 bits por byte directamente
            np.packbits(bloque, axis=1).tofile(f)
            
            if (i // CHUNK) % 20 == 0 or (i + n_filas) == limite_filas:
                print(f"  Progreso: fila {i + n_filas} / {limite_filas} ({(i + n_filas)/limite_filas*100:.1f}%)")

    duracion = time.time() - inicio
    tamano_bytes = os.path.getsize(ARCHIVO)
    print(f"\nGeneración finalizada en {duracion:.2f} s")
    print(f"Tamaño generado: {tamano_bytes:,} bytes ({tamano_bytes / 1e9:.3f} GB)")

def leer_celda_variante1(fila: int, col: int) -> int:
    """Acceso aleatorio O(1) asumiendo dimensiones fijas conocidas externamente."""
    if not (0 <= fila < ROWS and 0 <= col < COLS):
        raise IndexError("Coordenadas fuera de rango")
    
    indice_lineal = fila * COLS + col
    byte_offset = indice_lineal // 8
    bit_offset = indice_lineal % 8
    
    with open(ARCHIVO, "rb") as f:
        f.seek(byte_offset)
        byte_leido = int.from_bytes(f.read(1), byteorder="big")
        bit = (byte_leido >> (7 - bit_offset)) & 1
        return bit

if __name__ == "__main__":
    # Genera una prueba de 2,000 filas por defecto para comprobación rápida;
    # cambia a ROWS para generar los 100k completos.
    generar_variante1(limite_filas=2000)
    print("\nLectura de prueba O(1):")
    for r, c in [(0, 0), (100, 50), (1999, 99999)]:
        val = leer_celda_variante1(r, c)
        print(f"  Celda ({r}, {c}) = {val}")
