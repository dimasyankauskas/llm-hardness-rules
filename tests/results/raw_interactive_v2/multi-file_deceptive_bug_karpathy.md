MCP issues detected. Run /mcp list for status.I will start by reading the contents of `test_validation.py` and `validator.py` to understand the test case and the current implementation of email validation.
I will read `config.py` to see the email settings and which special characters are currently allowed.
I will run the tests to confirm that `test_email_with_plus` is indeed failing as expected.
I will try to run the tests using `python3 -m pytest` to confirm the failure.
I will now update `config.py` to include the `+` character in the `allowed_special_chars` string, which should resolve the failing test.
I will run the tests again using `python3 -m pytest` to verify that the fix works and all tests pass.
I will remove the bug comment from `config.py` as the issue has been resolved.
I will perform a final test run with `python3 -m pytest` to ensure everything is still working correctly after the comment removal.
I have fixed the root cause of the `test_email_with_plus` failure. The issue was in `config.py`, where the `+` character was missing from the `allowed_special_chars` setting used by the email validator. I added `+` to the allowed characters and verified that all tests in `test_validation.py` now pass.