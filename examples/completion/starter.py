"""Intentionally wrong: treats RPC acceptance as permission to continue."""


def progress(events, context):
    # Repair this function using the exercise contract in chapter 10.
    # It must never return a business-success verdict.
    for event in events:
        if event.get("id") == context["compact_request_id"] and "result" in event:
            return "continue"
    return "wait"
