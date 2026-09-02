# Laboratorio 1: Visor Procedural Interactivo de Chunks en TXT para Bloc de Notas
# Escribe UNICAMENTE los datos numericos puros (0, 1, 2) en 'vista_matriz.txt'.
# Sin cabeceras, sin prefijos de fila, sin decoraciones en el archivo de texto.
# Permite navegar entre chunks interactivamente desde la terminal.

import os
import sys
import struct
import subprocess
import numpy as np

ARCHIVO_TXT = "vista_matriz.txt"
ARCHIVO_BIN = "matriz_100k.bin"
HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'

def detectar_formato_bin():
    if not os.path.exists(ARCHIVO_BIN):
        return None

    tamano = os.path.getsize(ARCHIVO_BIN)
    if tamano < 16:
        return None

    with open(ARCHIVO_BIN, "rb") as f:
        magic = f.read(8)
        if magic == HDF5_MAGIC:
            f.seek(0)
            hdr = f.read(64)
            _, ver, bits, sep, val_sep, _, rows, cols, bytes_datos, ancho_fila, _ = struct.unpack(
                '<8sBBBBIQQQQ16s', hdr
            )
            return {'tipo': 'HDF5', 'offset': 64, 'rows': rows, 'cols': cols, 'bits': bits, 'ancho_fila': ancho_fila}
        else:
            f.seek(0)
            dims = np.frombuffer(f.read(16), dtype=np.uint64)
            rows, cols = int(dims[0]), int(dims[1])
            ancho_1bit = int(np.ceil(cols / 8))
            ancho_2bit = (cols // 4) + 1
            if abs(tamano - (16 + rows * ancho_1bit)) <= abs(tamano - (16 + rows * ancho_2bit)):
                return {'tipo': '1-bit', 'offset': 16, 'rows': rows, 'cols': cols, 'bits': 1, 'ancho_fila': ancho_1bit}
            else:
                return {'tipo': '2-bits', 'offset': 16, 'rows': rows, 'cols': cols, 'bits': 2, 'ancho_fila': ancho_2bit}

def extraer_chunk_disco(f_bin, info, fila_ini, col_ini, alto, ancho):
    filas_reales = min(alto, max(0, info['rows'] - fila_ini))
    cols_reales = min(ancho, max(0, info['cols'] - col_ini))
    if filas_reales <= 0 or cols_reales <= 0:
        return np.zeros((0, 0), dtype=np.uint8)

    resultado = np.zeros((filas_reales, cols_reales), dtype=np.uint8)
    bits = info['bits']

    for r in range(filas_reales):
        f = fila_ini + r
        if bits == 1:
            bytes_necesarios = int(np.ceil((col_ini + cols_reales) / 8))
            f_bin.seek(info['offset'] + (f * info['ancho_fila']))
            raw = f_bin.read(bytes_necesarios)
            if len(raw) == bytes_necesarios:
                desemp = np.unpackbits(np.frombuffer(raw, dtype=np.uint8))
                resultado[r] = desemp[col_ini:col_ini + cols_reales]
        else:
            bytes_necesarios = int(np.ceil((col_ini + cols_reales) / 4))
            f_bin.seek(info['offset'] + (f * info['ancho_fila']))
            raw = f_bin.read(bytes_necesarios)
            if len(raw) == bytes_necesarios:
                arr = np.frombuffer(raw, dtype=np.uint8)
                c0 = (arr >> 6) & 0b11
                c1 = (arr >> 4) & 0b11
                c2 = (arr >> 2) & 0b11
                c3 = arr & 0b11
                desemp = np.stack([c0, c1, c2, c3], axis=-1).ravel()
                resultado[r] = desemp[col_ini:col_ini + cols_reales]

    return resultado

def generar_chunk_procedural(fila_ini, col_ini, alto, ancho):
    filas = np.arange(fila_ini, fila_ini + alto)[:, None]
    cols = np.arange(col_ini, col_ini + ancho)[None, :]
    h = (filas * 131071 + cols * 524287 + 104729) % 3
    return h.astype(np.uint8)

def escribir_chunk_puro_en_txt(chunk_data, con_espacios=False):
    """Escribe UNICAMENTE los numeros de la matriz sin ninguna decoracion."""
    sep = " " if con_espacios else ""
    with open(ARCHIVO_TXT, "w", encoding="utf-8") as f:
        for fila in chunk_data:
            linea_numeros = sep.join(str(int(x)) for x in fila)
            f.write(linea_numeros + "\n")

def navegar_chunks_interactivo():
    info_bin = detectar_formato_bin()
    origen = f"Disco ({ARCHIVO_BIN}) [{info_bin['tipo']}]" if info_bin else "Sintesis Procedural"
    total_filas = info_bin['rows'] if info_bin else 100_000
    total_cols = info_bin['cols'] if info_bin else 100_000

    alto_chunk = 40
    ancho_chunk = 80
    fila_actual = 0
    col_actual = 0
    con_espacios = False

    # Crear archivo y abrir Notepad de Windows
    try:
        with open(ARCHIVO_TXT, "w", encoding="utf-8") as f_init:
            f_init.write("Cargando primer chunk...\n")
        subprocess.Popen(["notepad.exe", ARCHIVO_TXT])
    except Exception:
        pass

    f_bin = open(ARCHIVO_BIN, "rb") if info_bin else None

    print("=================================================================")
    print(" NAVEGADOR INTERACTIVO DE CHUNKS (Datos Puros en Bloc de Notas)")
    print("=================================================================")
    print(f"Archivo de texto: {os.path.abspath(ARCHIVO_TXT)}")
    print(f"Dimensiones de matriz: {total_filas:,} Filas x {total_cols:,} Columnas")
    print(f"Tamano de cada chunk:  {alto_chunk} filas x {ancho_chunk} columnas")
    print(f"Origen de los datos:   {origen}\n")
    print("Controles en Terminal:")
    print("  [ENTER]      -> Avanzar al siguiente chunk (+columnas)")
    print("  d / a        -> Mover derecha / izquierda (+/- columnas)")
    print("  s / w        -> Mover abajo / arriba (+/- filas)")
    print("  c            -> Ir a coordenada especifica (fila, columna)")
    print("  e            -> Alternar espacios entre numeros (compacto / espaciado)")
    print("  q            -> Salir\n")

    try:
        while True:
            # Obtener datos del chunk
            if f_bin:
                chunk = extraer_chunk_disco(f_bin, info_bin, fila_actual, col_actual, alto_chunk, ancho_chunk)
            else:
                chunk = generar_chunk_procedural(fila_actual, col_actual, alto_chunk, ancho_chunk)

            # Volcar exclusivamente los números al archivo TXT
            escribir_chunk_puro_en_txt(chunk, con_espacios=con_espacios)

            f_fin = min(fila_actual + alto_chunk - 1, total_filas - 1)
            c_fin = min(col_actual + ancho_chunk - 1, total_cols - 1)

            print(f"-> [EN PANTALLA] Filas [{fila_actual:,} a {f_fin:,}] | Cols [{col_actual:,} a {c_fin:,}] "
                  f"(Formato: {'Espaciado' if con_espacios else 'Compacto'})")
            print("   (Actualizado en Bloc de Notas. Presiona F5 en Notepad si no recarga solo)")

            try:
                comando = input("Comando [ENTER=Siguiente, w/a/s/d=Mover, c=Ir a, q=Salir]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if comando in ['q', 'salir', 'exit']:
                break
            elif comando == 'd':
                col_actual = min(col_actual + ancho_chunk, total_cols - ancho_chunk)
            elif comando == 'a':
                col_actual = max(0, col_actual - ancho_chunk)
            elif comando == 's':
                fila_actual = min(fila_actual + alto_chunk, total_filas - alto_chunk)
            elif comando == 'w':
                fila_actual = max(0, fila_actual - alto_chunk)
            elif comando == 'e':
                con_espacios = not con_espacios
                print(f"   Modo cambiado a: {'Espaciado' if con_espacios else 'Compacto'}")
            elif comando == 'c':
                try:
                    r_str = input(f"  Fila destino (0 a {total_filas - 1}): ").strip()
                    c_str = input(f"  Columna destino (0 a {total_cols - 1}): ").strip()
                    fila_actual = min(max(0, int(r_str)), total_filas - alto_chunk)
                    col_actual = min(max(0, int(c_str)), total_cols - ancho_chunk)
                except ValueError:
                    print("  [Error] Entrada invalida.")
            else:
                # [ENTER] por defecto: avanza horizontalmente y salta de fila al llegar al final
                col_actual += ancho_chunk
                if col_actual >= total_cols - ancho_chunk:
                    col_actual = 0
                    fila_actual = (fila_actual + alto_chunk) % (total_filas - alto_chunk)

    finally:
        if f_bin:
            f_bin.close()

    print(f"\nNavegacion finalizada. Archivo disponible en: {os.path.abspath(ARCHIVO_TXT)}")

if __name__ == "__main__":
    navegar_chunks_interactivo()
