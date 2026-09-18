import pandas as pd
import json
import math
import os
import re

NIVEL_MIN = 1
NIVEL_MAX = 50


def encontrar_fila_cabecera(ruta_csv):
    with open(ruta_csv, "r", encoding="utf-8", errors="ignore") as f:
        for idx, linea in enumerate(f):
            if "Nickname" in linea or "Full Name" in linea or "nick" in linea.lower():
                return idx
            if idx > 10:
                break
    return 0


def cargar_aliases(ruta_aliases):
    """preferred_id -> juego_nick (o lista de nicks CSV a probar)."""
    if not ruta_aliases or not os.path.exists(ruta_aliases):
        return {}
    with open(ruta_aliases, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for pref, val in raw.items():
        if isinstance(val, list):
            out[pref] = [str(v) for v in val]
        else:
            out[pref] = [str(val)]
    return out


def nicks_csv_para(preferred, aliases):
    """Nicks del CSV asociados a un ID preferido (incluye el propio ID)."""
    extras = aliases.get(preferred, [])
    vistos = []
    for n in [preferred, *extras]:
        if n not in vistos:
            vistos.append(n)
    return vistos


def normalizar_nivel(crudo):
    """Escala natural (como juego 1): floor(Lv/2), acotado a 1–50."""
    if "event" in crudo.lower():
        return "Evento"
    try:
        valor = int(float(crudo))
        return max(NIVEL_MIN, min(NIVEL_MAX, math.floor(valor / 2)))
    except ValueError:
        return "Evento"


def resolver_eventos(procesados):
    n_movs = len(procesados)
    for idx in range(n_movs):
        if procesados[idx]["level"] != "Evento":
            continue

        if idx == 0:
            procesados[idx]["level"] = NIVEL_MIN
        elif idx == n_movs - 1:
            procesados[idx]["level"] = NIVEL_MAX
        else:
            nivel_prev = procesados[idx - 1]["level"]
            nivel_next = None

            for j in range(idx + 1, n_movs):
                if procesados[j]["level"] != "Evento":
                    nivel_next = procesados[j]["level"]
                    break

            if nivel_next is None:
                nivel_next = NIVEL_MAX

            procesados[idx]["level"] = math.floor((nivel_prev + nivel_next) / 2)


def movimientos_de_fila(fila, df_columns):
    movimientos_jugador = []
    for i in range(1, 5):
        col_mov = f"Move {i}"
        col_niv = f"Move {i} Level"

        if col_mov in df_columns and col_niv in df_columns:
            nombre_mov = str(fila[col_mov]).strip()
            nivel_mov = str(fila[col_niv]).strip().replace("Lv.", "").strip()

            if nombre_mov and nombre_mov.lower() not in ["nan", "none", "", "null"]:
                movimientos_jugador.append({"name": nombre_mov, "raw_lvl": nivel_mov})

    procesados = [
        {"move": m["name"], "level": normalizar_nivel(m["raw_lvl"])}
        for m in movimientos_jugador
    ]
    resolver_eventos(procesados)
    return procesados


def procesar_ie3(ruta_csv, nicks_preferidos, aliases=None):
    if not os.path.exists(ruta_csv):
        print(f"Advertencia: Archivo {ruta_csv} no encontrado.")
        return {}

    aliases = aliases or {}
    fila_cabecera = encontrar_fila_cabecera(ruta_csv)

    try:
        df = pd.read_csv(
            ruta_csv, header=fila_cabecera, sep=None, engine="python", encoding="utf-8"
        )
    except Exception as e:
        print(f"Error al leer {ruta_csv}: {e}")
        return {}

    columnas_limpias = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    columnas_finales = []
    movimiento_actual = None
    for col in columnas_limpias:
        if col.startswith("Move "):
            movimiento_actual = col
            columnas_finales.append(col)
        elif col.startswith("Learns at") and movimiento_actual is not None:
            columnas_finales.append(f"{movimiento_actual} Level")
        else:
            columnas_finales.append(col)

    df.columns = columnas_finales

    if "Nickname" not in df.columns:
        encontrado = False
        for c in df.columns:
            if "nick" in c.lower() or "name" in c.lower():
                df.rename(columns={c: "Nickname"}, inplace=True)
                encontrado = True
                break

        if not encontrado:
            print(f"\nERROR en {ruta_csv}: No se encontró la columna 'Nickname'.")
            print(f"Columnas detectadas: {list(df.columns)}\n")
            return {}

    df["Nickname"] = df["Nickname"].astype(str).str.strip()

    # Índice: nick CSV -> primera fila (versión principal si hay duplicados)
    por_nick_csv = {}
    duplicados = []
    for _, fila in df.iterrows():
        nick = fila["Nickname"]
        if nick in por_nick_csv:
            duplicados.append(nick)
            continue
        por_nick_csv[nick] = fila

    if duplicados:
        unicos = sorted(set(duplicados))
        print(
            f"Aviso: {len(unicos)} nicks duplicados en el CSV (se usa la 1ª fila): "
            f"{', '.join(unicos[:15])}" + ("..." if len(unicos) > 15 else "")
        )

    resultados = {}
    for preferred in nicks_preferidos:
        fila = None
        for csv_nick in nicks_csv_para(preferred, aliases):
            if csv_nick in por_nick_csv:
                fila = por_nick_csv[csv_nick]
                break
        if fila is None:
            continue
        movimientos = movimientos_de_fila(fila, df.columns)
        if movimientos:
            resultados[preferred] = movimientos

    return resultados


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archivo_csv = os.path.join(base_dir, "data", "raw", "juego3.csv")
    archivo_nicks = os.path.join(base_dir, "data", "raw", "nicks_ie3.txt")
    archivo_aliases = os.path.join(base_dir, "data", "raw", "nicks_ie3_aliases.json")
    archivo_salida = os.path.join(base_dir, "data", "processed", "movimientos_ie3.json")

    if not os.path.exists(archivo_nicks):
        print(
            f"Error: Debes crear el archivo '{archivo_nicks}' con los nicks (uno por línea)."
        )
        return

    with open(archivo_nicks, "r", encoding="utf-8-sig") as f:
        nicks_permitidos = [linea.strip() for linea in f if linea.strip()]

    if not nicks_permitidos:
        print(f"Error: '{archivo_nicks}' está vacío. Añade un nick por línea.")
        return

    aliases = cargar_aliases(archivo_aliases)
    print(
        f"Se encontraron {len(nicks_permitidos)} nicks para filtrar "
        f"({len(aliases)} con alias CSV)."
    )
    print("Procesando IE3...")
    datos = procesar_ie3(archivo_csv, nicks_permitidos, aliases)

    json_final = {}
    no_encontrados = []
    sin_moves = []
    for nick in nicks_permitidos:
        if nick in datos and datos[nick]:
            json_final[nick] = datos[nick]
        elif nick in datos:
            sin_moves.append(nick)
        else:
            no_encontrados.append(nick)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)

    print(f"\nProceso finalizado! {len(json_final)} jugadores en '{archivo_salida}'.")
    if no_encontrados:
        print(
            f"Sin correspondencia CSV para {len(no_encontrados)} nicks: "
            f"{', '.join(no_encontrados[:20])}"
            + ("..." if len(no_encontrados) > 20 else "")
        )
    if sin_moves:
        print(f"Sin supertécnicas para {len(sin_moves)} nicks: {', '.join(sin_moves)}")


if __name__ == "__main__":
    main()
