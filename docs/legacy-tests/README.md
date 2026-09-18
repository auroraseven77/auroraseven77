# Legacy TUU test surface

The former `TUU/tests/test_tuu_integration.py` and
`TUU/tests/test_tuu_m7_integration.py` targeted the removed `TUUCore`/M7 API.

They are intentionally excluded from the active test runner while the modern
Pydantic-based TUU lifecycle is the supported API. Their deletion is preserved
in Git history so a later migration can recover the exact legacy contracts.

Do not re-enable these files by changing CI paths or import hacks. A future
migration should rewrite the contracts against the current public API.
