import os
import sys
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from Modelo.Model import Partida


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("PINPOINT_SECRET", "clave-local-pinpoint")

partidas: dict[str, Partida] = {}


def obtener_partida() -> Partida | None:
    partida_id = session.get("partida_id")
    return partidas.get(partida_id) if partida_id else None


def serializar_pista(pista):
    if pista is None:
        return None
    return {"texto": pista.texto, "relacion": pista.relacion}


def respuesta_partida(partida: Partida, pista=None):
    return jsonify({
        "estado": partida.obtener_estado(),
        "pista": serializar_pista(pista),
    })


@app.get("/")
def inicio():
    return send_from_directory(ROOT / "Vista", "index.html")


@app.post("/api/iniciar")
def iniciar():
    datos = request.get_json(silent=True) or {}
    idioma = datos.get("idioma", "spa")

    if idioma not in ("spa", "eng"):
        return jsonify({"error": "El idioma debe ser 'spa' o 'eng'."}), 400

    try:
        partida = Partida()
        partida.iniciar_juego(idioma)
    except (RuntimeError, LookupError, ValueError) as error:
        return jsonify({"error": str(error)}), 503

    partida_id = str(uuid.uuid4())
    partidas[partida_id] = partida
    session["partida_id"] = partida_id
    return respuesta_partida(partida, partida.obtener_pista())


@app.post("/api/pista")
def pista():
    partida = obtener_partida()
    if partida is None:
        return jsonify({"error": "No hay una partida iniciada."}), 404
    return respuesta_partida(partida, partida.obtener_pista())


@app.post("/api/responder")
def responder():
    partida = obtener_partida()
    if partida is None:
        return jsonify({"error": "No hay una partida iniciada."}), 404

    datos = request.get_json(silent=True) or {}
    respuesta = datos.get("respuesta", "")
    if not isinstance(respuesta, str) or not respuesta.strip():
        return jsonify({"error": "La respuesta no puede estar vacía."}), 400

    correcta = partida.verificar_respuesta(respuesta)
    return jsonify({
        "correcta": correcta,
        "estado": partida.obtener_estado(),
    })


if __name__ == "__main__":
    app.run(debug=True)