<div align="center">
  <img src="./docs/logo.png" alt="Inazuma Eleven Endavant Logo" width="full"/>
  
  <h1>Inazuma Eleven Endavant: Scripts de Datos</h1>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" />
    <img src="https://img.shields.io/badge/BeautifulSoup-00599C?style=for-the-badge&logo=python&logoColor=white" alt="BeautifulSoup" />
    <img src="https://img.shields.io/badge/Pillow-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Pillow" />
  </p>
</div>

Bienvenido al repositorio de **Scripts de Datos**, una herramienta backend complementaria dentro del ecosistema de **Inazuma Eleven Endavant**. 

Mientras que la plataforma web principal gestiona la economía, el progreso RPG y los partidos de chapas, este repositorio contiene los scripts encargados de extraer, procesar y normalizar toda la inmensa base de datos del juego (estadísticas, movimientos, rostros) desde diversas fuentes, dejándola lista para alimentar el motor del torneo.

---

## 🏗️ Estructura del Repositorio

Este repositorio contiene dos subproyectos clave relacionados con el procesamiento y extracción de datos de Inazuma Eleven:

### 1. Inazuma Data Extractor (`inazuma-data-extractor/`)
Un conjunto de scripts en Python (`src/`) destinados a parsear y limpiar datos estadísticos, de movimientos y alineaciones desde diferentes fuentes de datos (CSVs, HTML).

* **Tecnologías**: Python.
* **Instalación**: 
  ```bash
  pip install -r inazuma-data-extractor/requirements.txt
  ```
* **Uso**: 
  Los scripts esperan encontrar los datos crudos en la carpeta `data/raw/` y escribirán los datos procesados en `data/processed/` o generarán archivos adicionales dentro de `data/raw/`.

### 2. Inazuma Scrapper (`inazuma-scrapper/`)
Un script especializado para descargar sprites (imágenes) de los jugadores directamente desde la wiki de Inazuma Eleven.

* **Tecnologías**: Python, Cloudscraper, Pillow.
* **Instalación**: 
  ```bash
  pip install -r inazuma-scrapper/requirements.txt
  ```
* **Características Clave**:
  * Usa `cloudscraper` para evadir bloqueos básicos y protecciones antibot.
  * Convierte las imágenes descargadas al formato optimizado `.webp` utilizando `Pillow`.
* **Uso**:
  Para ejecutarlo, navega a la carpeta del proyecto y ejecuta el scraper:
  ```bash
  python scraper.py
  ```

---

## 🔗 Integración en el Ecosistema Híbrido

Estos scripts desempeñan un papel invisible pero crucial para la plataforma:

1. **Recolección en Crudo**: El _Scrapper_ recupera visualmente todos los personajes necesarios de las wikis de la saga, mientras que el _Data Extractor_ unifica estadísticas de distintas entregas.
2. **Normalización**: Se procesan estas bases de datos combinando y comparando técnicas para crear un _lore_ balanceado, normalizado y unificado adaptado a nuestro propio motor de juego físico (Fútbol Chapas).
3. **Carga Inicial (Seeding)**: Los datos resultantes se inyectan en el backend en NestJS y la base de datos PostgreSQL principal para poblar el mercado web de jugadores y calcular los duelos del árbitro digital.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - mira el archivo [LICENSE](LICENSE) para más detalles.
