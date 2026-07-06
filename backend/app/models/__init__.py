"""SQLAlchemy models. See docs/ARCHITECTURE.md for the ERD."""
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(50))  # annual_accounts|interim_results|information_document|press_release|presentation|balance_sheet|market_data
    published_date: Mapped[date | None] = mapped_column(Date)
    pages: Mapped[int | None]
    sha256: Mapped[str | None] = mapped_column(String(64))
    has_text_layer: Mapped[bool] = mapped_column(Boolean, default=True)

    facts: Mapped[list["FinancialFact"]] = relationship(back_populates="document")


class Period(Base):
    __tablename__ = "periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(10), unique=True)  # FY24, FY25, HY25, HY26, MKT
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    period_type: Mapped[str] = mapped_column(String(4))  # FY | HY | PT
    audited: Mapped[bool] = mapped_column(Boolean, default=False)

    facts: Mapped[list["FinancialFact"]] = relationship(back_populates="period")


class FinancialFact(Base):
    __tablename__ = "financial_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("periods.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    statement: Mapped[str] = mapped_column(String(10))  # pnl | bs | cf | kpi
    line_code: Mapped[str] = mapped_column(String(60))
    label: Mapped[str] = mapped_column(String(255))
    value: Mapped[float] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String(10), default="EUR")  # EUR | count | ratio
    page_number: Mapped[int | None]
    extraction_method: Mapped[str] = mapped_column(String(10), default="vision")  # vision|text|derived
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    period: Mapped[Period] = relationship(back_populates="facts")
    document: Mapped[Document] = relationship(back_populates="facts")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_name: Mapped[str] = mapped_column(String(120))
    period_label: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10))  # pass | warn | fail
    detail: Mapped[str] = mapped_column(Text)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int | None]
    # embedding stored as JSON-encoded list for portability (cosine in Python at this
    # corpus size); pgvector + HNSW is the documented scale-up path (docs/ARCHITECTURE.md)
    content: Mapped[str] = mapped_column(Text)
    embedding_json: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document] = relationship()


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    audience: Mapped[str] = mapped_column(String(20))  # board|management|investor|credit
    section: Mapped[str] = mapped_column(String(30))
    period_label: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(60))
    prompt_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120), default="Demo CEO")
