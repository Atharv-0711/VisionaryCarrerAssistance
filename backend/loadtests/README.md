# Load Testing

Use Locust to tune cache TTL, pagination caps, and rate limits under realistic traffic.

## Install

```bash
pip install locust
```

## Run

```bash
locust -f backend/loadtests/locustfile.py --host http://localhost:5000
```

If authenticated endpoints are enabled, pass:

```bash
LOADTEST_AUTH_TOKEN=<token> locust -f backend/loadtests/locustfile.py --host http://localhost:5000
```

## Tuning targets

- Keep p95 response time for read endpoints under 500ms.
- Keep error rate under 1% at expected peak users.
- Reduce cache miss ratio by increasing `ANALYTICS_CACHE_TTL_SECONDS` carefully.
- Control query pressure with `ANALYTICS_MAX_PAGE_SIZE`.
- Prevent abuse and cascading failures with request/window caps.
