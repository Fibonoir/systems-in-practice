"""Application validation of externally supplied data."""

import json


class ProtocolError(ValueError):
    pass


ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["answered", "unknown"],
        },
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "chunk_id": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["chunk_id", "quote"],
            },
        },
    },
    "required": ["status", "answer", "citations"],
}


def object_with_keys(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ProtocolError("unexpected object fields")


def bounded_string(value, maximum, label):
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{label} must be nonempty text")
    if len(value) > maximum:
        raise ProtocolError(f"{label} too long")
    return value


def parse_answer(content, evidence):
    try:
        answer = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ProtocolError(
            "final answer is not JSON"
        ) from exc
    object_with_keys(
        answer, ["status", "answer", "citations"]
    )
    if answer["status"] not in ("answered", "unknown"):
        raise ProtocolError("unknown answer status")
    bounded_string(answer["answer"], 2000, "answer")
    citations = answer["citations"]
    if not isinstance(citations, list) or len(citations) > 6:
        raise ProtocolError("invalid citation list")
    if (answer["status"] == "answered") != bool(citations):
        raise ProtocolError(
            "answered needs citations; unknown needs none"
        )
    for citation in citations:
        object_with_keys(citation, ["chunk_id", "quote"])
        cid = bounded_string(
            citation["chunk_id"], 200, "chunk ID"
        )
        quote = bounded_string(
            citation["quote"], 300, "quote"
        )
        if len(quote.strip()) < 12:
            raise ProtocolError("quote too short to inspect")
        if cid not in evidence or quote not in evidence[cid]:
            raise ProtocolError(
                "citation was not observed verbatim"
            )
    return answer


def tool_schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            },
        },
    }


TOOLS = [
    tool_schema(
        "list_documents",
        "List available document IDs.",
        {},
        [],
    ),
    tool_schema(
        "search",
        "Find paragraphs by lexical overlap.",
        {
            "query": {"type": "string"},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
            },
        },
        ["query", "limit"],
    ),
    tool_schema(
        "read_document",
        "Read a known document ID.",
        {"document": {"type": "string"}},
        ["document"],
    ),
]


def validate_call(call):
    if not isinstance(call, dict):
        raise ProtocolError("tool call must be an object")
    function = call.get("function")
    if not isinstance(function, dict):
        raise ProtocolError("function must be an object")
    if set(function) not in (
        {"name", "arguments"},
        {"name", "arguments", "index"},
    ):
        raise ProtocolError("unexpected function fields")
    if "index" in function and (
        type(function["index"]) is not int
        or function["index"] < 0
    ):
        raise ProtocolError("invalid tool-call index")
    name, args = function["name"], function["arguments"]
    if not isinstance(name, str) or not isinstance(
        args, dict
    ):
        raise ProtocolError("invalid function call")
    if name == "list_documents":
        object_with_keys(args, [])
    elif name == "read_document":
        object_with_keys(args, ["document"])
        bounded_string(args["document"], 100, "document ID")
    elif name == "search":
        object_with_keys(args, ["query", "limit"])
        bounded_string(args["query"], 300, "query")
        if (
            type(args["limit"]) is not int
            or not 1 <= args["limit"] <= 5
        ):
            raise ProtocolError(
                "limit must be an integer from 1 to 5"
            )
    else:
        raise ProtocolError("unknown tool name")
    return name, args
