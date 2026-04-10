import re

with open('main.py', 'r') as f:
    content = f.read()

# 1. Yield an immediate connecting block to prevent Vercel 10s timeout during API checking
old_stream = """    async def stream_tokens_with_keys(req_body: ChatRequest, keys: dict):
        try:
            async for chunk in generate_ai_response_with_llm_stream("""

new_stream = """    async def stream_tokens_with_keys(req_body: ChatRequest, keys: dict):
        try:
            # Send immediate ping to prevent Vercel timeout if provider fallback takes time
            yield f"data: {json.dumps({'type': 'token', 'content': ''})}\n\n"

            async for chunk in generate_ai_response_with_llm_stream("""
content = content.replace(old_stream, new_stream)


# 2. Add proper SSE headers for Vercel Serverless (Cache-Control: no-cache, Connection: keep-alive)
old_streaming_response = """    return StreamingResponse(
        stream_tokens_with_keys(request, custom_keys),
        media_type="text/event-stream"
    )"""

new_streaming_response = """    return StreamingResponse(
        stream_tokens_with_keys(request, custom_keys),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # For Nginx/Vercel buffering disable
        }
    )"""
content = content.replace(old_streaming_response, new_streaming_response)

with open('main.py', 'w') as f:
    f.write(content)
