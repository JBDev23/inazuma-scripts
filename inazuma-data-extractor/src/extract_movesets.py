import pandas as pd
import json
import math
import os
import re


def encontrar_fila_cabecera(ruta_csv):
    with open(ruta_csv, "r", encoding="utf-8", errors="ignore") as f:
        for idx, linea in enumerate(f):
            if "Nickname" in linea or "Full Name" in linea or "nick" in linea.lower():
                return idx
            if idx > 10:
                break
    return 0


def cargar_aliases(ruta_aliases):
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
    extras = aliases.get(preferred, [])
    vistos = []
    for n in [preferred, *extras]:
        if n not in vistos:
            vistos.append(n)
    return vistos


def procesar_juego(
    ruta_csv, num_juego, nicks_permitidos, nicks_con_offset=None, aliases=None
):
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

    por_nick_csv = {}
    for _, fila in df.iterrows():
        nick = fila["Nickname"]
        if nick not in por_nick_csv:
            por_nick_csv[nick] = fila

    resultados = {}
    for preferred in nicks_permitidos:
        fila = None
        for csv_nick in nicks_csv_para(preferred, aliases):
            if csv_nick in por_nick_csv:
                fila = por_nick_csv[csv_nick]
                break
        if fila is None:
            continue

        movimientos_jugador = []
        for i in range(1, 5):
            col_mov = f"Move {i}"
            col_niv = f"Move {i} Level"

            if col_mov in df.columns and col_niv in df.columns:
                nombre_mov = str(fila[col_mov]).strip()
                nivel_mov = str(fila[col_niv]).strip().replace("Lv.", "").strip()

                if nombre_mov and nombre_mov.lower() not in ["nan", "none", "", "null"]:
                    movimientos_jugador.append(
                        {"name": nombre_mov, "raw_lvl": nivel_mov}
                    )

        usa_offset = (
            num_juego == 2
            and nicks_con_offset is not None
            and preferred in nicks_con_offset
        )

        procesados = []
        for m in movimientos_jugador:
            nombre = m["name"]
            crudo = m["raw_lvl"]

            if "event" in crudo.lower():
                nivel_final = "Evento"
            else:
                try:
                    valor = int(float(crudo))
                    if usa_offset:
                        nivel_final = max(26, math.floor(valor / 4) + 25)
                    else:
                        nivel_final = max(1, math.floor(valor / 2))
                except ValueError:
                    nivel_final = "Evento"

            procesados.append({"move": nombre, "level": nivel_final})

        n_movs = len(procesados)
        nivel_min = 26 if usa_offset else 1
        nivel_max = 50 if usa_offset else 25
        for idx in range(n_movs):
            if procesados[idx]["level"] == "Evento":
                if idx == 0:
                    procesados[idx]["level"] = nivel_min
                elif idx == n_movs - 1:
                    procesados[idx]["level"] = nivel_max
                else:
                    nivel_prev = procesados[idx - 1]["level"]
                    nivel_next = None

                    for j in range(idx + 1, n_movs):
                        if procesados[j]["level"] != "Evento":
                            nivel_next = procesados[j]["level"]
                            break

                    if nivel_next is None:
                        nivel_next = nivel_max

                    procesados[idx]["level"] = math.floor((nivel_prev + nivel_next) / 2)

        resultados[preferred] = procesados

    return resultados


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    archivo_juego1 = os.path.join(base_dir, "data", "raw", "juego1.csv")
    archivo_juego2 = os.path.join(base_dir, "data", "raw", "juego2.csv")
    archivo_nicks = os.path.join(base_dir, "data", "raw", "nicks.txt")
    archivo_aliases = os.path.join(base_dir, "data", "raw", "nicks_aliases.json")
    archivo_salida = os.path.join(
        base_dir, "data", "processed", "movimientos_combinados.json"
    )

    if not os.path.exists(archivo_nicks):
        print(
            f"Error: Debes crear el archivo '{archivo_nicks}' con los nicks de los jugadores."
        )
        return

    with open(archivo_nicks, "r", encoding="utf-8-sig") as f:
        nicks_permitidos = [linea.strip() for linea in f if linea.strip()]

    aliases = cargar_aliases(archivo_aliases)
    print(
        f"Se encontraron {len(nicks_permitidos)} nicks para filtrar "
        f"({len(aliases)} con alias CSV)."
    )

    print("Procesando Juego 1...")
    datos_juego1 = procesar_juego(archivo_juego1, 1, nicks_permitidos, aliases=aliases)

    print("Procesando Juego 2...")
    datos_juego2 = procesar_juego(
        archivo_juego2,
        2,
        nicks_permitidos,
        nicks_con_offset=set(datos_juego1.keys()),
        aliases=aliases,
    )

    print("Combinando datos y eliminando duplicados...")
    json_final = {}
    no_encontrados = []

    for nick in nicks_permitidos:
        combinados = []
        vistos = set()

        if nick in datos_juego1:
            for mov in datos_juego1[nick]:
                nombre_minuscula = mov["move"].lower()
                if nombre_minuscula not in vistos:
                    combinados.append(mov)
                    vistos.add(nombre_minuscula)

        if nick in datos_juego2:
            for mov in datos_juego2[nick]:
                nombre_minuscula = mov["move"].lower()
                if nombre_minuscula not in vistos:
                    combinados.append(mov)
                    vistos.add(nombre_minuscula)

        if combinados:
            json_final[nick] = combinados
        else:
            no_encontrados.append(nick)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)

    print(f"\nProceso finalizado! {len(json_final)} jugadores en '{archivo_salida}'.")
    if no_encontrados:
        print(
            f"Sin datos para {len(no_encontrados)} nicks: {', '.join(no_encontrados)}"
        )


if __name__ == "__main__":
    main()
