# Edge cases — review checklist

For every new or changed entry point (endpoint, handler, job, component, ViewModel action), walk the
inputs and states below. Report only cases that can **really** happen here, with the concrete input
and the wrong result. Silent wrong data outranks a loud crash.

## Inputs
- null / missing / empty string / whitespace / empty list / zero / negative.
- Boundaries: first/last element, max length, page size, `int` overflow, decimal precision and rounding.
- Duplicates: same id twice in a request, same event delivered twice.
- Unexpected format: casing, accents and non-ASCII, leading zeros, trailing spaces, culture-specific
  decimal separator, very large payloads.
- Unknown enum/status value coming from an upstream that evolves.

## Time
- Time zone: UTC vs local business zone, server zone differing from the business zone.
- DST change days, midnight, end of month, leap year, `today` computed twice in one flow.
- Comparing dates with times, inclusive vs exclusive ranges, clock skew between systems.

## State and concurrency
- Two requests/users updating the same record — lost update, missing optimistic concurrency.
- Check-then-act races (exists? → insert), shared static or singleton state, caches.
- Stale cache after a write; cache key missing a discriminator (tenant, culture, filter).
- Re-run or retry of a job/handler: is it idempotent? partial writes left behind?
- Cancellation mid-operation: resources released, half-written state?

## Integrations
- Upstream down, slow (timeout), 4xx, 5xx, empty body, partial page, schema change.
- Pagination: last page, empty page, item added/removed between pages.
- Transaction boundaries across two systems — one succeeds, the other fails.
- Rate limits and large result sets loaded fully into memory.

## UI (React / Android)
- Loading, empty, error and success states all rendered; double submit; back navigation mid-request.
- Rotation / process death / unmount while a request is in flight (stale setState, leaked collector).
- Very long text, no network, slow network, permission denied.

## Security-adjacent
- Authorisation on the new path (not only authentication); id from the client trusted for ownership.
- Personal data in logs, error messages or responses; secrets in config or code.
- User input reaching SQL, file paths, URLs, shell or HTML unescaped.
