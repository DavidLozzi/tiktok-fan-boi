from tiktok_automation.config import LLMSettings
from tiktok_automation.llm import LLMCaptioner


class DummyClient:
    def __init__(self):
        class _Responses:
            def create(self, *args, **kwargs):
                raise AssertionError("LLM network should be mocked")

        self.responses = _Responses()


def test_captioner_renders_credit_and_hashtags(monkeypatch, sample_metadata, test_logger):
    settings = LLMSettings(max_hashtags=3)
    captioner = LLMCaptioner(settings, test_logger, client=DummyClient())

    def fake_invoke(self, metadata, keyframes):
        return ("Fresh caption", ["Fun", "Viral", "Fun"])

    monkeypatch.setattr(LLMCaptioner, "_invoke_llm", fake_invoke)

    result = captioner.generate(sample_metadata, keyframes=[])
    assert "Credit: @source" in result.final_caption
    assert "#fun" in result.final_caption
    assert result.credit_added is True
