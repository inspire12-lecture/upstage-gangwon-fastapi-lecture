import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.service.agent_service import AgentService
from app.service.vector_service import VectorService


class TestAgentService:
    @pytest.fixture
    def mock_vector_service(self):
        return Mock(spec=VectorService)

    @pytest.fixture
    def mock_upstage_client(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response from Solar LLM"
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    @pytest.fixture
    def agent_service(self, mock_vector_service, mock_upstage_client):
        with patch.dict(os.environ, {"UPSTAGE_API_KEY": "test-key"}):
            with patch(
                "app.service.agent_service.Upstage", return_value=mock_upstage_client
            ):
                with patch.object(
                    AgentService,
                    "_AgentService__init__",
                    lambda self: self._init_with_mocks(
                        mock_vector_service, mock_upstage_client
                    ),
                ):
                    agent = AgentService()
                    return agent

    def _init_with_mocks(self, agent, mock_vector_service, mock_upstage_client):
        agent.vector_service = mock_vector_service
        agent.client = mock_upstage_client

    @pytest.mark.unit
    def test_agent_service_initialization_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="UPSTAGE_API_KEY environment variable is required"
            ):
                AgentService()

    @pytest.mark.unit
    def test_add_knowledge_success(self, agent_service, mock_vector_service):
        test_documents = ["Test document 1", "Test document 2"]
        mock_vector_service.add_documents.return_value = None

        result = agent_service.add_knowledge(test_documents)

        assert result["status"] == "success"
        assert "Added 2 documents" in result["message"]
        mock_vector_service.add_documents.assert_called_once_with(test_documents, None)

    @pytest.mark.unit
    def test_add_knowledge_with_metadata(self, agent_service, mock_vector_service):
        test_documents = ["Test document"]
        test_metadata = [{"source": "test"}]

        result = agent_service.add_knowledge(test_documents, test_metadata)

        assert result["status"] == "success"
        mock_vector_service.add_documents.assert_called_once_with(
            test_documents, test_metadata
        )

    @pytest.mark.unit
    def test_add_knowledge_failure(self, agent_service, mock_vector_service):
        test_documents = ["Test document"]
        mock_vector_service.add_documents.side_effect = Exception(
            "Vector service error"
        )

        result = agent_service.add_knowledge(test_documents)

        assert result["status"] == "error"
        assert "Vector service error" in result["message"]

    @pytest.mark.unit
    def test_get_knowledge_stats(self, agent_service, mock_vector_service):
        expected_stats = {"name": "test_collection", "count": 5, "metadata": {}}
        mock_vector_service.get_collection_info.return_value = expected_stats

        result = agent_service.get_knowledge_stats()

        assert result == expected_stats
        mock_vector_service.get_collection_info.assert_called_once()

    @pytest.mark.unit
    def test_prepare_context(self, agent_service):
        search_results = {
            "documents": ["Doc 1 content", "Doc 2 content"],
            "metadatas": [{"source": "file1"}, {"source": "file2"}],
        }

        context = agent_service._prepare_context(search_results)

        assert "Document 1:" in context
        assert "Document 2:" in context
        assert "Doc 1 content" in context
        assert "Doc 2 content" in context
        assert "source" in context

    @pytest.mark.unit
    def test_prepare_context_without_metadata(self, agent_service):
        search_results = {"documents": ["Doc content"], "metadatas": [{}]}

        context = agent_service._prepare_context(search_results)

        assert "Document 1:" in context
        assert "Doc content" in context

    @pytest.mark.unit
    def test_generate_response_success(self, agent_service, mock_upstage_client):
        query = "Test question"
        context = "Test context"

        response = agent_service._generate_response(query, context)

        assert response == "Test response from Solar LLM"
        mock_upstage_client.chat.completions.create.assert_called_once()

        call_args = mock_upstage_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "solar-1-mini-chat"
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["temperature"] == 0.3
        assert call_args[1]["max_tokens"] == 500

    @pytest.mark.unit
    def test_generate_response_failure(self, agent_service, mock_upstage_client):
        mock_upstage_client.chat.completions.create.side_effect = Exception("API Error")

        response = agent_service._generate_response("test", "test")

        assert "Error generating response: API Error" in response

    @pytest.mark.unit
    def test_process_query_complete_flow(
        self, agent_service, mock_vector_service, mock_upstage_client
    ):
        query = "What is FastAPI?"
        mock_search_results = {
            "documents": ["FastAPI is a web framework"],
            "metadatas": [{"source": "docs"}],
            "distances": [0.1],
        }
        mock_vector_service.search.return_value = mock_search_results

        result = agent_service.process_query(query)

        assert result["query"] == query
        assert result["response"] == "Test response from Solar LLM"
        assert result["retrieved_documents"] == ["FastAPI is a web framework"]
        assert result["document_distances"] == [0.1]
        assert "context_used" in result

        mock_vector_service.search.assert_called_once_with(query, n_results=3)

    @pytest.mark.unit
    def test_process_query_with_custom_context_limit(
        self, agent_service, mock_vector_service
    ):
        query = "Test query"
        context_limit = 5
        mock_vector_service.search.return_value = {
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        agent_service.process_query(query, context_limit)

        mock_vector_service.search.assert_called_once_with(
            query, n_results=context_limit
        )


@pytest.mark.integration
class TestAgentServiceIntegration:
    """
    Integration tests that require actual services to be running.
    Run with: pytest -m integration
    """

    @pytest.fixture
    def agent_service_integration(self):
        """
        Creates a real AgentService for integration testing.
        Requires UPSTAGE_API_KEY and ChromaDB to be running.
        """
        if not os.getenv("UPSTAGE_API_KEY"):
            pytest.skip("UPSTAGE_API_KEY not found - skipping integration test")

        try:
            return AgentService()
        except Exception as e:
            pytest.skip(f"Could not initialize AgentService: {e}")

    def test_full_agent_workflow(self, agent_service_integration):
        """Test the complete agent workflow with real services."""
        agent = agent_service_integration

        # Add test knowledge
        test_docs = [
            "Python is a programming language.",
            "FastAPI is a web framework for Python.",
        ]

        result = agent.add_knowledge(test_docs)
        assert result["status"] == "success"

        # Check knowledge stats
        stats = agent.get_knowledge_stats()
        assert stats["count"] > 0

        # Process a query
        response = agent.process_query("What is Python?")
        assert "query" in response
        assert "response" in response
        assert len(response["retrieved_documents"]) > 0

    def test_agent_with_real_chromadb_connection(self, agent_service_integration):
        """Test that agent can connect to and use ChromaDB."""
        agent = agent_service_integration

        # Test getting collection info (this tests ChromaDB connection)
        stats = agent.get_knowledge_stats()
        assert "name" in stats
        assert "count" in stats
        assert isinstance(stats["count"], int)


# Test runner for backward compatibility with existing script
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
