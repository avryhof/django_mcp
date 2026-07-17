from django.http import JsonResponse
from .protocol.errors import MCPError


def mcp_json_response(data, status=200, jsonrpc_id=None):
    return JsonResponse(
        {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": data,
        },
        status=status,
        json_dumps_params={"indent": 2},
    )


def mcp_error_response(error, jsonrpc_id=None):
    if isinstance(error, MCPError):
        error_dict = error.to_dict()
    elif isinstance(error, dict):
        error_dict = error
    else:
        error_dict = {
            "code": -32603,
            "message": str(error),
        }

    return JsonResponse(
        {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "error": error_dict,
        },
        status=200,
        json_dumps_params={"indent": 2},
    )


def mcp_tool_result_response(result, jsonrpc_id=None):
    return JsonResponse(
        {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": str(result) if not isinstance(result, str) else result,
                    }
                ],
            },
        },
        status=200,
        json_dumps_params={"indent": 2},
    )
