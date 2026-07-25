from __future__ import annotations

import pytest

from gridmatch.data.synthetic import generate_portfolio


@pytest.fixture(scope="session")
def synthetic_portfolio():
    return generate_portfolio()
