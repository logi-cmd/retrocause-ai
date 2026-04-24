from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import threading
import json
import queue

from retrocause.app.demo_data import (
    PROVIDERS,
    detect_demo_topic,
    topic_aware_demo_result,
)
from retrocause.api.evidence_routes import router as evidence_router
from retrocause.api.provider_routes import router as provider_router
from retrocause.api.result_conversion import (
    detect_production_scenario as _detect_production_scenario,
    result_to_v2 as _result_to_v2,
)
from retrocause.api.run_finalization import finalize_run_response
from retrocause.api.run_routes import router as run_router
from retrocause.api.run_store import create_run_id
from retrocause.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeResponseV2,
    Evidence,
    EvidenceBindingV2,
    GraphEdge,
    GraphNode,
    GraphEdgeV2,
    GraphNodeV2,
    HypothesisChainV2,
    PipelineEvaluationV2,
)

__all__ = [
    "AnalyzeRequest",
    "AnalyzeResponseV2",
    "EvidenceBindingV2",
    "GraphEdgeV2",
    "GraphNodeV2",
    "HypothesisChainV2",
    "PipelineEvaluationV2",
    "_detect_production_scenario",
    "_result_to_v2",
    "analyze_query_v2",
    "app",
]

app = FastAPI(title="RetroCause API", description="Backend API for RetroCause Engine")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evidence_router)
app.include_router(provider_router)
app.include_router(run_router)



@app.get("/")
async def root():
    return {"status": "ok", "message": "RetroCause API is running"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_query(request: AnalyzeRequest):
    try:
        from retrocause.parser import parse_input

        is_demo = True
        demo_topic: Optional[str] = None
        parsed_query = parse_input(request.query)
        result = topic_aware_demo_result(request.query)
        demo_topic = detect_demo_topic(request.query) or "default"

        result.is_demo = is_demo
        result.demo_topic = demo_topic

        nodes = [
            GraphNode(
                id=var.name,
                title=var.name.replace("_", " ").title(),
                description=var.description,
                probability=int(var.posterior_support * 100),
            )
            for var in result.variables
        ]

        edges = [
            GraphEdge(
                id=f"{edge.source}_{edge.target}",
                source=edge.source,
                target=edge.target,
                label=f"prob: {edge.conditional_prob:.2f}",
            )
            for edge in result.edges
        ]

        from retrocause.app.demo_data import DEMO_EVIDENCES

        evidences = [
            Evidence(
                id=ev.id,
                content=ev.content,
                source=str(ev.source_type),
                reliability=f"{ev.posterior_reliability:.2f}",
            )
            for ev in DEMO_EVIDENCES
        ]

        return AnalyzeResponse(
            query=result.query,
            nodes=nodes,
            edges=edges,
            evidences=evidences,
            is_demo=is_demo,
            demo_topic=demo_topic,
            analysis_mode="demo" if is_demo else result.analysis_mode,
            freshness_status=result.freshness_status,
            time_range=parsed_query.time_range,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/v2", response_model=AnalyzeResponseV2)
async def analyze_query_v2(request: AnalyzeRequest):
    try:
        run_id = create_run_id()
        is_demo = True
        result = topic_aware_demo_result(request.query)
        demo_topic = detect_demo_topic(request.query) or "default"

        result.is_demo = is_demo
        result.demo_topic = demo_topic

        resp = _result_to_v2(
            result,
            is_demo=is_demo,
            demo_topic=demo_topic,
            scenario_override=request.scenario_override,
        )
        return finalize_run_response(resp, request, run_id, PROVIDERS)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/v2/stream")
async def analyze_query_v2_stream(request: AnalyzeRequest):
    run_id = create_run_id()

    def generate():
        eq: queue.Queue[dict | None] = queue.Queue()

        def on_progress(step_name: str, step_index: int, total: int, message: str):
            eq.put(
                {
                    "type": "progress",
                    "step": step_name,
                    "step_index": step_index + 1,
                    "total_steps": total,
                    "message": message,
                }
            )

        def worker():
            import time as _time

            _t0 = _time.time()
            try:
                on_progress("local_demo", 0, 1, "Running keyless local OSS analysis.")
                demo_result = topic_aware_demo_result(request.query)
                demo_topic = detect_demo_topic(request.query) or "default"
                demo_result.is_demo = True
                demo_result.demo_topic = demo_topic
                resp = _result_to_v2(
                    demo_result,
                    is_demo=True,
                    demo_topic=demo_topic,
                    scenario_override=request.scenario_override,
                )
                resp = finalize_run_response(resp, request, run_id, PROVIDERS)
                _elapsed = _time.time() - _t0
                eq.put(
                    {
                        "type": "progress",
                        "step": "local_demo",
                        "step_index": 1,
                        "total_steps": 1,
                        "message": f"Local OSS analysis completed in {_elapsed:.1f}s.",
                    }
                )
                eq.put(
                    {
                        "type": "done",
                        "is_demo": True,
                        "demo_topic": demo_topic,
                        "data": resp.model_dump(mode="json"),
                    }
                )

            except Exception as exc:
                eq.put({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
            finally:
                eq.put(None)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            try:
                item = eq.get(timeout=420)
            except queue.Empty:
                break
            if item is None:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            if item.get("type") in ("done", "error"):
                break

    return StreamingResponse(generate(), media_type="text/event-stream")
