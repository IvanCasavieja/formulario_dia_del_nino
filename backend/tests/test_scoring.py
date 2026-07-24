from app.scoring import compute_resultados


def test_ejemplo_del_prompt_jurado_unanime_y_publico_gana():
    # 5 jurados votan A, público vota más por A que por B -> A = 5 + 1 = 6, B = 0 + 0 = 0
    resultados = compute_resultados(
        votos_publico=["A"] * 10 + ["B"] * 8,
        votos_jurado=["A"] * 5,
        candidatos=["A", "B"],
    )
    assert resultados["A"] == {"votos_jurado": 5, "votos_publico": 10, "punto_publico": 1, "puntaje_final": 6}
    assert resultados["B"] == {"votos_jurado": 0, "votos_publico": 8, "punto_publico": 0, "puntaje_final": 0}


def test_empate_de_publico_no_otorga_el_punto_a_nadie():
    resultados = compute_resultados(
        votos_publico=["A", "A", "B", "B"],
        votos_jurado=["A"],
        candidatos=["A", "B"],
    )
    assert resultados["A"]["punto_publico"] == 0
    assert resultados["B"]["punto_publico"] == 0
    assert resultados["A"]["puntaje_final"] == 1  # solo el punto de jurado
    assert resultados["B"]["puntaje_final"] == 0


def test_jurado_dividido_reparte_puntos_entre_varios_videos():
    resultados = compute_resultados(
        votos_publico=["A"],
        votos_jurado=["A", "B", "B", "C"],
        candidatos=["A", "B", "C"],
    )
    assert resultados["A"]["puntaje_final"] == 1 + 1  # 1 jurado + gana público (único voto)
    assert resultados["B"]["puntaje_final"] == 2  # 2 jurados, no gana público
    assert resultados["C"]["puntaje_final"] == 1  # 1 jurado, no gana público


def test_sin_votos_todavia_da_puntaje_cero_para_todos():
    resultados = compute_resultados(votos_publico=[], votos_jurado=[], candidatos=["A", "B"])
    assert resultados["A"] == {"votos_jurado": 0, "votos_publico": 0, "punto_publico": 0, "puntaje_final": 0}
    assert resultados["B"] == {"votos_jurado": 0, "votos_publico": 0, "punto_publico": 0, "puntaje_final": 0}
