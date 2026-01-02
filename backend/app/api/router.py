from fastapi import APIRouter
from app.schemas.ingest import InvocationIngest, IngestResponse

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    return {"status": "healthy"}

@api_router.post("/ingest", response_model=IngestResponse)
async def ingest_data(data: InvocationIngest):
    # TODO: Implement actual storage logic
    return IngestResponse(invocation_id=data.invocation_id)
