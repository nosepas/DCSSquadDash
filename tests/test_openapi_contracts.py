"""The two OpenAPI documents are the published contracts: they must stay valid."""
from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts"


@pytest.mark.parametrize("name", ["openapi-agent.yaml", "openapi-public.yaml"])
def test_openapi_document_is_valid(name):
    validate(yaml.safe_load((CONTRACTS / name).read_text("utf-8")))
