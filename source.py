from pyodide.http import pyfetch

params = await infer_params(
    conversation=CURRENT_CONVERSATION,
    description="""create the diagram based on what user asked and pass it to the plugin API to render. Mermaid is the preferred language.
    """,
    parameters={
        "type": "object",
        "properties": {},
        "required": [""]
        }
        )

resp = await pyfetch()
result = await resp.json()