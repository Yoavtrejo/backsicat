import json
import os
from typing import Any

import requests

MAX_VALUE_CHARS = 2000
MAX_PROMPT_CHARS = 24000

def _resolve_llm_config() -> tuple[str, str, str]:
    """
    Devuelve (api_key, base_url, model).
    Prioridad de clave: LLM_API_KEY > DEEPSEEK_API_KEY > OPENAI_API_KEY.
    Si defines DEEPSEEK_API_KEY y no pones URL, se usa https://api.deepseek.com/v1 .
    """
    key = (
        (os.environ.get("LLM_API_KEY") or "").strip()
        or (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
        or (os.environ.get("OPENAI_API_KEY") or "").strip()
    )

    explicit_base = (
        (os.environ.get("LLM_API_BASE") or os.environ.get("OPENAI_API_BASE") or "").strip().rstrip("/")
    )
    model = (os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL") or "").strip()

    has_deepseek_var = bool((os.environ.get("DEEPSEEK_API_KEY") or "").strip())

    if explicit_base:
        base = explicit_base
    elif has_deepseek_var:
        base = "https://api.deepseek.com/v1"
    else:
        base = "https://api.openai.com/v1"

    if not model:
        if "deepseek.com" in base.lower():
            model = "deepseek-chat"
        else:
            model = "gpt-4o-mini"

    return key, base, model


def _truncate_value(val: Any) -> Any:
    if isinstance(val, str) and len(val) > MAX_VALUE_CHARS:
        return val[: MAX_VALUE_CHARS - 3] + "..."
    if isinstance(val, (list, dict)):
        s = json.dumps(val, ensure_ascii=False)
        if len(s) > MAX_VALUE_CHARS:
            return s[: MAX_VALUE_CHARS - 3] + "..."
    return val


def sanitize_properties(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        if v is None:
            continue
        key = str(k)[:120]
        out[key] = _truncate_value(v)
    return out


def _send_chat(messages: list[dict], *, temperature: float = 0.3, max_tokens: int = 700) -> str:
    api_key, base_url, model = _resolve_llm_config()
    if not api_key:
        raise RuntimeError(
            "No hay clave de IA. Para DeepSeek usa DEEPSEEK_API_KEY=sk-... en el .env "
            "(o LLM_API_KEY). Opcional: LLM_MODEL=deepseek-chat."
        )

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = requests.post(url, headers=headers, json=body, timeout=90)
    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise RuntimeError(f"Error del proveedor de IA ({resp.status_code}): {err}")

    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Respuesta vacía del proveedor de IA.")
    content = (choices[0].get("message") or {}).get("content") or ""
    content = content.strip()
    if not content:
        raise RuntimeError("El modelo no devolvió texto.")
    return content


def explain_spatial_element(
    nombre_capa: str | None,
    categoria: str | None,
    properties: dict,
) -> str:
    props = sanitize_properties(properties)
    user_payload = {
        "nombre_capa": nombre_capa or None,
        "categoria": categoria or None,
        "atributos": props,
    }
    user_text = json.dumps(user_payload, ensure_ascii=False, indent=2)
    if len(user_text) > MAX_PROMPT_CHARS:
        user_text = user_text[: MAX_PROMPT_CHARS - 20] + "\n… (truncado)"

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente técnico para cartografía y ordenamiento territorial en México. "
                "Explica en español, de forma clara y breve (máximo 120 palabras), qué representa "
                "este elemento geoespacial y qué destacan sus atributos más relevantes para un "
                "usuario técnico. No inventes datos: solo usa lo que aparece en los atributos. "
                "Si faltan datos clave, indícalo sin especular."
            ),
        },
        {
            "role": "user",
            "content": user_text,
        },
    ]

    return _send_chat(messages, temperature=0.4, max_tokens=400)


def _to_plain_phase_stats(fases: list[dict]) -> dict[str, int]:
    total = len(fases)
    completed = sum(1 for f in fases if isinstance(f, dict) and bool(f.get("completada")))
    pending = max(total - completed, 0)
    return {"total": total, "completadas": completed, "pendientes": pending}


def build_report_context(
    *,
    estado: str | None = None,
    municipio: str | None = None,
    proyecto_id: int | None = None,
    capa_ids: list[int] | None = None,
) -> dict:
    from projects.models import Proyecto
    from upload_fields.models import CapaGeografica

    proyectos_qs = Proyecto.objects.all()
    if estado:
        proyectos_qs = proyectos_qs.filter(estado__icontains=estado)
    if municipio:
        proyectos_qs = proyectos_qs.filter(municipio__icontains=municipio)
    if proyecto_id:
        proyectos_qs = proyectos_qs.filter(id=proyecto_id)

    capas_qs = CapaGeografica.objects.all()
    if estado:
        capas_qs = capas_qs.filter(estado__icontains=estado)
    if municipio:
        capas_qs = capas_qs.filter(municipio__icontains=municipio)
    if capa_ids:
        capas_qs = capas_qs.filter(id__in=capa_ids)

    proyectos = list(proyectos_qs.order_by("-fecha_creacion")[:20])
    capas = list(capas_qs.order_by("-fecha_subida")[:40])

    resumen_proyectos = []
    for p in proyectos:
        fases = p.fases if isinstance(p.fases, list) else []
        resumen_proyectos.append(
            {
                "id": p.id,
                "folio": p.folio,
                "nombre": p.nombre_proyecto,
                "ubicacion": {"estado": p.estado, "municipio": p.municipio},
                "categoria": p.categoria,
                "escala": p.tipo_escala,
                "avance": float(p.avance),
                "fases": _to_plain_phase_stats(fases),
            }
        )

    categorias_capas: dict[str, int] = {}
    tipos_geometria: dict[str, int] = {}
    capas_resumen = []
    for c in capas:
        categorias_capas[c.categoria] = categorias_capas.get(c.categoria, 0) + 1
        tipos_geometria[c.tipo_geometria] = tipos_geometria.get(c.tipo_geometria, 0) + 1
        feature_count = 0
        if isinstance(c.datos_normalizados, dict):
            features = c.datos_normalizados.get("features")
            if isinstance(features, list):
                feature_count = len(features)
        capas_resumen.append(
            {
                "id": c.id,
                "nombre_capa": c.nombre_capa,
                "categoria": c.categoria,
                "tipo_geometria": c.tipo_geometria,
                "estado": c.estado,
                "municipio": c.municipio,
                "feature_count": feature_count,
            }
        )

    return {
        "filtros": {
            "estado": estado or None,
            "municipio": municipio or None,
            "proyecto_id": proyecto_id,
            "capa_ids": capa_ids or [],
        },
        "metricas": {
            "total_proyectos": len(resumen_proyectos),
            "total_capas": len(capas_resumen),
            "capas_por_categoria": categorias_capas,
            "capas_por_geometria": tipos_geometria,
        },
        "proyectos": resumen_proyectos,
        "capas": capas_resumen,
    }


def generate_report_text(context: dict, tono: str = "ejecutivo") -> str:
    payload = json.dumps(context, ensure_ascii=False, indent=2)
    if len(payload) > MAX_PROMPT_CHARS:
        payload = payload[: MAX_PROMPT_CHARS - 20] + "\n… (truncado)"

    style = (
        "lenguaje formal, orientado a toma de decisiones"
        if tono == "ejecutivo"
        else "lenguaje técnico geoespacial y operativo"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Eres analista senior de proyectos cartográficos. "
                "Redacta informes en español, sin inventar datos y con base estricta en el contexto entregado. "
                "Estructura en secciones Markdown: Resumen Ejecutivo, Hallazgos, Riesgos/Datos faltantes, "
                "Recomendaciones, Próximos pasos."
            ),
        },
        {
            "role": "user",
            "content": f"Genera un informe en tono {style} con este contexto:\n{payload}",
        },
    ]
    return _send_chat(messages, temperature=0.25, max_tokens=900)
