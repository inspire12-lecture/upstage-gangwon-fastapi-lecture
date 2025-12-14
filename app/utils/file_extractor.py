"""파일에서 텍스트를 추출하는 유틸리티"""
import io
import re
from typing import BinaryIO, Union
from fastapi import UploadFile, HTTPException

# PDF 처리
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# DOCX 처리  
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# 웹 크롤링
try:
    from bs4 import BeautifulSoup
    import aiohttp
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


class FileExtractor:
    """파일 텍스트 추출기"""
    
    # 지원하는 파일 타입
    SUPPORTED_TYPES = {
        "application/pdf": "PDF 문서",
        "text/plain": "텍스트 파일",
        "text/markdown": "마크다운 파일", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word 문서",
        "text/html": "HTML 문서"
    }
    
    # 파일 크기 제한 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @classmethod
    def get_supported_formats(cls) -> dict:
        """지원하는 파일 형식 목록 반환"""
        return cls.SUPPORTED_TYPES
    
    @classmethod
    async def extract_text(cls, file: UploadFile) -> str:
        """파일에서 텍스트 추출"""
        # 파일 크기 검증
        await cls._validate_file_size(file)
        
        # MIME 타입에 따른 처리
        if file.content_type == "application/pdf":
            return await cls._extract_pdf_text(file)
        elif file.content_type in ["text/plain", "text/markdown"]:
            return await cls._extract_text_file(file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return await cls._extract_docx_text(file)
        elif file.content_type == "text/html":
            return await cls._extract_html_text(file)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식: {file.content_type}"
            )
    
    @classmethod
    async def _validate_file_size(cls, file: UploadFile):
        """파일 크기 검증"""
        contents = await file.read()
        if len(contents) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {cls.MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        # 파일 포인터 리셋
        await file.seek(0)
    
    @classmethod
    async def _extract_pdf_text(cls, file: UploadFile) -> str:
        """PDF 파일에서 텍스트 추출"""
        if not PDF_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="PDF 처리 라이브러리가 설치되지 않았습니다"
            )
        
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        
        text_parts = []
        
        # pdfplumber 우선 시도 (레이아웃 보존)
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        except Exception as e:
            # PyPDF2로 fallback
            pdf_file.seek(0)
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            except Exception as fallback_e:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF 텍스트 추출 실패: {str(fallback_e)}"
                )
        
        if not text_parts:
            raise HTTPException(
                status_code=400,
                detail="PDF에서 텍스트를 추출할 수 없습니다"
            )
        
        return "\n\n".join(text_parts)
    
    @classmethod  
    async def _extract_text_file(cls, file: UploadFile) -> str:
        """일반 텍스트/마크다운 파일 처리"""
        try:
            contents = await file.read()
            # UTF-8 디코딩 시도, 실패 시 다른 인코딩 시도
            try:
                text = contents.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = contents.decode('cp949')  # 한글 윈도우
                except UnicodeDecodeError:
                    text = contents.decode('latin-1')  # 마지막 수단
            
            return text.strip()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"텍스트 파일 읽기 실패: {str(e)}"
            )
    
    @classmethod
    async def _extract_docx_text(cls, file: UploadFile) -> str:
        """DOCX 파일에서 텍스트 추출"""
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="DOCX 처리 라이브러리가 설치되지 않았습니다"
            )
        
        try:
            contents = await file.read()
            docx_file = io.BytesIO(contents)
            
            doc = Document(docx_file)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            if not text_parts:
                raise HTTPException(
                    status_code=400,
                    detail="DOCX에서 텍스트를 추출할 수 없습니다"
                )
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"DOCX 텍스트 추출 실패: {str(e)}"
            )
    
    @classmethod
    async def _extract_html_text(cls, file: UploadFile) -> str:
        """HTML 파일에서 텍스트 추출"""
        if not WEB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="웹 처리 라이브러리가 설치되지 않았습니다"
            )
        
        try:
            contents = await file.read()
            html_content = contents.decode('utf-8')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # script, style 태그 제거
            for element in soup(["script", "style"]):
                element.decompose()
            
            # 텍스트 추출 및 정리
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"HTML 텍스트 추출 실패: {str(e)}"
            )


class URLExtractor:
    """URL에서 텍스트 추출"""
    
    @classmethod
    async def extract_from_url(cls, url: str) -> str:
        """URL에서 텍스트 추출"""
        if not WEB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="웹 크롤링 라이브러리가 설치되지 않았습니다"
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=400,
                            detail=f"URL 접근 실패: {response.status}"
                        )
                    
                    html_content = await response.text()
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # script, style 태그 제거
                    for element in soup(["script", "style"]):
                        element.decompose()
                    
                    # 메인 콘텐츠 추출 (더 정교하게 개선 가능)
                    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
                    
                    if main_content:
                        text = main_content.get_text()
                    else:
                        text = soup.get_text()
                    
                    # 텍스트 정리
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return text
                    
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=400,
                detail=f"URL 크롤링 실패: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"텍스트 추출 실패: {str(e)}"
            )