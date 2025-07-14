# Guidance for Task

This codebase is a partially implemented FastAPI microservice for authenticated asynchronous order processing and status tracking. It provides the basic application skeleton for a secure and production-like order API. Your task is to enhance and complete the implementation so all endpoints and features work robustly as described below.

## What You Are Expected To Do

- Ensure *all* endpoints require authentication and only allow users to manage their own orders.
- Implement input validation using Pydantic models with strong constraints.
- Make sure submitted orders are persisted with status tracking (PENDING, PROCESSING, COMPLETED) using SQLAlchemy and SQLite.
- Integrate asynchronous order processing using FastAPI's BackgroundTasks (without Celery or any external queue).
- Implement detailed HTTP error responses for invalid submissions or unauthorized/forbidden requests.
- Provide endpoints for users to submit new orders and check the status of their orders individually or as a list.
- Secure all API endpoints with OAuth2 (PasswordBearer flow). Only authenticated users can access.
- Make the API robust and testable within a short time—avoid or fix race conditions or user information leaks.
- You may need to refactor or finish the skeleton implementation to meet these requirements.

## Verifying Your Solution

- Authenticate using OAuth2 and verify that only authorized users can submit and track their own orders.
- Validate that submitted orders comply with all requirements (field types, constraints).
- Check the order processing: after creation, order status should transition (PENDING → PROCESSING → COMPLETED) automatically in due time.
- Confirm proper HTTP status codes and detailed error messages are returned for all error scenarios (e.g., unauthenticated access, forbidden order lookup, invalid data).
- Ensure the SQLite database consistently stores all users and order data, and that the status transitions occur as expected.
- Confirm that user order isolation and input validation are enforced.

**Note:** Actual environment setup and running instructions are *not* provided here per assessment policy.
