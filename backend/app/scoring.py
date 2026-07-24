"""Puntaje de la votación (etapa 2): todos los videos candidatos compiten a la vez
(no hay enfrentamientos 1 vs 1). Puntaje final por video = cantidad de jurados que lo
eligieron + 1 si ganó el voto del público (0 si no, incluyendo un empate en el máximo -
ver _punto_publico)."""
from collections import Counter


def _punto_publico(conteo_publico: Counter) -> str | None:
    """El video con más votos del público se lleva el punto único. Si dos o más
    candidatos empatan en el máximo, nadie se lleva el punto (default acordado con el
    organizador ante la ausencia de un criterio de desempate manual)."""
    if not conteo_publico:
        return None
    max_votos = max(conteo_publico.values())
    ganadores = [video for video, votos in conteo_publico.items() if votos == max_votos]
    return ganadores[0] if len(ganadores) == 1 else None


def compute_resultados(
    votos_publico: list[str], votos_jurado: list[str], candidatos: list[str]
) -> dict[str, dict]:
    """`votos_publico`/`votos_jurado` son las elecciones (video_choice) ya extraídas de
    las filas de Salesforce; `candidatos` son los video_choice de todos los videos en
    competencia. Devuelve, por cada candidato, el desglose y el puntaje final."""
    conteo_publico = Counter(votos_publico)
    conteo_jurado = Counter(votos_jurado)
    video_ganador_publico = _punto_publico(conteo_publico)

    resultados = {}
    for video_choice in candidatos:
        votos_jurado_video = conteo_jurado.get(video_choice, 0)
        punto_publico = 1 if video_choice == video_ganador_publico else 0
        resultados[video_choice] = {
            "votos_jurado": votos_jurado_video,
            "votos_publico": conteo_publico.get(video_choice, 0),
            "punto_publico": punto_publico,
            "puntaje_final": votos_jurado_video + punto_publico,
        }
    return resultados
