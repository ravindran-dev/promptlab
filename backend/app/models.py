import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class BenchmarkCase(Base):
    __tablename__ = "benchmark_cases"

    id = Column(String(100), primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)
    template = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class MetricRun(Base):
    __tablename__ = "metric_runs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_version = Column(String(50), nullable=False, index=True)
    benchmark_case_id = Column(String(100), ForeignKey("benchmark_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Store inputs for standalone generation tracing
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)
    template = Column(Text, nullable=False)
    
    prd = Column(Text, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    
    # Scoring metrics
    coverage_score = Column(Float, nullable=False)
    hallucination_score = Column(Float, nullable=False)
    design_score = Column(Float, nullable=False)
    engineering_score = Column(Float, nullable=False)
    qa_score = Column(Float, nullable=False)
    prototype_score = Column(Float, nullable=False)
    repetition_score = Column(Float, nullable=False)
    format_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
