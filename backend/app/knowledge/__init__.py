"""Knowledge spaces group uploads and chats by the kind of file."""

from app.knowledge.spaces import (
    SPACES,
    UnknownSpace,
    WrongSpaceFile,
    infer_space,
    require_file,
    space_by_id,
)

__all__ = [
    "SPACES",
    "UnknownSpace",
    "WrongSpaceFile",
    "infer_space",
    "require_file",
    "space_by_id",
]
