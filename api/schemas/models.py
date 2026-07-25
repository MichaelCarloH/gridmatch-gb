"""Model registry response schemas."""

from api.schemas.common import ListEnvelope, ObjectEnvelope


class ModelListResponse(ListEnvelope):
    pass


class ModelResponse(ObjectEnvelope):
    pass
