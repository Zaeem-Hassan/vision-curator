"""Image SQLAlchemy model."""

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Image(Base):
    """Represents a single image within a dataset."""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Embedding info
    has_embedding: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding_model: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Analysis results
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    cluster_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duplicate_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    outlier_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # UMAP coordinates for visualization
    umap_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    umap_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    umap_z: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Extra metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="images")

    def __repr__(self) -> str:
        return f"<Image {self.filename} (dataset={self.dataset_id})>"
