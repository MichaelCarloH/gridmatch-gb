"""Research notebook response schemas."""

from api.schemas.common import ListEnvelope, ObjectEnvelope


class NotebookListResponse(ListEnvelope):
    pass


class NotebookResponse(ObjectEnvelope):
    pass
