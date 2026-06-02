import os
from typing import Optional


def setup_tracing(
    project_name: str = "aiuda-flow",
    endpoint: Optional[str] = None,
    local: bool = True,
) -> None:
    """
    Configure Arize Phoenix tracing.

    - local=True  → starts embedded Phoenix server (no external service needed)
    - local=False → sends traces to endpoint (Phoenix Cloud or self-hosted)
    """
    if local:
        _setup_local(project_name)
    else:
        _setup_remote(project_name, endpoint)


def _setup_local(project_name: str) -> None:
    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        session = px.launch_app()
        print(f"🔭 Phoenix UI → {session.url}")

        exporter = px.active_session().get_tracer_provider().get_active_span_processor()

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(px.active_session().get_tracer_provider()._active_span_processor._span_processors[0]._span_processor))
        trace.set_tracer_provider(provider)

        LangChainInstrumentor().instrument()
        print(f"✅ Tracing active — project: {project_name}")

    except Exception as e:
        print(f"⚠️  Phoenix setup failed: {e}")
        _setup_otel_stdout(project_name)


def _setup_remote(project_name: str, endpoint: Optional[str]) -> None:
    try:
        from arize.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        tracer_provider = register(
            space_id=os.environ.get("ARIZE_SPACE_ID", ""),
            api_key=os.environ.get("ARIZE_API_KEY", ""),
            project_name=project_name,
            endpoint=endpoint,
        )
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        print(f"✅ Arize remote tracing active — project: {project_name}")

    except Exception as e:
        print(f"⚠️  Arize remote setup failed: {e}")
        _setup_otel_stdout(project_name)


def _setup_otel_stdout(project_name: str) -> None:
    """Fallback: print spans to stdout."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    print(f"📋 Fallback: tracing to stdout — project: {project_name}")
