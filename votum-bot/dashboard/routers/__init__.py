"""Router package for FastAPI endpoints."""

from . import councils, motions, votes, archives, configs

__all__ = ["councils", "motions", "votes", "archives", "configs"]