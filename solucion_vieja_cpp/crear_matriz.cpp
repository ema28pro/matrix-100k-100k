#include <fstream>
#include <random>
#include <chrono>
#include <iostream>
#include <cstdint>


const uint64_t FILAS = 10;
const uint64_t COLUMNAS = 100000;
const uint64_t FILAS_POR_BLOQUE = 1000;
const uint64_t BYTES_POR_FILA = COLUMNAS / 8;
const uint64_t TAMANO_BLOQUE = FILAS_POR_BLOQUE * BYTES_POR_FILA; // 12.5 MB

const char* NOMBRE_ARCHIVO = "matriz_100k.bin";

// Buffer en memoria estática (segmento BSS)
static unsigned char bloque[TAMANO_BLOQUE];

void generar_matriz() {

    std::mt19937_64 generador(std::random_device{}());
    std::uniform_int_distribution<int> bit(0, 1);

    std::ofstream archivo(NOMBRE_ARCHIVO, std::ios::binary);
    if (!archivo) {
        std::cerr << "Error: No se pudo crear el archivo.\n";
        return;
    }

    // 1. Escribir Cabecera Autodescriptiva de 16 bytes (FILAS y COLUMNAS)
    archivo.write(reinterpret_cast<const char*>(&FILAS), sizeof(FILAS));
    archivo.write(reinterpret_cast<const char*>(&COLUMNAS), sizeof(COLUMNAS));

    std::cout << "Generando matriz de " << FILAS << " x " << COLUMNAS << "...\n";
    std::cout << "Destino: " << NOMBRE_ARCHIVO << "\n";
    std::cout << "Cabecera: 16 bytes (FILAS=" << FILAS << ", COLUMNAS=" << COLUMNAS << ")\n";
    std::cout << "Tamano por fila: " << BYTES_POR_FILA << " bytes\n";
    uint64_t tamano_esperado = sizeof(FILAS) + sizeof(COLUMNAS) + (FILAS * BYTES_POR_FILA);
    std::cout << "Tamano total esperado (con cabecera): " << (tamano_esperado / (1024.0 * 1024.0 * 1024.0)) << " GB\n\n";

    auto inicio = std::chrono::steady_clock::now();

    for (uint64_t f = 0; f < FILAS; f += FILAS_POR_BLOQUE) {
        uint64_t filas_en_este_bloque = std::min(FILAS_POR_BLOQUE, FILAS - f);

        for (uint64_t r = 0; r < filas_en_este_bloque; ++r) {
            unsigned char* fila_ptr = &bloque[r * BYTES_POR_FILA];

            for (uint64_t byte_idx = 0; byte_idx < BYTES_POR_FILA; ++byte_idx) {
                unsigned char byte_actual = 0;
                // Empaquetamos 8 celdas (bits) dentro de 1 byte
                for (int b = 0; b < 8; ++b) {
                    int valor = bit(generador);
                    byte_actual |= (valor << (7 - b));
                }
                fila_ptr[byte_idx] = byte_actual;
            }
        }

        // Escritura por bloque completo al disco
        archivo.write(reinterpret_cast<char*>(bloque),
                      filas_en_este_bloque * BYTES_POR_FILA);

        if ((f / FILAS_POR_BLOQUE) % 20 == 0) {
            std::cout << "  Progreso: fila " << (f + filas_en_este_bloque) << " / " << FILAS << "\n";
        }
    }

    archivo.close();

    auto fin = std::chrono::steady_clock::now();
    double segundos = std::chrono::duration<double>(fin - inicio).count();

    std::cout << "\nMatriz guardada con exito en '" << NOMBRE_ARCHIVO << "' (" << segundos << " s)\n";
}

int main() {
    generar_matriz();
    return 0;
}
