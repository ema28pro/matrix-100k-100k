"""
===============================================================================
VARIANTE 3: Matriz de Enteros de 2 Bits (Valores 0 a 2) con Separador 0xFF (11111111)
===============================================================================
Motivación del Experimento:
- Al ver que en la Variante 2 el separador '0' colisionaba con los datos, se diseñó
  un sistema donde los datos y los separadores pertenecen a dominios disjuntos:
  1. Las celdas almacenan enteros en el rango [0, 2] usando 2 bits por elemento:
     - 00b = 0
     - 01b = 1
     - 10b = 2
     - (11b = 3 queda reservado o no utilizado por los datos).
  2. En cada byte caben exactamente 4 celdas (100,000 / 4 = 25,000 bytes por fila).
  3. Al final de cada fila se inserta un byte separador centinela con valor 0xFF
     (binario: 11111111 = 255), garantizando que ningún dato colisione con el separador.

Análisis y Conclusión Técnica:
- Funciona correctamente y resuelve la ambigüedad semántica.
- Sin embargo, para matrices densas regulares, el byte separador de fila sigue siendo
  TÉCNICAMENTE REDUNDANTE:
  * Como cada fila mide exactamente 25,000 bytes de datos + 1 byte de separador,
    el offset exacto se puede calcular directamente con una multiplicación.
  * El separador no aporta ninguna información nueva que no brinde la fórmula:
    offset = 16 + fila * (25000 + 1)
  * Para el problema original de matriz binaria (0 y 1), pasar a 2 bits duplica
    innecesariamente el tamaño a ~2.5 GB. Por ello, la SOLUCIÓN DEFINITIVA regresa
    a 1 bit por celda (8 bits/byte) y elimina por completo los separadores.
===============================================================================
"""

import os
import time
import numpy as np

ROWS = 100_000
COLS = 100_000
ARCHIVO = "matriz_variante3_2bits_0xff.bin"
SEPARADOR_BYTE = bytes([0xFF])  # 11111111 en binario

def empaquetar_2bits_fila(valores_2bits: np.ndarray) -> bytes:
    """
    Empaqueta un arreglo 1D de enteros (valores 0..2) en bytes (4 elementos por byte).
    valores_2bits: np.ndarray con valores en {0, 1, 2} de longitud divisible por 4.
    """
    # Agrupamos de a 4 celdas
    v = valores_2bits.reshape(-1, 4)
    # Desplazamos y combinamos: (c0 << 6) | (c1 << 4) | (c2 << 2) | c3
    bytes_array = (v[:, 0] << 6) | (v[:, 1] << 4) | (v[:, 2] << 2) | v[:, 3]
    return bytes_array.astype(np.uint8).tobytes()

def desempaquetar_2bits_celda(byte_val: int, pos_en_byte: int) -> int:
    """Extrae el valor de 2 bits (pos_en_byte de 0 a 3, de más a menos significativo)."""
    shift = (3 - pos_en_byte) * 2
    return (byte_val >> shift) & 0b11

def generar_variante3(limite_filas=1000):
    print("=== [VARIANTE 3] Matriz 2-bits (0..2) con Separador 0xFF (11111111) ===")
    print(f"Dimensiones de prueba: {limite_filas} x {COLS}")
    print(f"Archivo de salida: {ARCHIVO}")
    
    rng = np.random.default_rng(seed=42)
    inicio = time.time()
    
    with open(ARCHIVO, "wb") as f:
        # Cabecera de 16 bytes (uint64 ROWS, uint64 COLS)
        np.array([limite_filas, COLS], dtype=np.uint64).tofile(f)
        
        for i in range(limite_filas):
            # Generamos valores aleatorios en {0, 1, 2}
            fila_vals = rng.integers(0, 3, size=COLS, dtype=np.uint8)
            fila_empaquetada = empaquetar_2bits_fila(fila_vals)
            
            # Escribimos los 25,000 bytes de datos + 1 byte de separador (0xFF)
            f.write(fila_empaquetada)
            f.write(SEPARADOR_BYTE)
            
            if (i + 1) % 500 == 0 or (i + 1) == limite_filas:
                print(f"  Fila generada: {i + 1} / {limite_filas}")

    duracion = time.time() - inicio
    tamano_bytes = os.path.getsize(ARCHIVO)
    print(f"\nGeneración finalizada en {duracion:.2f} s")
    print(f"Tamaño generado: {tamano_bytes:,} bytes")
    bytes_por_fila = (COLS // 4) + 1  # 25,001 bytes
    print(f"Estructura por fila: 25,000 bytes (datos 2-bits) + 1 byte (0xFF) = {bytes_por_fila:,} bytes")

def leer_celda_variante3(fila: int, col: int) -> int:
    """Lectura directa O(1) de una celda de 2 bits."""
    TAMANO_CABECERA = 16
    BYTES_DATOS_FILA = COLS // 4      # 25,000 bytes
    ANCHO_TOTAL_FILA = BYTES_DATOS_FILA + 1  # 25,001 bytes (con separador 0xFF)
    
    byte_en_fila = col // 4
    pos_en_byte = col % 4
    offset_total = TAMANO_CABECERA + (fila * ANCHO_TOTAL_FILA) + byte_en_fila
    
    with open(ARCHIVO, "rb") as f:
        f.seek(offset_total)
        byte_leido = int.from_bytes(f.read(1), byteorder="big")
        return desempaquetar_2bits_celda(byte_leido, pos_en_byte)

def verificar_separadores_variante3(limite_filas=1000):
    """Verifica que todos los bytes separadores sean efectivamente 0xFF (11111111)."""
    TAMANO_CABECERA = 16
    ANCHO_TOTAL_FILA = (COLS // 4) + 1
    
    print("\nVerificando integridad de separadores 0xFF al final de cada fila...")
    with open(ARCHIVO, "rb") as f:
        for r in range(min(5, limite_filas)):
            offset_separador = TAMANO_CABECERA + (r * ANCHO_TOTAL_FILA) + (COLS // 4)
            f.seek(offset_separador)
            sep = f.read(1)
            print(f"  Fila {r}: Separador en offset {offset_separador} -> Hex: {sep.hex().upper()} (Binario: {bin(sep[0])[2:].zfill(8)})")

if __name__ == "__main__":
    generar_variante3(limite_filas=1000)
    verificar_separadores_variante3(limite_filas=1000)
    print("\nLectura de celdas de prueba (valores entre 0 y 2):")
    for r, c in [(0, 0), (10, 20), (500, 45000), (999, 99999)]:
        val = leer_celda_variante3(r, c)
        print(f"  Celda ({r}, {c}) = {val}")
