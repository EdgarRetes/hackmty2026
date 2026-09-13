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

from core.risk_engine import predict_risk
from facturas.models import Invoice
from mercado.matching_engine import opportunity_summary, rank_offers

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
    "directo, como lo sería un asesor financiero real."
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
        .select_related("debtor_client")
        .order_by("due_date")
    )


def _build_tools(company):
    """
    Closures over `company` so the model never has to supply a company id
    (and can't accidentally query another company's data) — the functions'
    signatures only expose the arguments Gemini should actually decide.
    """

    def listar_facturas_disponibles() -> list[dict]:
        """Lista las facturas pendientes de la empresa que aún no se han publicado ni tienen financiamiento. Para cada una incluye su cliente, sector, monto, días para vencer, riesgo estimado y una cotización estimada (tasa y efectivo neto) si se financiara hoy sola.

        Returns:
            Una lista de facturas con: invoice_id, folio, cliente, sector, monto, dias_para_vencer, riesgo, tasa_estimada_pct, efectivo_neto_estimado.
        """
        today = timezone.now().date()
        results = []
        for invoice in _pending_invoices(company):
            summary = opportunity_summary(invoice)
            best_quote = rank_offers(invoice)[0]
            results.append(
                {
                    "invoice_id": invoice.id,
                    "folio": f"FAC-2026-{invoice.id:04d}",
                    "cliente": invoice.debtor_client.name,
                    "sector": summary["sector"],
                    "monto": str(invoice.amount),
                    "dias_para_vencer": (invoice.due_date - today).days,
                    "riesgo": summary["risk"],
                    "tasa_estimada_pct": summary["estimated_return_rate"],
                    "efectivo_neto_estimado": best_quote["net_amount"],
                }
            )
        return results

    def detalle_factura(invoice_id: int) -> dict:
        """Da el detalle completo de una factura pendiente: predicción de riesgo (días de atraso p10/p50/p90) y la cotización de cada una de las 3 financiadoras disponibles (conservadora, agresiva, especializada), con su porcentaje de anticipo, tasa y efectivo neto.

        Args:
            invoice_id: El id numérico de la factura.
        """
        try:
            invoice = Invoice.objects.select_related("debtor_client").get(
                pk=invoice_id, company=company
            )
        except Invoice.DoesNotExist:
            return {"error": f"No se encontró la factura {invoice_id} para esta empresa."}

        risk = predict_risk(invoice)
        return {
            "invoice_id": invoice.id,
            "cliente": invoice.debtor_client.name,
            "monto": str(invoice.amount),
            "riesgo_dias_atraso": {"p10": risk["p10"], "p50": risk["p50"], "p90": risk["p90"]},
            "cotizaciones": rank_offers(invoice),
        }

    def simular_paquete(invoice_ids: list[int]) -> dict:
        """Simula juntar dos o más facturas pendientes de esta empresa en una sola publicación (paquete) y calcula, para cada financiadora, el resultado combinado: efectivo neto total, tasa promedio ponderada por monto y porcentaje de anticipo promedio. No publica nada, solo calcula.

        Args:
            invoice_ids: Lista de ids de las facturas a combinar (al menos 2 para que tenga sentido simular un paquete).
        """
        invoices = list(
            Invoice.objects.filter(pk__in=invoice_ids, company=company).select_related(
                "debtor_client"
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
            for quote in rank_offers(invoice):
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

    return [listar_facturas_disponibles, detalle_factura, simular_paquete]


def chat(company, message, history=None):
    """
    One turn of the assistant conversation. `history` is the prior
    turns as [{"role": "user"|"model", "text": str}, ...] — the frontend
    keeps and resends it, so this stays stateless on the backend.
    """
    client = genai.Client(api_key=_key())

    contents = []
    for turn in history or []:
        role = "model" if turn.get("role") == "model" else "user"
        text = (turn.get("text") or "").strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=_build_tools(company),
    )
    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return response.text
