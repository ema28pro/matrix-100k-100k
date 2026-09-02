# Laboratorio 1: Inspeccion de Cabecera Binaria y Bytes Crudos
# Permite leer e inspeccionar los primeros bytes (Hexadecimal y ASCII) de cualquier archivo.
# Por defecto analiza 'matriz_100k.bin', pero acepta cualquier archivo (ej. JPG, BMP, etc.).

import os
import sys

def buscar_archivo_por_defecto():
    rutas = ["matriz_100k.bin", os.path.join("data", "matriz_100k.bin"), "muestra_matriz.bmp"]
    for r in rutas:
        if os.path.exists(r):
            return r
    return "matriz_100k.bin"

def inspeccionar_cabecera(ruta_archivo=None, n_bytes=64):
    if not ruta_archivo:
        ruta_archivo = buscar_archivo_por_defecto()

    if not os.path.exists(ruta_archivo):
        print(f"Error: No se encontro el archivo '{ruta_archivo}'.")
        print("Uso: python inspeccionar_cabecera.py [ruta_archivo] [cantidad_bytes]")
        return

    tamano_total = os.path.getsize(ruta_archivo)
    bytes_a_leer = min(n_bytes, tamano_total)

    with open(ruta_archivo, "rb") as f:
        cabecera = f.read(bytes_a_leer)

    print("=================================================================")
    print(f" INSPECTOR DE CABECERA BINARIA: {os.path.basename(ruta_archivo)}")
    print("=================================================================")
    print(f"Ruta: {os.path.abspath(ruta_archivo)}")
    print(f"Tamano total del archivo: {tamano_total:,} bytes")
    print(f"Bytes leidos: {len(cabecera)} bytes\n")

    # 1. Representacion Hexadecimal continua (metodo solicitado)
    print("--- 1. Hexadecimal Continuo (.hex()) ---")
    print(cabecera.hex())

    # 2. Representacion Hexadecimal espaciada cada 2 caracteres (bytes)
    print("\n--- 2. Hexadecimal Separado por Bytes ---")
    hex_espaciado = " ".join(f"{b:02X}" for b in cabecera)
    print(hex_espaciado)

    # 3. Vista Forense Tipo Hexdump (Offset | Hexadecimal | ASCII)
    print("\n--- 3. Volcado Hexdump (Offset | Bytes Hexadecimal | ASCII) ---")
    print(" Offset    00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F   Texto ASCII")
    print("-" * 72)

    for i in range(0, len(cabecera), 16):
        chunk = cabecera[i:i + 16]
        hex_primera_mitad = " ".join(f"{b:02X}" for b in chunk[:8])
        hex_segunda_mitad = " ".join(f"{b:02X}" for b in chunk[8:])
        hex_formateado = f"{hex_primera_mitad:<23}  {hex_segunda_mitad:<23}"

        # Caracteres ASCII imprimibles o punto (.)
        ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        print(f"{i:08X}   {hex_formateado}  |{ascii_repr}|")

    # 4. Diagnostico de firma comun
    print("\n--- 4. Diagnostico de Firma Detectada ---")
    if cabecera.startswith(b'\x89HDF\r\n\x1a\n'):
        print("[DETECTADO] Firma canónica HDF5 (Hierarchical Data Format 5) - Superblock v2")
    elif cabecera.startswith(b'BM'):
        print("[DETECTADO] Firma de imagen Bitmap (BMP Windows)")
    elif cabecera.startswith(b'\xFF\xD8\xFF'):
        print("[DETECTADO] Firma de imagen JPEG / JPG (SOI Marker)")
    elif cabecera.startswith(b'\x89PNG\r\n\x1a\n'):
        print("[DETECTADO] Firma de imagen PNG")
    elif len(cabecera) >= 16:
        print("[INFO] Cabecera binaria general de 16+ bytes (posible matriz clasica uint64)")

if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else None
    tamano = int(sys.argv[2]) if len(sys.argv) > 2 else 64
    inspeccionar_cabecera(archivo, tamano)
