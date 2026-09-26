"""Monthly cost projection for the deployed project, compared with a spending target.

Usage comes from Cloud Monitoring (billable Cloud Run instance time, request counts,
stored bytes, Storage operations) over recent whole days, scaled to an average month.
Prices are list prices from the Cloud Billing Catalog for us-central1. Free allowances
are shared by every project on a billing account, so two projections are reported: one
where this project gets the whole allowance and one where other projects have used it.
Neither includes taxes, credits, or discounts; the billing console is authoritative.
"""

DAYS_PER_MONTH = 30.44
GIB = 1024 ** 3
# List prices checked in the Cloud Billing Catalog on 2026-09-26 (USD).
PRICES = {
    "run_cpu_second": 0.000024,        # Services CPU (Request-based billing)
    "run_gib_second": 0.0000025,       # Services Memory (Request-based billing)
    "run_request": 0.0000004,          # Requests, after 2 million a month
    "storage_gib_month": 0.02,         # Standard Storage US Regional, after 5 GiB
    "class_a": 0.000005,               # Regional Standard Class A, after 5,000
    "class_b": 0.0000004,              # Regional Standard Class B, after 50,000
    "registry_gib_month": 0.10,        # Artifact Registry storage, after 0.5 GiB
    "scheduler_job": 0.10,             # Cloud Scheduler job, after 3 per billing account
}
# Free allowances per billing account per month. The Cloud Run CPU and memory allowances
# are applied as free-tier credits rather than catalog tiers (see docs/CLOUD.md).
FREE = {
    "run_cpu_second": 180_000,
    "run_gib_second": 360_000,
    "run_request": 2_000_000,
    "storage_gib_month": 5,
    "class_a": 5_000,
    "class_b": 50_000,
    "registry_gib_month": 0.5,
    "scheduler_job": 3,
}
# Storage JSON API methods billed as Class A; other object and bucket reads are Class B.
CLASS_A = {"WriteObject", "ListObjects", "ComposeObject", "CopyObject", "RewriteObject",
           "UpdateObjectMetadata", "PatchObject", "ListBuckets", "InsertObject",
           "UpdateBucketMetadata", "CreateBucket", "RestoreObject"}


def monthly(per_day):
    return per_day * DAYS_PER_MONTH


def usage(services, stored_bytes, requests_by_method, registry_bytes, scheduler_jobs=1):
    """Monthly quantities from daily measurements.

    ``services`` maps a service to {"instance_seconds_per_day", "requests_per_day",
    "vcpu", "gib"}; ``stored_bytes`` is the current billable total across buckets (live,
    noncurrent, and soft-deleted); ``requests_by_method`` holds daily operation counts.
    """
    cpu = sum(monthly(s["instance_seconds_per_day"]) * s["vcpu"] for s in services.values())
    mem = sum(monthly(s["instance_seconds_per_day"]) * s["gib"] for s in services.values())
    class_a = sum(n for method, n in requests_by_method.items() if method in CLASS_A)
    class_b = sum(n for method, n in requests_by_method.items() if method not in CLASS_A)
    return {
        "run_cpu_second": cpu,
        "run_gib_second": mem,
        "run_request": sum(monthly(s["requests_per_day"]) for s in services.values()),
        "storage_gib_month": stored_bytes / GIB,
        "class_a": monthly(class_a),
        "class_b": monthly(class_b),
        "registry_gib_month": registry_bytes / GIB,
        "scheduler_job": scheduler_jobs,
    }


def cost(quantities, *, free=True):
    """Dollar cost per item, with or without this project receiving the free allowances."""
    return {item: round(max(0.0, amount - (FREE[item] if free else 0)) * PRICES[item], 4)
            for item, amount in quantities.items()}


def project(quantities, target):
    with_free, without_free = cost(quantities, free=True), cost(quantities, free=False)
    return {
        "quantities": {k: round(v, 3) for k, v in quantities.items()},
        "free_allowance_used": {k: round(quantities[k] / FREE[k], 3) for k in quantities},
        "cost_with_free_allowances": with_free,
        "cost_without_free_allowances": without_free,
        "total_with_free_allowances": round(sum(with_free.values()), 2),
        "total_without_free_allowances": round(sum(without_free.values()), 2),
        "target": target,
        "within_target_either_way": sum(without_free.values()) < target,
        "within_target_with_free_allowances": sum(with_free.values()) < target,
    }
