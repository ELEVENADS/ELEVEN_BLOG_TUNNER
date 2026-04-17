import pytest
from eleven_blog_tunner.core.exceptions import (
    ElevenBlogException,
    AgentException,
    LLMException,
    RAGException,
    ToolException,
    ConfigException,
    AgentNotFoundError,
    LLMConnectionError,
)

class TestElevenBlogException:
    def test_exception_with_message(self):
        exc = ElevenBlogException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.error_code == 500
        assert exc.details == {}

    def test_exception_with_code_and_message(self):
        exc = ElevenBlogException("Custom message", error_code=400)
        assert str(exc) == "Custom message"
        assert exc.error_code == 400

    def test_exception_with_details(self):
        exc = ElevenBlogException("Error with details", details={"key": "value"})
        assert exc.details == {"key": "value"}

    def test_exception_to_dict(self):
        exc = ElevenBlogException("Test", error_code=404, details={"test": True})
        result = exc.to_dict()
        assert "error" in result
        assert result["error"]["message"] == "Test"
        assert result["error"]["error_code"] == 404


class TestAgentException:
    def test_agent_exception_defaults(self):
        exc = AgentException("Agent error")
        assert "Agent error" in str(exc)
        assert exc.error_code == 500


class TestLLMException:
    def test_llm_exception_defaults(self):
        exc = LLMException("LLM error")
        assert "LLM error" in str(exc)
        assert exc.error_code == 500


class TestRAGException:
    def test_rag_exception_defaults(self):
        exc = RAGException("RAG error")
        assert "RAG error" in str(exc)
        assert exc.error_code == 500


class TestToolException:
    def test_tool_exception_defaults(self):
        exc = ToolException("Tool error")
        assert "Tool error" in str(exc)
        assert exc.error_code == 500


class TestConfigException:
    def test_config_exception_defaults(self):
        exc = ConfigException("Config error")
        assert "Config error" in str(exc)
        assert exc.error_code == 500


class TestSpecificExceptions:
    def test_agent_not_found_error(self):
        exc = AgentNotFoundError("my_agent")
        assert "my_agent" in str(exc)
        assert exc.error_code == 404
        assert exc.details["agent_name"] == "my_agent"

    def test_llm_connection_error(self):
        exc = LLMConnectionError("openai", "connection refused")
        assert "openai" in str(exc)
        assert exc.error_code == 503
