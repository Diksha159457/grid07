from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Persona:
    bot_id: str
    name: str
    description: str
    stance: str


@dataclass(frozen=True)
class RouteMatch:
    bot_id: str
    bot_name: str
    similarity: float
    rationale: str


@dataclass(frozen=True)
class GeneratedPost:
    bot_id: str
    topic: str
    post_content: str
    source_headline: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Comment:
    author: str
    content: str


@dataclass(frozen=True)
class ThreadContext:
    parent_post: Comment
    comment_history: list[Comment] = field(default_factory=list)

    def to_lines(self) -> list[str]:
        lines = [f"[PARENT POST by {self.parent_post.author}]: {self.parent_post.content}"]
        for comment in self.comment_history:
            lines.append(f"[COMMENT by {comment.author}]: {comment.content}")
        return lines
