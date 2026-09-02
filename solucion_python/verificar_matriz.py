import numpy as np
import os
import struct

def buscar_archivo():
    rutas = ["matriz_100k.bin", os.path.join("data", "matriz_100k.bin"), os.path.join("..", "matriz_100k.bin")]
    for r in rutas:
        if os.path.exists(r):
            return r
    return rutas[0]

ARCHIVO = buscar_archivo()
HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'

def detectar_formato(f, tamano_total):
    f.seek(0)
    magic = f.read(8)
    if magic == HDF5_MAGIC:
        # Formato 1: Cabecera Estándar HDF5 (64 bytes)
        f.seek(0)
        hdr = f.read(64)
        _, ver, bits_celda, tiene_sep, val_sep, flags, rows, cols, bytes_datos, ancho_fila, _ = struct.unpack(
            '<8sBBBBIQQQQ16s', hdr
        )
        return {
            'formato': 'Estándar HDF5 (64 bytes)',
            'offset_datos': 64,
            'rows': rows,
            'cols': cols,
            'bits_celda': bits_celda,
            'tiene_sep': bool(tiene_sep),
            'val_sep': val_sep,
            'bytes_datos': bytes_datos,
            'ancho_fila': ancho_fila,
            'tamano_esperado': 64 + (rows * ancho_fila)
        }
    else:
        # Formato 2: Cabecera Clásica Directa (16 bytes: uint64 ROWS, uint64 COLS)
        f.seek(0)
        cabecera_16 = f.read(16)
        dims = np.frombuffer(cabecera_16, dtype=np.uint64)
        rows, cols = int(dims[0]), int(dims[1])

        # Deducir si es 1-bit (C++ original: cols // 8) o 2-bits con separador (cols // 4 + 1)
        ancho_1bit = int(np.ceil(cols / 8))
        ancho_2bit_sep = (cols // 4) + 1

        tam_1bit = 16 + (rows * ancho_1bit)
        tam_2bit = 16 + (rows * ancho_2bit_sep)

        if abs(tamano_total - tam_1bit) <= abs(tamano_total - tam_2bit):
            # Formato 1-bit clásico
            return {
                'formato': 'Cabecera Clásica (16 bytes) - 1 bit por celda',
                'offset_datos': 16,
                'rows': rows,
                'cols': cols,
                'bits_celda': 1,
                'tiene_sep': False,
                'val_sep': None,
                'bytes_datos': ancho_1bit,
                'ancho_fila': ancho_1bit,
                'tamano_esperado': tam_1bit
            }
        else:
            # Formato 2-bits clásico con separador
            return {
                'formato': 'Cabecera Clásica (16 bytes) - 2 bits con separador 0xFF',
                'offset_datos': 16,
                'rows': rows,
                'cols': cols,
                'bits_celda': 2,
                'tiene_sep': True,
                'val_sep': 0xFF,
                'bytes_datos': cols // 4,
                'ancho_fila': ancho_2bit_sep,
                'tamano_esperado': tam_2bit
            }

def verificar():
    if not os.path.exists(ARCHIVO):
        print(f"Error: No se encontró el archivo '{ARCHIVO}'.")
        print("Primero genera la matriz con 'crear_matriz.exe' o 'generar_matriz.py'.")
        return

    tamano_real = os.path.getsize(ARCHIVO)
    if tamano_real < 16:
        print(f"Error: El archivo tiene solo {tamano_real} bytes, insuficiente para leer cabecera.")
        return

    with open(ARCHIVO, "rb") as f:
        meta = detectar_formato(f, tamano_real)

        print("=================================================================")
        print(f" VERIFICADOR UNIVERSAL DE MATRIZ ({meta['formato']})")
        print("=================================================================")
        print(f"Archivo: {os.path.abspath(ARCHIVO)}")
        print(f"Dimensiones en cabecera: {meta['rows']:,} filas x {meta['cols']:,} columnas")
        print(f"Codificación: {meta['bits_celda']} bit(s) por celda")
        print(f"Separador de fila: {'Activo (0x%02X)' % meta['val_sep'] if meta['tiene_sep'] else 'Sin separador'}")
        print(f"Ancho por fila en disco: {meta['ancho_fila']:,} bytes")
        print(f"Tamaño esperado: {meta['tamano_esperado']:,} bytes")
        print(f"Tamaño en disco:  {tamano_real:,} bytes")

        if tamano_real == meta['tamano_esperado']:
            print("[OK] El tamaño físico en disco coincide exactamente con el formato detectado.")
        elif tamano_real < meta['tamano_esperado']:
            print(f"[INFO] Archivo parcial: contiene {(tamano_real - meta['offset_datos']) // meta['ancho_fila']:,} filas completas de {meta['rows']:,}.")

        # Si tiene separador, validarlo
        if meta['tiene_sep']:
            print("\n--- Verificación de Separadores de Fila ---")
            filas_disponibles = max(0, (tamano_real - meta['offset_datos']) // meta['ancho_fila'])
            filas_a_probar = [r for r in [0, 1, 2, meta['rows'] // 2, meta['rows'] - 1] if r < filas_disponibles]
            separadores_ok = True
            for r in filas_a_probar:
                offset_sep = meta['offset_datos'] + (r * meta['ancho_fila']) + meta['bytes_datos']
                f.seek(offset_sep)
                val = f.read(1)[0]
                es_valido = (val == meta['val_sep'])
                if not es_valido: separadores_ok = False
                print(f"  Fila {r:>6}: Offset {offset_sep:>12} -> Valor: 0x{val:02X} ({val}) {'[OK]' if es_valido else '[ERROR]'}")
            if separadores_ok and filas_a_probar:
                print(f"[OK] Todos los separadores probados son válidos (0x{meta['val_sep']:02X}).")

        # Muestra de datos
        filas_disponibles = max(0, (tamano_real - meta['offset_datos']) // meta['ancho_fila'])
        filas_a_leer = min(500, meta['rows'], filas_disponibles)

        if filas_a_leer > 0:
            f.seek(meta['offset_datos'])
            raw = np.fromfile(f, dtype=np.uint8, count=filas_a_leer * meta['ancho_fila']).reshape(filas_a_leer, meta['ancho_fila'])
            datos_bytes = raw[:, :meta['bytes_datos']]

            if meta['bits_celda'] == 1:
                muestra = np.unpackbits(datos_bytes, axis=1)[:, :meta['cols']]
            else:
                c0 = (datos_bytes >> 6) & 0b11
                c1 = (datos_bytes >> 4) & 0b11
                c2 = (datos_bytes >> 2) & 0b11
                c3 = datos_bytes & 0b11
                muestra = np.stack([c0, c1, c2, c3], axis=-1).reshape(filas_a_leer, -1)[:, :meta['cols']]

            print(f"\n--- Distribución de Valores (Muestra de {filas_a_leer:,} filas) ---")
            valores_unicos, conteos = np.unique(muestra, return_counts=True)
            total = muestra.size
            for v, c in zip(valores_unicos, conteos):
                print(f"  Valor {v}: {c:,} celdas ({c / total * 100:.2f}%)")

            print("\nVista previa (primeras 4 filas, primeras 16 columnas):")
            for r in range(min(4, filas_a_leer)):
                fila_str = " ".join(str(x) for x in muestra[r, :16])
                print(f"  Fila {r:>3}: {fila_str}")

if __name__ == "__main__":
    verificar()