


def _extract_text_from_response(resp_json):
    """
    Robustly extract textual content from Bedrock/Anthropic response shapes.
    Returns a single string (may be empty).
    """
    # 0) top-level 'content' (list of blocks) e.g. { 'content': [{'type':'text','text':'Boom'}], ... }
    content = resp_json.get("content")
    if isinstance(content, list) and content:
        parts = []
        for block in content:
            if isinstance(block, dict):
                # common block shape: {'type': 'text', 'text': '...'}
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
            elif isinstance(block, str):
                parts.append(block)
        text = "".join(parts).strip()
        if text:
            return text

    # 1) 'messages' top-level (list) -> messages[0]['content'] may be list or str
    msgs = resp_json.get("messages")
    if isinstance(msgs, list) and msgs:
        first = msgs[0]
        content = first.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    parts.append(block)
            text = "".join(parts).strip()
            if text:
                return text

    # 2) older 'message' or nested 'message' -> message['content']
    msg = resp_json.get("message")
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, list):
            parts = []
            for block in c:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text",""))
                elif isinstance(block, str):
                    parts.append(block)
            text = "".join(parts).strip()
            if text:
                return text

    # 3) 'completion' string
    comp = resp_json.get("completion")
    if isinstance(comp, str) and comp.strip():
        return comp.strip()

    # 4) some models use 'output'/'result' keys
    for k in ("output", "result", "text"):
        v = resp_json.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    return ""

