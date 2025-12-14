"""문서 처리 서비스"""
import re
import time
from typing import List, Dict, Any
from fastapi import UploadFile

from app.models.schemas.document import (
    DocumentChunkRequest, 
    DocumentChunk, 
    DocumentChunkResponse,
    ChunkStrategy,
    EmbeddingRequest,
    EmbeddingResponse,
    FileChunkRequest,
    URLChunkRequest,
    TextExtractionResponse
)
from app.repository.client.upstage_client import UpstageClient
from app.utils.file_extractor import FileExtractor, URLExtractor

class DocumentService:
    """문서 처리 서비스"""
    
    def __init__(self, upstage_client: UpstageClient):
        self.client = upstage_client
    
    def chunk_document(self, request: DocumentChunkRequest) -> DocumentChunkResponse:
        """문서를 청크로 분할"""
        start_time = time.time()
        
        chunks = []
        text = request.text
        
        if request.strategy == ChunkStrategy.CHARACTER:
            chunks = self._chunk_by_character(text, request.chunk_size, request.chunk_overlap)
        elif request.strategy == ChunkStrategy.TOKEN:
            chunks = self._chunk_by_token(text, request.chunk_size, request.chunk_overlap)
        elif request.strategy == ChunkStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(text, request.chunk_size, request.chunk_overlap)
        elif request.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text, request.chunk_size, request.chunk_overlap)
        elif request.strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_by_semantic(text, request.chunk_size, request.chunk_overlap)
        
        processing_time = time.time() - start_time
        
        return DocumentChunkResponse(
            chunks=chunks,
            total_chunks=len(chunks),
            original_length=len(text),
            strategy_used=request.strategy,
            processing_time=processing_time
        )
    
    def _chunk_by_character(self, text: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """문자 수 기반 청킹"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end]
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=content,
                start_index=start,
                end_index=end,
                length=len(content),
                metadata={"strategy": "character"}
            )
            chunks.append(chunk)
            
            chunk_id += 1
            start = end - overlap
            
            if start >= len(text):
                break
                
        return chunks
    
    def _chunk_by_token(self, text: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """토큰 수 기반 청킹 (간단한 단어 분할)"""
        words = text.split()
        chunks = []
        chunk_id = 0
        start_idx = 0
        
        while start_idx < len(words):
            end_idx = min(start_idx + chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            content = " ".join(chunk_words)
            
            # 원본 텍스트에서의 위치 계산
            start_pos = text.find(chunk_words[0]) if chunk_words else 0
            end_pos = start_pos + len(content)
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=content,
                start_index=start_pos,
                end_index=end_pos,
                length=len(content),
                metadata={"strategy": "token", "word_count": len(chunk_words)}
            )
            chunks.append(chunk)
            
            chunk_id += 1
            start_idx = end_idx - overlap
            
            if start_idx >= len(words):
                break
                
        return chunks
    
    def _chunk_by_sentence(self, text: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """문장 기반 청킹"""
        # 간단한 문장 분할 (더 정교한 라이브러리 사용 가능)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(sentences):
            chunk_sentences = []
            current_length = 0
            end = start
            
            # chunk_size까지 문장들을 모음
            while end < len(sentences) and current_length < chunk_size:
                sentence = sentences[end]
                if current_length + len(sentence) <= chunk_size:
                    chunk_sentences.append(sentence)
                    current_length += len(sentence)
                    end += 1
                else:
                    break
            
            if not chunk_sentences and end < len(sentences):
                # 문장이 너무 길면 강제로 포함
                chunk_sentences = [sentences[end]]
                end += 1
            
            if chunk_sentences:
                content = ". ".join(chunk_sentences)
                start_pos = text.find(chunk_sentences[0])
                end_pos = start_pos + len(content)
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=content,
                    start_index=start_pos,
                    end_index=end_pos,
                    length=len(content),
                    metadata={"strategy": "sentence", "sentence_count": len(chunk_sentences)}
                )
                chunks.append(chunk)
                
                chunk_id += 1
            
            # 겹침 처리
            start = max(start + 1, end - overlap)
            
        return chunks
    
    def _chunk_by_paragraph(self, text: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """문단 기반 청킹"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(paragraphs):
            chunk_paragraphs = []
            current_length = 0
            end = start
            
            while end < len(paragraphs) and current_length < chunk_size:
                paragraph = paragraphs[end]
                if current_length + len(paragraph) <= chunk_size:
                    chunk_paragraphs.append(paragraph)
                    current_length += len(paragraph)
                    end += 1
                else:
                    break
            
            if not chunk_paragraphs and end < len(paragraphs):
                chunk_paragraphs = [paragraphs[end]]
                end += 1
            
            if chunk_paragraphs:
                content = "\n\n".join(chunk_paragraphs)
                start_pos = text.find(chunk_paragraphs[0])
                end_pos = start_pos + len(content)
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=content,
                    start_index=start_pos,
                    end_index=end_pos,
                    length=len(content),
                    metadata={"strategy": "paragraph", "paragraph_count": len(chunk_paragraphs)}
                )
                chunks.append(chunk)
                
                chunk_id += 1
            
            start = max(start + 1, end - max(1, overlap // 2))
            
        return chunks
    
    def _chunk_by_semantic(self, text: str, chunk_size: int, overlap: int) -> List[DocumentChunk]:
        """의미 기반 청킹 (현재는 문장 기반으로 대체)"""
        # 실제로는 임베딩을 사용한 의미적 유사성 기반 청킹을 구현할 수 있음
        return self._chunk_by_sentence(text, chunk_size, overlap)
    
    def create_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """텍스트 임베딩 생성"""
        try:
            embeddings = self.client.create_embeddings(request.texts)
            total_tokens = sum(len(text.split()) for text in request.texts)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model_used=request.model,
                total_tokens=total_tokens
            )
        except Exception as e:
            raise RuntimeError(f"임베딩 생성 실패: {str(e)}")
    
    def chunk_and_embed(self, chunk_request: DocumentChunkRequest, model: str = "solar-embedding-1-large-query") -> Dict[str, Any]:
        """문서 청킹 + 임베딩 생성"""
        # 1단계: 문서 청킹
        chunk_response = self.chunk_document(chunk_request)
        
        # 2단계: 각 청크에 대해 임베딩 생성
        texts = [chunk.content for chunk in chunk_response.chunks]
        embedding_request = EmbeddingRequest(texts=texts, model=model)
        embedding_response = self.create_embeddings(embedding_request)
        
        # 3단계: 청크와 임베딩 매핑
        for i, chunk in enumerate(chunk_response.chunks):
            chunk.metadata["embedding"] = embedding_response.embeddings[i]
        
        return {
            "chunks": chunk_response,
            "embeddings": embedding_response,
            "total_processing_time": chunk_response.processing_time
        }
    
    async def extract_text_from_file(self, file: UploadFile) -> TextExtractionResponse:
        """파일에서 텍스트 추출"""
        start_time = time.time()
        
        text = await FileExtractor.extract_text(file)
        
        return TextExtractionResponse(
            text=text,
            source_type="file",
            file_name=file.filename,
            content_type=file.content_type,
            text_length=len(text),
            extraction_time=time.time() - start_time
        )
    
    async def extract_text_from_url(self, url: str) -> TextExtractionResponse:
        """URL에서 텍스트 추출"""
        start_time = time.time()
        
        text = await URLExtractor.extract_from_url(url)
        
        return TextExtractionResponse(
            text=text,
            source_type="url",
            content_type="text/html",
            text_length=len(text),
            extraction_time=time.time() - start_time
        )
    
    async def chunk_file(self, file: UploadFile, request: FileChunkRequest) -> DocumentChunkResponse:
        """파일을 청크로 분할"""
        # 1단계: 파일에서 텍스트 추출
        text_response = await self.extract_text_from_file(file)
        
        # 2단계: 텍스트 청킹
        chunk_request = DocumentChunkRequest(
            text=text_response.text,
            strategy=request.strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            preserve_formatting=request.preserve_formatting
        )
        
        chunk_response = self.chunk_document(chunk_request)
        
        # 메타데이터에 파일 정보 추가
        for chunk in chunk_response.chunks:
            chunk.metadata.update({
                "source_file": file.filename,
                "source_type": "file",
                "content_type": file.content_type
            })
        
        return chunk_response
    
    async def chunk_url(self, request: URLChunkRequest) -> DocumentChunkResponse:
        """URL에서 텍스트를 추출하여 청크로 분할"""
        # 1단계: URL에서 텍스트 추출
        text_response = await self.extract_text_from_url(request.url)
        
        # 2단계: 텍스트 청킹
        chunk_request = DocumentChunkRequest(
            text=text_response.text,
            strategy=request.strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        chunk_response = self.chunk_document(chunk_request)
        
        # 메타데이터에 URL 정보 추가
        for chunk in chunk_response.chunks:
            chunk.metadata.update({
                "source_url": request.url,
                "source_type": "url"
            })
        
        return chunk_response
    
    def get_supported_file_formats(self) -> Dict[str, str]:
        """지원하는 파일 형식 목록"""
        return FileExtractor.get_supported_formats()