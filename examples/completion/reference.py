"""Reference consumer for the bounded, projected App Server fixture contract."""


def progress(events, context):
    """Return wait/continue/verify/failed; business acceptance belongs to the host."""
    ack = False
    compact_turn = compact_item = followup_turn = None
    item_done = False
    compact_status = followup_status = None
    for event in events:
        if event.get("id") == context["compact_request_id"]:
            if "error" in event:
                return "failed"
            ack = "result" in event
        if event.get("id") == context["followup_request_id"]:
            if "error" in event:
                return "failed"
            followup_turn = event["result"]["turn"]["id"]
        params = event.get("params", {})
        if params.get("threadId") != context["thread_id"]:
            continue
        method = event.get("method")
        item = params.get("item", {})
        if (method == "item/started" and item.get("type") == "contextCompaction"
                and params["turnId"] not in context["prior_turn_ids"] and compact_turn is None):
            compact_turn, compact_item = params["turnId"], item["id"]
        if (method == "item/completed" and compact_turn is not None
                and params["turnId"] == compact_turn and item.get("id") == compact_item
                and item.get("type") == "contextCompaction"):
            item_done = True
        if method == "turn/completed":
            turn = params["turn"]
            if compact_turn is not None and turn["id"] == compact_turn:
                compact_status = turn["status"]
            if followup_turn is not None and turn["id"] == followup_turn:
                followup_status = turn["status"]
    if compact_status in {"failed", "interrupted"} or followup_status in {"failed", "interrupted"}:
        return "failed"
    if not (ack and item_done and compact_status == "completed"):
        return "wait"
    if followup_turn is None:
        return "continue"
    return "verify" if followup_status == "completed" else "wait"
