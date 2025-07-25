# Acme Corp

## Purpose

Acme Corp is a fictional company that sells products to customers. They act as a test brand for GetGather. There are CI tests that run which spin up the Acme Corp website and run the GetGather test yamls against it.

## Running the tests

The ACME tests run via `pytest`, and are making API calls to the `getgather` API server, which is accessing the Acme Corp website.

1.  **Start the main API server** in one terminal:

    ```bash
    uv run poe web
    ```

2.  **Start the ACME Corp server** in another terminal (the command below does this):

    ```bash
    poe acme-corp
    ```

3.  **Run the tests** in a third terminal.

    To run all ACME authentication tests:

    ```bash
    uv run pytest -m "api and acme" tests/api/test_acme_auth.py
    ```

    To run a specific test (which usually corresponds to the yaml file name), use the `-k` flag:

    ```bash
    uv run pytest -m "api and acme" tests/api/test_acme_auth.py -k "acme-email-password-fsm"
    ```

Success is marked by successfully authenticating (measured by there being being an exit code of 0)
