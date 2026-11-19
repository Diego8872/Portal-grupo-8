"""Capa de proveedores de IA. Hoy: Groq. Para sumar Anthropic se agrega otra clase y se registra en PROVEEDORES."""
import base64
import json
import re
import time

import requests


class LLMError(Exception):
    pass


def _parse_json(texto: str) -> dict:
    texto = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S).strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.M).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMError(f"La IA no devolvió un JSON válido: {texto[:200]}")


class Proveedor:
    nombre = "base"

    def extraer_json(self, instrucciones: str, contenido: str = "", imagenes: list | None = None) -> dict:
        """Devuelve un dict. `imagenes` = lista de bytes JPEG (documentos escaneados)."""
        raise NotImplementedError


class Groq(Proveedor):
    """Groq con selección automática de modelo.

    Groq retira modelos seguido (llama-3.3-70b-versatile y llama-4-scout ya fueron dados de baja). Por eso:
    - se consulta /models y se usa el primero disponible de cada lista de preferencia;
    - si un modelo responde "no existe", se prueba el siguiente;
    - se pueden forzar modelos con los secrets GROQ_MODEL_TEXT / GROQ_MODEL_VISION.
    """
    nombre = "groq"
    URL = "https://api.groq.com/openai/v1"
    TEXTO = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    VISION = ["qwen/qwen3.8-27b", "meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"]
    _NO_EXISTE = ("model_not_found", "model_decommissioned", "does not exist", "decommissioned", "no longer supported")

    def __init__(self, api_key: str, modelo_texto: str = "", modelo_vision: str = ""):
        if not api_key:
            raise LLMError("Falta GROQ_API_KEY")
        self.api_key = api_key
        self.modelo_texto, self.modelo_vision = modelo_texto.strip(), modelo_vision.strip()
        self.ultimo_modelo = None
        self._disponibles = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def disponibles(self) -> list:
        """IDs de modelos que la cuenta puede usar ([] si no se pudo consultar)."""
        if self._disponibles is None:
            try:
                r = requests.get(f"{self.URL}/models", headers=self._headers(), timeout=20)
                self._disponibles = [m["id"] for m in r.json().get("data", [])] if r.status_code == 200 else []
            except Exception:
                self._disponibles = []
        return self._disponibles

    def candidatos(self, vision: bool) -> list:
        forzado = self.modelo_vision if vision else self.modelo_texto
        if forzado:
            return [forzado]
        pref, disp = (self.VISION if vision else self.TEXTO), self.disponibles()
        ok = [m for m in pref if m in disp]
        return ok or pref

    def _post(self, payload: dict) -> requests.Response:
        for intento in range(4):
            r = requests.post(f"{self.URL}/chat/completions", json=payload, headers=self._headers(), timeout=120)
            if r.status_code in (429, 500, 502, 503) and intento < 3:
                time.sleep(min(float(r.headers.get("retry-after", 2 ** (intento + 1))), 25))
                continue
            return r
        return r

    def _llamar(self, modelo: str, mensajes: list) -> requests.Response:
        """Llama al modelo; si rechaza algún parámetro opcional (400), lo quita y reintenta."""
        extra = {}
        if modelo.startswith("openai/gpt-oss"):
            extra["reasoning_effort"] = "medium"
        elif modelo.startswith("qwen/"):
            extra["reasoning_effort"] = "none"
        base = {"model": modelo, "messages": mensajes, "temperature": 0, "max_completion_tokens": 4000}
        variantes = [{**extra, "response_format": {"type": "json_object"}},
                     {"response_format": {"type": "json_object"}}, {}]
        for v in variantes:
            r = self._post({**base, **v})
            if r.status_code != 400:
                return r
        return r

    def extraer_json(self, instrucciones, contenido="", imagenes=None):
        if imagenes:
            partes = [{"type": "text", "text": instrucciones}]
            for img in imagenes:
                partes.append({"type": "image_url",
                               "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img).decode()}})
            mensajes = [{"role": "user", "content": partes}]
        else:
            mensajes = [
                {"role": "system", "content": "Respondés únicamente con un objeto JSON válido, sin texto adicional."},
                {"role": "user", "content": f"{instrucciones}\n\n=== DOCUMENTO ===\n{contenido}"},
            ]
        ultimo_error = ""
        for modelo in self.candidatos(bool(imagenes)):
            r = self._llamar(modelo, mensajes)
            if r.status_code == 200:
                self.ultimo_modelo = modelo
                return _parse_json(r.json()["choices"][0]["message"]["content"])
            ultimo_error = f"{modelo} -> Groq {r.status_code}: {r.text[:250]}"
            if r.status_code in (400, 404) and any(t in r.text.lower() for t in self._NO_EXISTE):
                continue  # ese modelo ya no existe: se prueba el siguiente
            break
        raise LLMError(ultimo_error or "Groq no respondió")


PROVEEDORES = {"groq": Groq}


def get_proveedor(nombre: str, api_key: str, **opciones) -> Proveedor:
    return PROVEEDORES[nombre](api_key, **opciones)
