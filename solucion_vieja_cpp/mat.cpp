// Laboratorio 1: matriz 100.000 x 100.000 escrita en disco
// matriz BINARIA (0/1) y empaquetar 8 celdas en cada byte -> ~1.25 GB en disco.

#include <fstream>
#include <random>
#include <chrono>
#include <iostream>
#include <cstdint>

const uint64_t FILAS = 100000;
const uint64_t COLUMNAS = 100000;

const uint64_t FILAS_POR_BLOQUE = 1000;

const uint64_t BYTES_POR_FILA = COLUMNAS / 8;
const uint64_t TAMANO_BLOQUE = FILAS_POR_BLOQUE * BYTES_POR_FILA; // 100000 / 8 = 12.5 MB

const char* NOMBRE_ARCHIVO = "matriz_100k.bin";

static unsigned char bloque[TAMANO_BLOQUE];

void generar_matriz() {
    std::mt19937_64 generador(std::random_device{}());
    std::uniform_int_distribution<int> bit(0, 1);

    std::ofstream archivo(NOMBRE_ARCHIVO, std::ios::binary);
    if (!archivo) {
        std::cerr << "No se pudo crear el archivo.\n";
        return;
    }

    std::cout << "Generando matriz " << FILAS << " x " << COLUMNAS << "...\n";
    std::cout << "Bytes por fila (empaquetada): " << BYTES_POR_FILA << "\n";

    auto inicio = std::chrono::steady_clock::now();

    for (uint64_t f = 0; f < FILAS; f += FILAS_POR_BLOQUE) {
        uint64_t filas_en_este_bloque = std::min(FILAS_POR_BLOQUE, FILAS - f);

        for (uint64_t r = 0; r < filas_en_este_bloque; ++r) {
            unsigned char* fila_ptr = &bloque[r * BYTES_POR_FILA];

            for (uint64_t byte_idx = 0; byte_idx < BYTES_POR_FILA; ++byte_idx) {
                unsigned char byte_actual = 0;
                // Empacamos 8 celdas (bits) dentro de un solo byte
                for (int b = 0; b < 8; ++b) {
                    int valor = bit(generador);          // 0 o 1
                    byte_actual |= (valor << (7 - b));    // lo ubicamos en su posición
                }
                fila_ptr[byte_idx] = byte_actual;
            }
        }

        // Escribimos el bloque completo de una vez (menos llamadas al disco)
        archivo.write(reinterpret_cast<char*>(bloque),
                       filas_en_este_bloque * BYTES_POR_FILA);

        if ((f / FILAS_POR_BLOQUE) % 20 == 0) {
            std::cout << "  fila " << (f + filas_en_este_bloque) << " / " << FILAS << "\n";
        }
    }

    archivo.close();

    auto fin = std::chrono::steady_clock::now();
    double segundos = std::chrono::duration<double>(fin - inicio).count();

    std::cout << "\nListo en " << segundos << " s\n";
}

// "Mostrar" la matriz: no se puede imprimir todo, así que leemos una pequeña
// submatriz (5x5) directamente del archivo, sin cargarlo completo a memoria.
void mostrar_muestra(int filas_muestra = 5, int columnas_muestra = 40) {
    std::ifstream archivo(NOMBRE_ARCHIVO, std::ios::binary);
    if (!archivo) {
        std::cerr << "No se pudo abrir el archivo para leer.\n";
        return;
    }

    std::cout << "\nMuestra (" << filas_muestra << " filas x "
              << columnas_muestra << " celdas):\n";

    // Buffer estático suficiente para una fila de muestra
    static unsigned char buffer_muestra[BYTES_POR_FILA];

    for (int r = 0; r < filas_muestra; ++r) {
        // Nos posicionamos al inicio de la fila r, sin leer nada antes
        archivo.seekg(r * BYTES_POR_FILA, std::ios::beg);

        // Solo necesitamos los primeros bytes para mostrar columnas_muestra bits
        int bytes_necesarios = (columnas_muestra + 7) / 8;
        archivo.read(reinterpret_cast<char*>(buffer_muestra), bytes_necesarios);

        for (int c = 0; c < columnas_muestra; ++c) {
            unsigned char byte_actual = buffer_muestra[c / 8];
            int bit_valor = (byte_actual >> (7 - (c % 8))) & 1;
            std::cout << bit_valor;
        }
        std::cout << "\n";
    }
}

int main() {
    generar_matriz();

    // Evidencia de que el archivo quedó bien: tamaño esperado vs real
    uint64_t tamano_esperado = FILAS * BYTES_POR_FILA;
    std::cout << "Tamano esperado: " << (tamano_esperado / 1e9) << " GB\n";

    mostrar_muestra();

    return 0;
}