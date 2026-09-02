# Laboratorio 1: Exportar una region de la matriz a imagen BMP
# Compatible con cabecera estandar HDF5 (64B) y cabecera clasica (16B, 1-bit o 2-bits).
# Opciones de color:
#   1. RGB / RVG:       0 = Rojo, 1 = Verde, 2 = Azul
#   2. CMY:             0 = Cyan, 1 = Magenta, 2 = Amarillo (Yellow)
#   3. Escala de Grises: 0 = Negro, 1 = Gris, 2 = Blanco

import numpy as np
import os
import sys
import struct

def buscar_archivo_bin():
    rutas_posibles = [
        "matriz_100k.bin",
        os.path.join("data", "matriz_100k.bin"),
        os.path.join("..", "matriz_100k.bin")
    ]
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    return rutas_posibles[0]

ARCHIVO_BIN = buscar_archivo_bin()
SALIDA_BMP = "muestra_matriz.bmp"
HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'

def detectar_cabecera(f, tamano_total):
    f.seek(0)
    magic = f.read(8)
    if magic == HDF5_MAGIC:
        f.seek(0)
        hdr = f.read(64)
        _, ver, bits_celda, tiene_sep, val_sep, flags, filas, cols, bytes_datos, ancho_fila, _ = struct.unpack(
            '<8sBBBBIQQQQ16s', hdr
        )
        return 64, filas, cols, bits_celda, ancho_fila, "Estándar HDF5 (64B)"
    else:
        f.seek(0)
        dims = np.frombuffer(f.read(16), dtype=np.uint64)
        filas, cols = int(dims[0]), int(dims[1])
        ancho_1bit = int(np.ceil(cols / 8))
        ancho_2bit = (cols // 4) + 1
        tam_1bit = 16 + (filas * ancho_1bit)
        tam_2bit = 16 + (filas * ancho_2bit)

        if abs(tamano_total - tam_1bit) <= abs(tamano_total - tam_2bit):
            return 16, filas, cols, 1, ancho_1bit, "Clásica (16B) - 1 bit"
        else:
            return 16, filas, cols, 2, ancho_2bit, "Clásica (16B) - 2 bits"

def crear_paleta(modo='rgb'):
    """
    Construye la paleta BMP de 256 entradas de 4 bytes [Blue, Green, Red, 0] (RGBQUAD).
    """
    paleta = bytearray(256 * 4)
    modo = str(modo).lower().strip()

    if modo in ['cmy', 'cyan', 'cmyk', '2']:
        # 0: Cyan     (R=0,   G=255, B=255) -> BGR: [255, 255, 0, 0]
        paleta[0:4] = bytes([255, 255, 0, 0])
        # 1: Magenta  (R=255, G=0,   B=255) -> BGR: [255, 0, 255, 0]
        paleta[4:8] = bytes([255, 0, 255, 0])
        # 2: Amarillo (R=255, G=255, B=0)   -> BGR: [0, 255, 255, 0]
        paleta[8:12] = bytes([0, 255, 255, 0])
        descripcion = "CMY -> [0 = Cyan, 1 = Magenta, 2 = Amarillo]"
    elif modo in ['gris', 'grises', 'gray', '3']:
        # 0: Negro, 1: Gris, 2: Blanco
        paleta[0:4] = bytes([0, 0, 0, 0])
        paleta[4:8] = bytes([128, 128, 128, 0])
        paleta[8:12] = bytes([255, 255, 255, 0])
        descripcion = "Escala de Grises -> [0 = Negro, 1 = Gris, 2 = Blanco]"
    else:  # 'rgb', 'rvg', '1' o por defecto
        # 0: Rojo  (R=255, G=0,   B=0) -> BGR: [0, 0, 255, 0]
        paleta[0:4] = bytes([0, 0, 255, 0])
        # 1: Verde (R=0,   G=255, B=0) -> BGR: [0, 255, 0, 0]
        paleta[4:8] = bytes([0, 255, 0, 0])
        # 2: Azul  (R=0,   G=0,   B=255) -> BGR: [255, 0, 0, 0]
        paleta[8:12] = bytes([255, 0, 0, 0])
        descripcion = "RGB (RVG) -> [0 = Rojo, 1 = Verde, 2 = Azul]"

    return paleta, descripcion

def exportar_submatriz_a_bmp(fila_inicio=0, col_inicio=0, ancho=1000, alto=1000, modo_color='rgb'):
    if not os.path.exists(ARCHIVO_BIN):
        print(f"Error: No se encontro el archivo binario en '{ARCHIVO_BIN}'.")
        print("Ejecuta primero 'crear_matriz.exe' o 'generar_matriz.py'.")
        return

    tamano_total = os.path.getsize(ARCHIVO_BIN)
    if tamano_total < 16:
        print("Error: Archivo incompleto o vacío.")
        return

    print(f"Leyendo archivo: {ARCHIVO_BIN} ({tamano_total:,} bytes)")
    with open(ARCHIVO_BIN, "rb") as f:
        tam_cabecera, filas_totales, cols_totales, bits_celda, ancho_fila, formato = detectar_cabecera(f, tamano_total)

        # Ajustar dimensiones a las filas y columnas disponibles
        alto = min(alto, max(0, filas_totales - fila_inicio))
        ancho = min(ancho, max(0, cols_totales - col_inicio))

        if alto == 0 or ancho == 0:
            print(f"Error: La región solicitada está vacía (alto={alto}, ancho={ancho}).")
            return

        paleta, desc_color = crear_paleta(modo_color)

        print("=================================================================")
        print(" EXPORTADOR VISUAL BMP DE SUBMATRIZ")
        print("=================================================================")
        print(f"Formato detectado: {formato}")
        print(f"Dimensiones de matriz: {filas_totales:,} x {cols_totales:,}")
        print(f"Ventana extraida: {alto} filas x {ancho} cols desde ({fila_inicio}, {col_inicio})")
        print(f"Esquema de color: {desc_color}")

        if bits_celda == 1:
            bytes_necesarios = int(np.ceil((col_inicio + ancho) / 8))
        else:
            bytes_necesarios = int(np.ceil((col_inicio + ancho) / 4))

        filas_data = []
        for r in range(fila_inicio, fila_inicio + alto):
            offset = tam_cabecera + (r * ancho_fila)
            f.seek(offset)
            raw_chunk = f.read(bytes_necesarios)
            if len(raw_chunk) < bytes_necesarios:
                print(f"[ERROR] Archivo truncado al leer fila {r} en offset {offset}.")
                return

            raw_bytes = np.frombuffer(raw_chunk, dtype=np.uint8)

            if bits_celda == 1:
                bits_fila = np.unpackbits(raw_bytes)[col_inicio:col_inicio + ancho]
                filas_data.append(bits_fila)
            else:
                c0 = (raw_bytes >> 6) & 0b11
                c1 = (raw_bytes >> 4) & 0b11
                c2 = (raw_bytes >> 2) & 0b11
                c3 = raw_bytes & 0b11
                celdas = np.stack([c0, c1, c2, c3], axis=-1).ravel()
                filas_data.append(celdas[col_inicio:col_inicio + ancho])

    matriz_visual = np.array(filas_data, dtype=np.uint8)

    # Estructura del archivo BMP de 8 bits por pixel con paleta indexada
    row_bytes_unpadded = ancho
    row_padding = (4 - (row_bytes_unpadded % 4)) % 4
    row_stride = row_bytes_unpadded + row_padding
    pixel_data_size = row_stride * alto

    bfOffBits = 14 + 40 + len(paleta)
    bfSize = bfOffBits + pixel_data_size

    bmp_header = struct.pack('<2sIHHI', b'BM', bfSize, 0, 0, bfOffBits)
    dib_header = struct.pack('<IiiHHIIIIII', 40, ancho, -alto, 1, 8, 0, pixel_data_size, 2835, 2835, 256, 0)

    padding_bytes = b'\x00' * row_padding
    pixel_data = bytearray()
    for r in range(alto):
        pixel_data.extend(matriz_visual[r].tobytes())
        pixel_data.extend(padding_bytes)

    with open(SALIDA_BMP, "wb") as f_out:
        f_out.write(bmp_header)
        f_out.write(dib_header)
        f_out.write(paleta)
        f_out.write(pixel_data)

    print(f"\n[OK] Imagen BMP generada: {os.path.abspath(SALIDA_BMP)} ({os.path.getsize(SALIDA_BMP):,} bytes)")
    print(f"Lista para abrir en Paint, Fotos o visor de imagenes.")

def seleccionar_modo_interactivo():
    # 1. Si se pasa argumento en linea de comandos: ej. 'python exportar_bmp.py cmy' o 'rgb'
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        if arg in ['cmy', 'cyan', 'yellow', 'magenta', '2']:
            return 'cmy'
        elif arg in ['gris', 'grises', 'gray', '3']:
            return 'gris'
        else:
            return 'rgb'

    # 2. Modo interactivo si hay terminal abierta
    if sys.stdin.isatty():
        print("\nSelecciona la paleta de colores para la imagen BMP:")
        print("  1. RGB / RVG            (0 = Rojo, 1 = Verde, 2 = Azul)")
        print("  2. Cyan, Magenta, Yellow (0 = Cyan, 1 = Magenta, 2 = Amarillo)")
        print("  3. Escala de Grises     (0 = Negro, 1 = Gris, 2 = Blanco)")
        try:
            opcion = input("Elige una opcion [1/2/3] (Enter para RGB): ").strip()
            if opcion == '2':
                return 'cmy'
            elif opcion == '3':
                return 'gris'
            else:
                return 'rgb'
        except (EOFError, KeyboardInterrupt):
            return 'rgb'

    return 'rgb'

if __name__ == "__main__":
    modo = seleccionar_modo_interactivo()
    exportar_submatriz_a_bmp(modo_color=modo)
