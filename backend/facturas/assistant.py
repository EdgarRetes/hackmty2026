"""
Gemini-powered assistant that helps a Company decide which of its pending
invoices to bundle into one publicación. It has tool access to the same
risk engine + pricing agents + matching engine every other endpoint uses —
it never invents numbers, it calls real functions against the real DB.

The key comes from the GEMINI_API_KEY env var — never hardcode it, never
log it, never include it in an exception message. See core/nessie_client.py
for the same convention applied to another third-party key.
"""

import os
from decimal import Decimal

from django.utils import timezone
from google import genai
from google.genai import types

from core.risk_engine import assess_invoice
from facturas.models import Invoice, RiskAssessment
from mercado.matching_engine import opportunity_summary, rank_offers

from .services import publish_invoices

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")

SYSTEM_INSTRUCTION = (
    "Eres el asistente de factoraje de Factora para una PyME mexicana. Tu "
    "trabajo es ayudar al dueño de la empresa a decidir qué facturas "
    "pendientes de cobro le conviene juntar en una sola publicación para "
    "venderla a una financiadora. Usa siempre tus herramientas para "
    "consultar los datos reales de la empresa — nunca inventes montos, "
    "tasas ni niveles de riesgo. Explica tus recomendaciones con números "
    "concretos (monto, tasa estimada, efectivo neto, riesgo) en pesos "
    "mexicanos, compara opciones cuando tenga sentido, y sé breve y "
    "directo, como lo sería un asesor financiero real. Cada factura pasa "
    "primero por un underwriting automático (aprobada/revisión/rechazada); "
    "nunca recomiendes juntar una factura que no esté aprobada, y explica "
    "la razón si el usuario pregunta por qué una no calificó. Cuando el "
    "usuario elija una de tus opciones o te pida explícitamente publicarla "
    "(por ejemplo \"quiero la opción 1\", \"publícala\", \"hazlo\"), usa la "
    "herramienta publicar_paquete con esos invoice_id exactos — no le "
    "pidas que lo haga él mismo, tú puedes publicarla directamente. "
    "Confirma siempre qué publicaste y con qué facturas."
)


def _key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
    return key


def _pending_invoices(company):
    return (
        Invoice.objects.filter(
            company=company, status=Invoice.Status.PENDING, batch__isnull=True
        )
        .select_related("debtor_client", "company")
        .order_by("due_date")
    )


def _json_safe_quotes(quotes):
    """
    rank_offers() includes an internal `annual_rate` Decimal (used only to
    compute the other, already-stringified fields) that DRF's Response
    knows how to encode but google-genai's plain json.dumps does not —
    strip it before handing a quote list back to the model.
    """
    return [{key: value for key, value in quote.items() if key != "annual_rate"} for quote in quotes]


def _latest_assessment(invoice):
    """
    Reuse the invoice's latest underwriting decision when one already
    exists (same pattern as matching_engine.opportunity_summary) instead
    of persisting a fresh RiskAssessment row on every assistant query —
    the assistant reads a lot more often than it writes.
    """
    assessment = invoice.risk_assessments.order_by("-created_at").first()
    if assessment is None:
        assessment = assess_invoice(invoice)
    return assessment


def _build_tools(company, published):
    """
    Closures over `company` so the model never has to supply a company id
    (and can't accidentally query another company's data) — the functions'
    signatures only expose the arguments Gemini should actually decide.

    `published` is a list the publish tool appends to on success, so
    `chat()` can tell the caller a real publication was created this turn
    without having to parse it back out of the model's prose reply.
    """

    def listar_facturas_disponibles() -> list[dict]:
        """Lista las facturas pendientes de la empresa que aún no se han publicado ni tienen financiamiento. Para cada una incluye su cliente, sector, monto, días para vencer, riesgo estimado y, si ya pasó el underwriting automático, una cotización estimada (tasa y efectivo neto) si se financiara hoy sola. Las facturas que no pasaron el underwriting se marcan como no elegibles y no deben recomendarse para publicar.

        Returns:
            Una lista de facturas con: invoice_id, folio, cliente, sector, monto, dias_para_vencer, riesgo, elegible, motivo_no_elegible, tasa_estimada_pct, efectivo_neto_estimado.
        """
        today = timezone.now().date()
        results = []
        for invoice in _pending_invoices(company):
            assessment = _latest_assessment(invoice)
            summary = opportunity_summary(invoice)
            quotes = rank_offers(invoice, assessment)
            elegible = assessment.decision == RiskAssessment.Decision.APPROVE
            results.append(
                {
                    "invoice_id": invoice.id,
                    "folio": f"FAC-2026-{invoice.id:04d}",
                    "cliente": invoice.debtor_client.name,
                    "sector": summary["sector"],
                    "monto": str(invoice.amount),
                    "dias_para_vencer": (invoice.due_date - today).days,
                    "riesgo": summary["risk"],
                    "elegible": elegible,
                    "motivo_no_elegible": None if elegible else list(assessment.reasons),
                    "tasa_estimada_pct": summary["estimated_return_rate"] if elegible else None,
                    "efectivo_neto_estimado": quotes[0]["net_amount"] if quotes else None,
                }
            )
        return results

    def detalle_factura(invoice_id: int) -> dict:
        """Da el detalle completo de una factura pendiente: el resultado del underwriting automático (decisión, calificación, score de riesgo, probabilidad de incumplimiento, razones y advertencias) y, si fue aprobada, la cotización de las 3 financiadoras disponibles (conservadora, agresiva, especializada) con su porcentaje de anticipo, tasa y efectivo neto.

        Args:
            invoice_id: El id numérico de la factura.
        """
        try:
            invoice = Invoice.objects.select_related("debtor_client", "company").get(
                pk=invoice_id, company=company
            )
        except Invoice.DoesNotExist:
            return {"error": f"No se encontró la factura {invoice_id} para esta empresa."}

        assessment = _latest_assessment(invoice)
        return {
            "invoice_id": invoice.id,
            "cliente": invoice.debtor_client.name,
            "monto": str(invoice.amount),
            "underwriting": {
                "decision": assessment.decision,
                "calificacion": assessment.rating,
                "riesgo_score": str(assessment.risk_score),
                "probabilidad_incumplimiento_pct": str(assessment.probability_of_default * 100),
                "razones": list(assessment.reasons),
                "advertencias": list(assessment.warnings),
            },
            "cotizaciones": _json_safe_quotes(rank_offers(invoice, assessment)),
        }

    def simular_paquete(invoice_ids: list[int]) -> dict:
        """Simula juntar dos o más facturas pendientes de esta empresa en una sola publicación (paquete) y calcula, para cada financiadora, el resultado combinado: efectivo neto total, tasa promedio ponderada por monto y porcentaje de anticipo promedio. Si alguna factura del paquete no pasa el underwriting automático, la publicación completa se rechazaría (así funciona el endpoint real), así que se reporta el error en vez de un cálculo parcial. No publica nada, solo calcula.

        Args:
            invoice_ids: Lista de ids de las facturas a combinar (al menos 2 para que tenga sentido simular un paquete).
        """
        invoices = list(
            Invoice.objects.filter(pk__in=invoice_ids, company=company).select_related(
                "debtor_client", "company"
            )
        )
        missing = set(invoice_ids) - {invoice.id for invoice in invoices}
        if missing:
            return {"error": f"Estas facturas no existen o no son de esta empresa: {sorted(missing)}"}
        if not invoices:
            return {"error": "No se dieron facturas válidas."}

        buckets = {}
        for invoice in invoices:
            amount = Decimal(str(invoice.amount))
            assessment = _latest_assessment(invoice)
            if assessment.decision != RiskAssessment.Decision.APPROVE:
                return {
                    "error": (
                        f"La publicación se rechazaría completa: la factura {invoice.id} "
                        f"no pasó el underwriting automático."
                    ),
                    "invoice_id": invoice.id,
                    "razones": list(assessment.reasons),
                }
            for quote in rank_offers(invoice, assessment):
                lender_id = quote["lender"]["id"]
                bucket = buckets.setdefault(
                    lender_id,
                    {
                        "lender": quote["lender"]["name"],
                        "net_amount": Decimal("0"),
                        "weighted_rate": Decimal("0"),
                        "weighted_advance": Decimal("0"),
                        "total_amount": Decimal("0"),
                    },
                )
                bucket["net_amount"] += Decimal(quote["net_amount"])
                bucket["weighted_rate"] += Decimal(quote["rate"]) * amount
                bucket["weighted_advance"] += Decimal(quote["advance_percentage"]) * amount
                bucket["total_amount"] += amount

        aggregated = []
        for bucket in buckets.values():
            total = bucket["total_amount"]
            aggregated.append(
                {
                    "financiadora": bucket["lender"],
                    "efectivo_neto_total": str(bucket["net_amount"].quantize(Decimal("0.01"))),
                    "tasa_promedio_pct": str((bucket["weighted_rate"] / total).quantize(Decimal("0.01"))),
                    "porcentaje_anticipo_promedio": str(
                        (bucket["weighted_advance"] / total).quantize(Decimal("0.01"))
                    ),
                }
            )
        aggregated.sort(key=lambda a: Decimal(a["efectivo_neto_total"]), reverse=True)

        total_amount = sum((Decimal(str(invoice.amount)) for invoice in invoices), Decimal("0"))
        return {
            "facturas_incluidas": len(invoices),
            "monto_total": str(total_amount),
            "mejores_ofertas_por_financiadora": aggregated,
        }

    def publicar_paquete(invoice_ids: list[int]) -> dict:
        """Publica de verdad, ahora mismo, una publicación con las facturas indicadas — exactamente lo mismo que si el usuario le diera clic a "Publicar" en la pantalla de Facturas. Úsala solo cuando el usuario haya elegido una opción concreta o pida explícitamente publicar/confirmar. Una vez publicada, la publicación queda visible para las financiadoras y las facturas dejan de estar disponibles para otro paquete.

        Args:
            invoice_ids: Lista de ids de las facturas a publicar juntas (1 o más).
        """
        batch, error = publish_invoices(invoice_ids, company=company)
        if error:
            return {"error": error}
        published.append(batch.id)
        return {
            "publicado": True,
            "batch_id": batch.id,
            "folio": f"PUB-{batch.id:04d}",
            "invoice_ids": list(invoice_ids),
        }

    return [listar_facturas_disponibles, detalle_factura, simular_paquete, publicar_paquete]


def chat(company, message, history=None):
    """
    One turn of the assistant conversation. `history` is the prior
    turns as [{"role": "user"|"model", "text": str}, ...] — the frontend
    keeps and resends it, so this stays stateless on the backend.

    Returns {"reply": str, "published_batch_id": int | None} — the id is
    set when the model actually called publicar_paquete successfully
    during this turn, so the frontend can link to / refresh around it
    without having to parse the model's prose.
    """
    client = genai.Client(api_key=_key())

    contents = []
    for turn in history or []:
        role = "model" if turn.get("role") == "model" else "user"
        text = (turn.get("text") or "").strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    published = []
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=_build_tools(company, published),
    )
    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return {
        "reply": response.text,
        "published_batch_id": published[-1] if published else None,
    }
