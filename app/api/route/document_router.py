"""문서 처리 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Dict, Any

from app.models.schemas.document import (
    DocumentChunkRequest,
    DocumentChunkResponse, 
    EmbeddingRequest,
    EmbeddingResponse,
    FileChunkRequest,
    URLChunkRequest,
    TextExtractionResponse
)
from app.service.document_service import DocumentService
from app.deps import get_document_service

document_router = APIRouter(prefix="/documents", tags=["documents"])

@document_router.post("/chunk", response_model=DocumentChunkResponse)
async def chunk_document(
    request: DocumentChunkRequest,
    service: DocumentService = Depends(get_document_service)
) -> DocumentChunkResponse:
    """
    문서를 청크로 분할
    
    - **text**: 청킹할 텍스트
    - **strategy**: 청킹 전략 (character/token/sentence/paragraph/semantic)
    - **chunk_size**: 청크 크기
    - **chunk_overlap**: 청크 겹침 크기
    """
    try:
        return service.chunk_document(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 청킹 실패: {str(e)}"
        )

@document_router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    service: DocumentService = Depends(get_document_service)
) -> EmbeddingResponse:
    """
    텍스트 임베딩 생성
    
    - **texts**: 임베딩할 텍스트 목록
    - **model**: 사용할 임베딩 모델
    """
    try:
        return service.create_embeddings(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"임베딩 생성 실패: {str(e)}"
        )

@document_router.post("/chunk-and-embed")
async def chunk_and_embed(
    request: DocumentChunkRequest,
    model: str = "solar-embedding-1-large-query",
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """
    문서 청킹 + 임베딩 생성 (통합)
    
    - **request**: 청킹 요청
    - **model**: 임베딩 모델명
    
    Returns: 청킹 결과 + 임베딩 결과
    """
    try:
        return service.chunk_and_embed(request, model)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 처리 실패: {str(e)}"
        )

@document_router.get("/strategies")
async def get_chunk_strategies() -> Dict[str, str]:
    """사용 가능한 청킹 전략 목록"""
    return {
        "character": "문자 수 기반 청킹",
        "token": "토큰(단어) 수 기반 청킹", 
        "sentence": "문장 기반 청킹",
        "paragraph": "문단 기반 청킹",
        "semantic": "의미 기반 청킹 (베타)"
    }

@document_router.get("/models")
async def get_embedding_models() -> Dict[str, str]:
    """사용 가능한 임베딩 모델 목록"""
    return {
        "solar-embedding-1-large-query": "Upstage Solar 임베딩 모델 (쿼리용)",
        "solar-embedding-1-large-passage": "Upstage Solar 임베딩 모델 (문서용)"
    }

# === 새로운 파일 업로드 기능 ===

@document_router.post("/extract-file", response_model=TextExtractionResponse)
async def extract_text_from_file(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
) -> TextExtractionResponse:
    """
    파일에서 텍스트 추출
    
    - **file**: 업로드할 파일 (PDF, TXT, DOCX, HTML 지원)
    
    Returns: 추출된 텍스트와 메타정보
    """
    try:
        return await service.extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 텍스트 추출 실패: {str(e)}"
        )

@document_router.post("/extract-url", response_model=TextExtractionResponse)  
async def extract_text_from_url(
    url: str,
    service: DocumentService = Depends(get_document_service)
) -> TextExtractionResponse:
    """
    URL에서 텍스트 추출
    
    - **url**: 텍스트를 추출할 웹페이지 URL
    
    Returns: 추출된 텍스트와 메타정보
    """
    try:
        return await service.extract_text_from_url(url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL 텍스트 추출 실패: {str(e)}"
        )

@document_router.post("/chunk-file", response_model=DocumentChunkResponse)
async def chunk_file(
    file: UploadFile = File(...),
    strategy: str = "character",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    service: DocumentService = Depends(get_document_service)
) -> DocumentChunkResponse:
    """
    파일을 업로드하여 청크로 분할
    
    - **file**: 업로드할 파일
    - **strategy**: 청킹 전략
    - **chunk_size**: 청크 크기  
    - **chunk_overlap**: 청크 겹침 크기
    """
    try:
        from app.models.schemas.document import ChunkStrategy
        chunk_strategy = ChunkStrategy(strategy)
        
        request = FileChunkRequest(
            strategy=chunk_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            preserve_formatting=False
        )
        
        return await service.chunk_file(file, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 청킹 전략: {strategy}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 청킹 실패: {str(e)}"
        )

@document_router.post("/chunk-url", response_model=DocumentChunkResponse)
async def chunk_url(
    request: URLChunkRequest,
    service: DocumentService = Depends(get_document_service)
) -> DocumentChunkResponse:
    """
    URL에서 텍스트를 추출하여 청크로 분할
    
    - **url**: 처리할 웹페이지 URL
    - **strategy**: 청킹 전략
    - **chunk_size**: 청크 크기
    - **chunk_overlap**: 청크 겹침 크기
    """
    try:
        return await service.chunk_url(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL 청킹 실패: {str(e)}"
        )

@document_router.get("/formats")
async def get_supported_file_formats(
    service: DocumentService = Depends(get_document_service)
) -> Dict[str, str]:
    """지원하는 파일 형식 목록"""
    return service.get_supported_file_formats()