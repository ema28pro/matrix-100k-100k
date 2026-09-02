#include <fstream>
#include <iostream>
#include <cstdint>
#include <algorithm>

const char* NOMBRE_ARCHIVO = "matriz_100k.bin";
const uint64_t TAMANO_CABECERA = sizeof(uint64_t) * 2; // 16 bytes (FILAS y COLUMNAS)

uint64_t FILAS = 0;
uint64_t COLUMNAS = 0;
uint64_t BYTES_POR_FILA = 0;

// 1. Obtener el valor de cualquier celda (i, j) en tiempo O(1)
int obtener_celda(std::ifstream& archivo, uint64_t fila, uint64_t columna) {
    if (fila >= FILAS || columna >= COLUMNAS) {
        std::cerr << "Error: Coordenadas (" << fila << ", " << columna << ") fuera de rango [0, " 
                  << FILAS - 1 << "] x [0, " << COLUMNAS - 1 << "].\n";
        return -1;
    }

    uint64_t indice_lineal_bits = fila * COLUMNAS + columna;
    uint64_t byte_offset = TAMANO_CABECERA + (indice_lineal_bits / 8);
    int bit_offset = indice_lineal_bits % 8;

    archivo.seekg(byte_offset, std::ios::beg);
    unsigned char byte_leido;
    archivo.read(reinterpret_cast<char*>(&byte_leido), 1);

    return (byte_leido >> (7 - bit_offset)) & 1;
}

// 2. Mostrar una parte / segmento de una fila específica
void mostrar_segmento_fila(std::ifstream& archivo, uint64_t fila, uint64_t col_inicio, uint64_t cantidad) {
    if (fila >= FILAS) {
        std::cerr << "Error: Fila " << fila << " fuera de rango.\n";
        return;
    }
    if (col_inicio >= COLUMNAS) {
        std::cerr << "Error: Columna inicial " << col_inicio << " fuera de rango.\n";
        return;
    }

    uint64_t col_fin = std::min(col_inicio + cantidad, COLUMNAS);
    std::cout << "\nFila [" << fila << "] (columnas " << col_inicio << " a " << col_fin - 1 << "):\n";

    for (uint64_t c = col_inicio; c < col_fin; ++c) {
        int val = obtener_celda(archivo, fila, c);
        std::cout << val;
        // Espaciado cada 8 bits para facilitar la lectura de bytes
        if ((c - col_inicio + 1) % 8 == 0) std::cout << " ";
    }
    std::cout << "\n";
}

// 3. Mostrar una submatriz/ventana arbitraria desde (fila_inicio, col_inicio)
void mostrar_submatriz(std::ifstream& archivo, uint64_t fila_inicio, uint64_t col_inicio, 
                       uint64_t alto, uint64_t ancho) {
    std::cout << "\nSubmatriz desde (" << fila_inicio << ", " << col_inicio 
              << ") tamano " << alto << "x" << ancho << ":\n";

    for (uint64_t r = 0; r < alto; ++r) {
        uint64_t f = fila_inicio + r;
        if (f >= FILAS) break;

        std::cout << "Fila " << f << ": ";
        for (uint64_t c = 0; c < ancho; ++c) {
            uint64_t col = col_inicio + c;
            if (col >= COLUMNAS) break;
            std::cout << obtener_celda(archivo, f, col) << " ";
        }
        std::cout << "\n";
    }
}

int main() {
    std::ifstream archivo(NOMBRE_ARCHIVO, std::ios::binary);
    if (!archivo) {
        std::cerr << "Error: No se pudo abrir '" << NOMBRE_ARCHIVO << "'. Primero generala con crear_matriz.exe.\n";
        return 1;
    }

    // Leer cabecera de 16 bytes
    archivo.read(reinterpret_cast<char*>(&FILAS), sizeof(FILAS));
    archivo.read(reinterpret_cast<char*>(&COLUMNAS), sizeof(COLUMNAS));

    BYTES_POR_FILA = COLUMNAS / 8;

    std::cout << "=================================================================\n";
    std::cout << " VISOR INTERACTIVO DE MATRIZ EN DISCO\n";
    std::cout << "=================================================================\n";
    std::cout << "Dimensiones leidas de cabecera: " << FILAS << " x " << COLUMNAS << "\n";
    std::cout << "Bytes por fila: " << BYTES_POR_FILA << " B\n\n";

    int opcion = 0;
    while (opcion != 4) {
        std::cout << "\n--- MENU DE CONSULTA (Acceso O(1) con seekg) ---\n";
        std::cout << "1. Consultar una celda especifica (fila, columna)\n";
        std::cout << "2. Mostrar un segmento de una fila\n";
        std::cout << "3. Mostrar una submatriz/ventana 2D (ej. 5x10)\n";
        std::cout << "4. Salir\n";
        std::cout << "Elige una opcion: ";
        if (!(std::cin >> opcion)) break;

        if (opcion == 1) {
            uint64_t r, c;
            std::cout << "Fila (0 a " << FILAS - 1 << "): ";
            std::cin >> r;
            std::cout << "Columna (0 a " << COLUMNAS - 1 << "): ";
            std::cin >> c;
            int val = obtener_celda(archivo, r, c);
            std::cout << "-> Celda [" << r << "][" << c << "] = " << val << "\n";
        } 
        else if (opcion == 2) {
            uint64_t r, c_ini, cant;
            std::cout << "Fila (0 a " << FILAS - 1 << "): ";
            std::cin >> r;
            std::cout << "Columna inicial (0 a " << COLUMNAS - 1 << "): ";
            std::cin >> c_ini;
            std::cout << "Cantidad de celdas a mostrar: ";
            std::cin >> cant;
            mostrar_segmento_fila(archivo, r, c_ini, cant);
        } 
        else if (opcion == 3) {
            uint64_t r_ini, c_ini, alto, ancho;
            std::cout << "Fila inicial: ";
            std::cin >> r_ini;
            std::cout << "Columna inicial: ";
            std::cin >> c_ini;
            std::cout << "Alto (filas a mostrar, ej. 5): ";
            std::cin >> alto;
            std::cout << "Ancho (columnas a mostrar, ej. 10): ";
            std::cin >> ancho;
            mostrar_submatriz(archivo, r_ini, c_ini, alto, ancho);
        }
    }

    archivo.close();
    return 0;
}
