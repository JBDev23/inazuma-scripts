import cloudscraper
from bs4 import BeautifulSoup
import os
import sys
import io  # Librería nativa para manejar datos en memoria
from PIL import Image  # La nueva librería para procesar imágenes

# Windows (cp1252) no puede imprimir emojis; forzar UTF-8 en la consola
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 1. Mapa de URLs: Relaciona el nombre corto de tu lista con el enlace real de la wiki
urls_equipos = {
    "Raimon": "https://inazuma.fandom.com/es/wiki/Instituto_Raimon",
    "Occult": "https://inazuma.fandom.com/es/wiki/Instituto_Occult",
    "Kirkwood": "https://inazuma.fandom.com/es/wiki/Instituto_Kirkwood",
    "Wild": "https://inazuma.fandom.com/es/wiki/Instituto_Wild",
    "Brainwashing": "https://inazuma.fandom.com/es/wiki/Instituto_Brain",
    "Otaku": "https://inazuma.fandom.com/es/wiki/Instituto_Otaku",
    "Shuriken": "https://inazuma.fandom.com/es/wiki/Instituto_Shuriken",
    "Zeus": "https://inazuma.fandom.com/es/wiki/Instituto_Zeus",
    "Royal-Academy": "https://inazuma.fandom.com/es/wiki/Royal_Academy",
    "Umbrella": "https://inazuma.fandom.com/es/wiki/Instituto_Umbrella",
    "Raimon-Old-Boys": "https://inazuma.fandom.com/es/wiki/Inazuma_Eleven_(equipo)",
    "Farm": "https://inazuma.fandom.com/es/wiki/Instituto_Farm",
    "Alpine": "https://inazuma.fandom.com/es/wiki/Instituto_Alpino",
    "Cloister-Divinity": "https://inazuma.fandom.com/es/wiki/Instituto_Claustro_Sagrado",
    "Royal-Academy-Redux": "https://inazuma.fandom.com/es/wiki/Royal_Academy_Redux",
    "Triple-C": "https://inazuma.fandom.com/es/wiki/Triple_C_de_Osaka",
    "Fauxshore": "https://inazuma.fandom.com/es/wiki/Instituto_Fauxshore",
    "Mary-Times-Memorial": "https://inazuma.fandom.com/es/wiki/Instituto_Mary_Times_Memorial",
    "Secret-Service": "https://inazuma.fandom.com/es/wiki/Servicio_Secreto",
    "Gemini-Storm": "https://inazuma.fandom.com/es/wiki/Tormenta_de_G%C3%A9minis",
    "Epsilon": "https://inazuma.fandom.com/es/wiki/%C3%89psilon",
    "The-Genesis": "https://inazuma.fandom.com/es/wiki/G%C3%A9nesis",
    "Prominence": "https://inazuma.fandom.com/es/wiki/Prominence",
    "Diamond-Dust": "https://inazuma.fandom.com/es/wiki/Diamond",
    "Caos": "https://inazuma.fandom.com/es/wiki/Caos",
    "Dark-Emperors": "https://inazuma.fandom.com/es/wiki/Emperadores_Oscuros",
    "Inazuma-Japan": "https://inazuma.fandom.com/es/wiki/Inazuma_Jap%C3%B3n",
    "Big-Waves": "https://inazuma.fandom.com/es/wiki/Big_Waves",
    "Desert-Lion": "https://inazuma.fandom.com/es/wiki/Leones_del_Desierto",
    "Fire-Dragon": "https://inazuma.fandom.com/es/wiki/Dragones_de_Fuego",
    "Knights-of-Queen": "https://inazuma.fandom.com/es/wiki/Knights_of_Queen",
    "The-Empire": "https://inazuma.fandom.com/es/wiki/Los_Emperadores",
    "Unicorn": "https://inazuma.fandom.com/es/wiki/Unicorn",
    "Orpheus": "https://inazuma.fandom.com/es/wiki/Orfeo",
    "Os-Reis": "https://inazuma.fandom.com/es/wiki/Os_Reis",
    "Little-Gigant": "https://inazuma.fandom.com/es/wiki/The_Little_Giants",
    "Team-K": "https://inazuma.fandom.com/es/wiki/Equipo_D",
    "Team-Garshield": "https://inazuma-eleven.fandom.com/wiki/Team_Garshield",
    "Red-Matador": "https://inazuma.fandom.com/es/wiki/Los_Rojos",
    "Rose-Griffon": "https://inazuma.fandom.com/es/wiki/Grifos_de_la_Rosa",
    "The-Great-Horn": "https://inazuma.fandom.com/es/wiki/Caimanes_del_Cabo",
    "Tenkuu-no-Shito": "https://inazuma.fandom.com/es/wiki/Sky_Team",
    "Makai-Gundan-Z": "https://inazuma.fandom.com/es/wiki/Dark_Team",
}

# 2. Leer tu archivo de texto y organizar los datos
equipos_jugadores = {}

print("📂 Leyendo el archivo jugadores.txt...")
with open("jugadores.txt", "r", encoding="utf-8") as archivo:
    for linea in archivo:
        if linea.strip():
            partes = linea.strip().split()
            equipo = partes[0]
            jugador = partes[1]

            if equipo not in equipos_jugadores:
                equipos_jugadores[equipo] = []
            equipos_jugadores[equipo].append(jugador)

# 3. Preparar el scraper antibloqueos
scraper = cloudscraper.create_scraper()

# 4. Iterar por cada equipo y descargar los sprites
for equipo, jugadores in equipos_jugadores.items():
    print("\n=====================================")
    print(f"🌐 Procesando equipo: {equipo}")
    print("=====================================")

    url_equipo = urls_equipos.get(equipo)
    if not url_equipo:
        print(
            f"❌ Falta la URL de {equipo} en el diccionario 'urls_equipos'. Saltando..."
        )
        continue

    carpeta_destino = f"sprites_{equipo.lower()}"
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    respuesta = scraper.get(url_equipo)

    if respuesta.status_code == 200:
        soup = BeautifulSoup(respuesta.text, "html.parser")
        print(f"✅ Página descargada. Buscando {len(jugadores)} jugadores...")

        for jugador in jugadores:
            imagen_tag = soup.find("img", alt=lambda x: x and jugador in x)

            if imagen_tag:
                url_imagen = imagen_tag.get("data-src") or imagen_tag.get("src")

                if url_imagen:
                    # Descargamos los bytes de la imagen original (ej: PNG)
                    img_data = scraper.get(url_imagen).content

                    try:
                        # 🔄 MAGIA DE CONVERSIÓN AQUÍ:
                        # 1. Cargamos los bytes en un "archivo virtual" en memoria usando io.BytesIO
                        # 2. Abrimos la imagen con Pillow
                        imagen = Image.open(io.BytesIO(img_data))

                        # 3. Definimos la nueva ruta con extensión .webp
                        ruta_archivo = f"{carpeta_destino}/{jugador}.webp"

                        # 4. Guardamos la imagen especificando el formato 'WEBP'
                        imagen.save(ruta_archivo, "WEBP")
                        print(f"  ✨ Sprite convertido -> {jugador}.webp")

                    except Exception as e:
                        print(
                            f"  ❌ Error al procesar/convertir la imagen de {jugador}: {e}"
                        )
                else:
                    print(f"  ⚠️ Etiqueta para {jugador} encontrada sin URL.")
            else:
                print(f"  ❌ No se encontró el sprite para {jugador}.")
    else:
        print(f"❌ Error al acceder a {url_equipo} (Código {respuesta.status_code})")

print(
    "\n¡Proceso terminado con éxito! Revisa tus carpetas, ahora todos tus sprites son .webp"
)
