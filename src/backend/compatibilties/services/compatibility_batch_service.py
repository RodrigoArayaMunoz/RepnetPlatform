import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable, Iterable

from config import settings
from services.compatibility_service import JobMetrics, WRITE_RATE_LIMITER, call_ml
from services.ml_client import ml_client
from services.product_cache_service import ProductCacheService

logger = logging.getLogger(__name__)


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm(value) -> str:
    return _safe_text(value).lower()


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


async def get_item_compact_cached(
    *,
    access_token: str,
    user_id: int | str,
    item_id: str,
    metrics: JobMetrics,
) -> dict:
    cached = ProductCacheService.get_item_compact(item_id)
    if cached:
        logger.info("[BATCH][CACHE_HIT] item_id=%s", item_id)
        return cached

    logger.info("[BATCH][CACHE_MISS] item_id=%s -> consultando item detail", item_id)
    item_detail = await call_ml(
        ml_client.get_item_detail,
        access_token,
        item_id,
        user_id=user_id,
        metrics=metrics,
    )

    compact = {
        "item_id": item_id,
        "category_id": item_detail.get("category_id"),
        "user_product_id": item_detail.get("user_product_id"),
    }
    ProductCacheService.set_item_compact(item_id, compact)
    return compact


async def post_compatibility_row(
    *,
    access_token: str,
    user_id: int | str,
    row: dict,
    metrics: JobMetrics,
) -> dict:
    item_id = str(row.get("item_id") or "")
    product_id = str(row.get("product_id") or "")

    if not row.get("ok") or not item_id or not product_id:
        return {
            "ok": False,
            "item_id": item_id,
            "product_id": product_id,
            "excel_row_index": row.get("excel_row_index"),
            "error_code": "MISSING_ITEM_DATA",
            "error_message": "No se obtuvo category_id o user_product_id",
            "response": None,
        }

    item_compact = await get_item_compact_cached(
        access_token=access_token,
        user_id=user_id,
        item_id=item_id,
        metrics=metrics,
    )

    category_id = item_compact.get("category_id")
    user_product_id = item_compact.get("user_product_id")

    if not category_id or not user_product_id:
        logger.error(
            "[ROW_POST][ERROR] item_id=%s sin category_id o user_product_id",
            item_id,
        )
        return {
            "ok": False,
            "item_id": item_id,
            "product_id": product_id,
            "excel_row_index": row.get("excel_row_index"),
            "error_code": "MISSING_ITEM_DATA",
            "error_message": "No se obtuvo category_id o user_product_id",
            "response": None,
        }

    logger.info(
        "[ROW_POST][POST] excel_row=%s item_id=%s user_product_id=%s product_id=%s",
        row.get("excel_row_index"),
        item_id,
        user_product_id,
        product_id,
    )

    response = await call_ml(
        ml_client.add_user_product_compatibility,
        access_token=access_token,
        user_product_id=str(user_product_id),
        category_id=str(category_id),
        product_id=str(product_id),
        creation_source="DEFAULT",
        user_id=user_id,
        metrics=metrics,
        limiter=WRITE_RATE_LIMITER,
    )

    logger.info(
        "[ROW_POST][OK] excel_row=%s item_id=%s user_product_id=%s product_id=%s",
        row.get("excel_row_index"),
        item_id,
        user_product_id,
        product_id,
    )

    return {
        "ok": True,
        "item_id": item_id,
        "product_id": product_id,
        "excel_row_index": row.get("excel_row_index"),
        "user_product_id": str(user_product_id),
        "category_id": str(category_id),
        "response": response,
    }

#def build_grouped_product_ids(rows: list[dict]) -> dict[str, list[str]]:
    #grouped: dict[str, set[str]] = defaultdict(set)

    #for row in rows:
        #item_id = row.get("item_id")
        #product_id = row.get("product_id")
        #ok = row.get("ok")

        #if not item_id or not product_id or not ok:
            #continue

        #grouped[str(item_id)].add(str(product_id))

    #return {
        #item_id: sorted(list(product_ids))
        #for item_id, product_ids in grouped.items()
    #}

async def post_compatibilities_batch(
    *,
    access_token: str,
    user_id: int | str,
    item_id: str,
    product_ids: list[str],
    metrics: JobMetrics,
) -> dict:
    item_compact = await get_item_compact_cached(
        access_token=access_token,
        user_id=user_id,
        item_id=item_id,
        metrics=metrics,
    )

    category_id = item_compact.get("category_id")
    user_product_id = item_compact.get("user_product_id")

    if not category_id or not user_product_id:
        logger.error(
            "[BATCH][ERROR] item_id=%s sin category_id o user_product_id",
            item_id,
        )
        return {
            "ok": False,
            "item_id": item_id,
            "product_ids": product_ids,
            "error_code": "MISSING_ITEM_DATA",
            "error_message": "No se obtuvo category_id o user_product_id",
            "response": None,
        }

    batch_size = min(200, max(1, int(getattr(settings, "compat_batch_size", 200))))
    product_ids = [str(pid) for pid in product_ids][:batch_size]

    logger.info(
        "[BATCH][POST] item_id=%s user_product_id=%s products_sent=%s",
        item_id,
        user_product_id,
        len(product_ids),
    )

    response = await call_ml(
        ml_client.add_user_product_compatibilities_batch,
        access_token=access_token,
        user_product_id=str(user_product_id),
        category_id=str(category_id),
        product_ids=product_ids,
        creation_source="DEFAULT",
        user_id=user_id,
        metrics=metrics,
        limiter=WRITE_RATE_LIMITER,
    )

    logger.info(
        "[BATCH][OK] item_id=%s user_product_id=%s products_sent=%s",
        item_id,
        user_product_id,
        len(product_ids),
    )

    return {
        "ok": True,
        "item_id": item_id,
        "user_product_id": str(user_product_id),
        "category_id": str(category_id),
        "products_sent_count": len(product_ids),
        "product_ids": product_ids,
        "response": response,
    }


def build_final_row_results(
    resolved_rows: list[dict],
    post_results: list[dict],
) -> list[dict]:
    result_by_pair_and_row: dict[tuple[str, str, int], dict] = {}

    for idx, post in enumerate(post_results):
        item_id = str(post.get("item_id") or "")
        product_id = str(post.get("product_id") or "")
        excel_row_index = post.get("excel_row_index", idx)
        result_by_pair_and_row[(item_id, product_id, excel_row_index)] = post

    final_rows: list[dict] = []

    for idx, row in enumerate(resolved_rows):
        item_id = str(row.get("item_id") or "")
        product_id = str(row.get("product_id") or "")
        excel_row_index = row.get("excel_row_index", idx)

        if not row.get("ok") or not product_id:
            final_rows.append(
                {
                    **row,
                    "ok": False,
                    "success_count": 0,
                    "error_count": 1,
                    "results": [
                        {
                            "ok": False,
                            "year": row.get("year"),
                            "reason": row.get("error_message", "No se pudo resolver product_id"),
                            "error_type": "functional",
                            "error_code": row.get("error_code", "PRODUCT_RESOLUTION_ERROR"),
                        }
                    ],
                }
            )
            continue

        post_result = result_by_pair_and_row.get((item_id, product_id, excel_row_index))

        if post_result and post_result.get("ok"):
            final_rows.append(
                {
                    **row,
                    "ok": True,
                    "success_count": 1,
                    "error_count": 0,
                    "year_requested": row.get("year"),
                    "year_processed": row.get("year"),
                    "results": [
                        {
                            "ok": True,
                            "year": row.get("year"),
                            "product_id": product_id,
                            "item_id": item_id,
                            "user_product_id": post_result.get("user_product_id"),
                            "category_id": post_result.get("category_id"),
                            "response": post_result.get("response"),
                        }
                    ],
                }
            )
        else:
            error_info = post_result or {
                "error_code": "MISSING_POST_CONFIRMATION",
                "error_message": "No se encontró confirmación del POST para esta fila",
            }
            final_rows.append(
                {
                    **row,
                    "ok": False,
                    "success_count": 0,
                    "error_count": 1,
                    "error_type": "technical",
                    "year_requested": row.get("year"),
                    "results": [
                        {
                            "ok": False,
                            "year": row.get("year"),
                            "reason": error_info.get("error_message"),
                            "error_type": "technical",
                            "error_code": error_info.get("error_code"),
                            "product_id": product_id,
                        }
                    ],
                }
            )

    return final_rows

def build_unique_compatibility_key(row: dict) -> str:
    item_id = _norm(row.get("item_id"))
    product_id = _norm(row.get("product_id"))

    if row.get("ok") and product_id:
        return f"ok::{item_id}::{product_id}"

    return "::".join(
        [
            "error",
            item_id,
            _norm(row.get("brand_name")),
            _norm(row.get("model_name")),
            _norm(row.get("version_name")),
            _norm(row.get("year") or row.get("year_requested") or row.get("year_processed")),
            _norm(row.get("engine_name")),
            _norm(row.get("transmission_name")),
            _norm(row.get("error_code") or row.get("reason")),
        ]
    )


def dedupe_final_rows(final_rows: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}

    for row in final_rows:
        key = build_unique_compatibility_key(row)

        if key not in deduped:
            copied = dict(row)
            copied["duplicate_count"] = 1
            deduped[key] = copied
            continue

        deduped[key]["duplicate_count"] = int(deduped[key].get("duplicate_count", 1)) + 1

    return list(deduped.values())


def build_compat_summary(final_rows: list[dict], post_results: list[dict], metrics: JobMetrics) -> dict:
    processed_rows = len(final_rows)
    rows_ok = sum(1 for r in final_rows if r.get("ok"))
    rows_error = processed_rows - rows_ok

    brands = len(
        {
            _norm(r.get("brand_name"))
            for r in final_rows
            if _safe_text(r.get("brand_name"))
        }
    )

    models = len(
        {
            f"{_norm(r.get('brand_name'))}::{_norm(r.get('model_name'))}"
            for r in final_rows
            if _safe_text(r.get("model_name"))
        }
    )

    functional_errors = sum(1 for r in final_rows if r.get("error_type") == "functional")
    technical_errors = sum(1 for r in final_rows if r.get("error_type") == "technical")

    return {
        "processed_rows": processed_rows,
        "total_rows": processed_rows,
        "excel_rows_processed": processed_rows,
        "success_count": rows_ok,
        "error_count": rows_error,
        "compatibilities_total": processed_rows,
        "compatibilities_ok": rows_ok,
        "compatibilities_error": rows_error,
        "functional_errors": functional_errors,
        "technical_errors": technical_errors,
        "brands": brands,
        "models": models,
        "items_count": len({str(r.get("item_id") or "") for r in final_rows if r.get("item_id")}),
        "post_count": len(post_results),
        "metrics": metrics.to_dict(),
    }

async def process_compatibility_batches(
    *,
    access_token: str,
    user_id: int | str,
    rows: list[dict],
    on_progress: Callable[[int, int], Awaitable[None]] | None = None,
) -> dict:
    metrics = JobMetrics()
    max_concurrency = max(1, int(getattr(settings, "compat_batch_concurrency", 4)))

    rows_to_process: list[dict] = []
    for idx, row in enumerate(rows):
        enriched = dict(row)
        enriched["excel_row_index"] = row.get("excel_row_index", idx + 2)
        rows_to_process.append(enriched)

    logger.info(
        "[ROW_POST][START] excel_rows=%s concurrency=%s",
        len(rows_to_process),
        max_concurrency,
    )

    semaphore = asyncio.Semaphore(max_concurrency)
    progress_lock = asyncio.Lock()
    completed = 0
    post_results: list[dict | None] = [None] * len(rows_to_process)

    async def worker(pos: int, row: dict) -> None:
        nonlocal completed

        async with semaphore:
            result = await post_compatibility_row(
                access_token=access_token,
                user_id=user_id,
                row=row,
                metrics=metrics,
            )
            post_results[pos] = result

            should_notify = False
            completed_snapshot = 0

            async with progress_lock:
                completed += 1
                completed_snapshot = completed
                should_notify = on_progress is not None

            logger.info(
                "[ROW_POST][PROGRESS] completed=%s/%s excel_row=%s item_id=%s product_id=%s ok=%s",
                completed_snapshot,
                len(rows_to_process),
                row.get("excel_row_index"),
                row.get("item_id"),
                row.get("product_id"),
                result.get("ok"),
            )

            if should_notify and on_progress is not None:
                try:
                    await on_progress(completed_snapshot, len(rows_to_process))
                except Exception:
                    logger.exception("[ROW_POST][WARN] fallo actualizando progreso")

    await asyncio.gather(*(worker(i, row) for i, row in enumerate(rows_to_process)))

    final_post_results = [
        r if r is not None else {
            "ok": False,
            "error_code": "MISSING_POST_RESULT",
            "error_message": "Resultado faltante del POST por fila",
            "item_id": "",
            "product_id": "",
        }
        for r in post_results
    ]

    final_rows = build_final_row_results(rows_to_process, final_post_results)
    summary = build_compat_summary(final_rows, final_post_results, metrics)

    logger.info(
        "[ROW_POST][END] excel_rows=%s ok=%s error=%s",
        summary["processed_rows"],
        summary["success_count"],
        summary["error_count"],
    )

    return {
        "results": final_rows,
        "post_results": final_post_results,
        "summary": summary,
    }