"""문서 청킹 관련 스키마"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ChunkStrategy(str, Enum):
    """청킹 전략"""
    CHARACTER = "character"  # 문자 수 기반
    TOKEN = "token"         # 토큰 수 기반  
    SENTENCE = "sentence"   # 문장 기반
    PARAGRAPH = "paragraph" # 문단 기반
    SEMANTIC = "semantic"   # 의미 기반

class DocumentChunkRequest(BaseModel):
    """문서 청킹 요청"""
    text: str = Field(..., description="청킹할 텍스트", min_length=1)
    strategy: ChunkStrategy = Field(ChunkStrategy.CHARACTER, description="청킹 전략")
    chunk_size: int = Field(1000, ge=100, le=8000, description="청크 크기")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="청크 겹침 크기")
    separators: Optional[List[str]] = Field(None, description="구분자 목록")
    preserve_formatting: bool = Field(True, description="포맷팅 유지 여부")

class DocumentChunk(BaseModel):
    """문서 청크"""
    id: int = Field(..., description="청크 ID")
    content: str = Field(..., description="청크 내용")
    start_index: int = Field(..., description="원본에서의 시작 위치")
    end_index: int = Field(..., description="원본에서의 끝 위치")
    length: int = Field(..., description="청크 길이")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")

class DocumentChunkResponse(BaseModel):
    """문서 청킹 응답"""
    chunks: List[DocumentChunk] = Field(..., description="청크 목록")
    total_chunks: int = Field(..., description="총 청크 수")
    original_length: int = Field(..., description="원본 텍스트 길이")
    strategy_used: ChunkStrategy = Field(..., description="사용된 청킹 전략")
    processing_time: float = Field(..., description="처리 시간(초)")
    
class EmbeddingRequest(BaseModel):
    """임베딩 요청"""
    texts: List[str] = Field(..., description="임베딩할 텍스트 목록", min_items=1, max_items=100)
    model: str = Field("solar-embedding-1-large-query", description="사용할 임베딩 모델")

class EmbeddingResponse(BaseModel):
    """임베딩 응답"""
    embeddings: List[List[float]] = Field(..., description="임베딩 벡터 목록")
    model_used: str = Field(..., description="사용된 모델")
    total_tokens: int = Field(..., description="처리된 토큰 수")

class FileChunkRequest(BaseModel):
    """파일 청킹 요청"""
    strategy: ChunkStrategy = Field(ChunkStrategy.CHARACTER, description="청킹 전략")
    chunk_size: int = Field(1000, ge=100, le=8000, description="청크 크기")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="청크 겹침 크기")
    preserve_formatting: bool = Field(True, description="포맷팅 유지 여부")

class URLChunkRequest(BaseModel):
    """URL 청킹 요청"""
    url: str = Field(..., description="텍스트를 추출할 URL", regex=r'^https?://.+')
    strategy: ChunkStrategy = Field(ChunkStrategy.CHARACTER, description="청킹 전략")
    chunk_size: int = Field(1000, ge=100, le=8000, description="청크 크기")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="청크 겹침 크기")

class TextExtractionResponse(BaseModel):
    """텍스트 추출 응답"""
    text: str = Field(..., description="추출된 텍스트")
    source_type: str = Field(..., description="소스 타입 (file/url)")
    file_name: Optional[str] = Field(None, description="파일명")
    content_type: Optional[str] = Field(None, description="콘텐츠 타입")
    text_length: int = Field(..., description="텍스트 길이")
    extraction_time: float = Field(..., description="추출 시간(초)")