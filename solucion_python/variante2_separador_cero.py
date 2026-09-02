"""
===============================================================================
VARIANTE 2: Matriz Llena de Bits '1' con Cabecera y Separador de Fila con Bit '0'
===============================================================================
Contexto y Motivación del Experimento:
- Al analizar la Variante 1, nos dimos cuenta de que habíamos generado simplemente
  un vector o línea continua de bits en disco, y que esto realmente no cumplía con la
  definición estructural de una matriz en archivo.
- Concluimos que para entrar en la definición formal de matriz se requería una cabecera
  (Header con dimensiones) y delimitadores de fin de fila.
- Como en las indicaciones el docente NO especificó con qué valores debía llenarse
  la matriz (solo requirió escribir 100k x 100k y mostrarla), se planteó:
  * Rellenar cada celda con el bit '1' (100,000 bits en 1).
  * Colocar un bit '0' al final de cada fila como separador/delimitador de fin de fila.

¿Por qué nos dimos cuenta de que NO tenía sentido?:
1. Ruptura del Alineamiento de Bytes (Bit-Boundary Hazard):
   100,000 bits de datos + 1 bit separador = 100,001 bits por fila.
   Al no ser múltiplo de 8 (12,500.125 bytes), cada fila empieza corrida en un bit
   distinto dentro del byte (Fila 0 en bit 0, Fila 1 en bit 1, etc.), haciendo
   imposible un acceso algebraico limpio sin operaciones complejas inter-byte.
2. Matriz Trivial e Imposibilidad de Almacenar Datos Heterogéneos:
   Para que el bit '0' sirva de delimitador, los datos deben ser obligatoriamente '1'.
   Si se quieren almacenar datos reales con ceros y unos, el dato '0' y el separador '0'
   son indistinguibles.

Transición a la Variante 3:
- Esta inviabilidad nos llevó a la siguiente conclusión: necesitamos soportar números
  reales (valores 0 al 2) y un separador que no colisione y respete la alineación de bytes.
  Esto dio origen a la Variante 3 (enteros de 2 bits con byte separador 0xFF = 11111111).
===============================================================================
"""

import os
import time
import numpy as np

ROWS = 100_000
COLS = 100_000
ARCHIVO = "matriz_variante2_separador_cero.bin"

def generar_variante2(limite_filas=1000):
    print("=== [VARIANTE 2] Matriz Llena de 1s con Separador de Fila '0' ===")
    print(f"Dimensiones de prueba: {limite_filas} x {COLS}")
    print(f"Archivo de salida: {ARCHIVO}")
    print("Regla: Todas las celdas de datos valen 1; cada fila termina en separador 0 (0x00).")
    
    inicio = time.time()
    with open(ARCHIVO, "wb") as f:
        # 1. Cabecera autodescriptiva (16 bytes: uint64 ROWS, uint64 COLS)
        np.array([limite_filas, COLS], dtype=np.uint64).tofile(f)
        
        # 2. Fila llena exclusivamente de 1s:
        # 100,000 celdas de '1' = 12,500 bytes con valor 0xFF (todos sus bits en 1)
        bytes_datos_fila = COLS // 8
        fila_unos_bytes = bytes([0xFF] * bytes_datos_fila)
        
        # 3. Separador de fin de fila: byte con valor 0x00 (delimitador 0)
        separador_cero = bytes([0x00])
        
        for i in range(limite_filas):
            # Escribimos los datos (todos 1s) + el separador (0)
            f.write(fila_unos_bytes)
            f.write(separador_cero)
            
            if (i + 1) % 500 == 0 or (i + 1) == limite_filas:
                print(f"  Fila generada: {i + 1} / {limite_filas}")

    duracion = time.time() - inicio
    tamano_bytes = os.path.getsize(ARCHIVO)
    print(f"\nGeneración finalizada en {duracion:.2f} s")
    print(f"Tamaño generado: {tamano_bytes:,} bytes")
    print(f"Estructura por fila: 12,500 bytes (todos 1s) + 1 byte (separador 0) = 12,501 bytes")

def leer_celda_variante2(fila: int, col: int) -> int:
    """Lectura con salto de separador (Stride = 12,500 bytes datos + 1 byte separador)."""
    TAMANO_CABECERA = 16
    ANCHO_FILA_CON_SEPARADOR = (COLS // 8) + 1  # 12,501 bytes
    
    byte_en_fila = col // 8
    bit_en_byte = col % 8
    offset_total = TAMANO_CABECERA + (fila * ANCHO_FILA_CON_SEPARADOR) + byte_en_fila
    
    with open(ARCHIVO, "rb") as f:
        f.seek(offset_total)
        byte_leido = int.from_bytes(f.read(1), byteorder="big")
        bit = (byte_leido >> (7 - bit_en_byte)) & 1
        return bit

def verificar_separador_fila(fila: int) -> int:
    """Verifica que el byte separador al final de la fila sea efectivamente 0x00."""
    TAMANO_CABECERA = 16
    ANCHO_FILA_CON_SEPARADOR = (COLS // 8) + 1
    offset_separador = TAMANO_CABECERA + (fila * ANCHO_FILA_CON_SEPARADOR) + (COLS // 8)
    
    with open(ARCHIVO, "rb") as f:
        f.seek(offset_separador)
        return int.from_bytes(f.read(1), byteorder="big")

if __name__ == "__main__":
    generar_variante2(limite_filas=1000)
    print("\nLectura de celdas (todas deben retornar 1):")
    for r, c in [(0, 0), (100, 500), (999, 99999)]:
        val = leer_celda_variante2(r, c)
        print(f"  Celda ({r}, {c}) = {val}")
    
    print("\nVerificación de bytes separadores (deben retornar 0):")
    for r in [0, 1, 2, 999]:
        sep = verificar_separador_fila(r)
        print(f"  Separador final de fila {r}: valor = {sep} (0x{sep:02X})")
