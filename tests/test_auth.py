import pytest
from httpx import AsyncClient
from app import schemas, auth
from operations import auth_operation


@pytest.mark.asyncio
async def test_create_user(db_session):
    """
    Unit test for auth_operation.create_user
    """
    email = "user@example.com"
    password = "password123"
    role = schemas.UserRole.user

    hashed_password = auth.hash_password(password)
    user = await auth_operation.create_user(
        db=db_session,
        email=email,
        hashed_password=hashed_password,
        role=role
    )

    assert user.id is not None
    assert user.email == email
    assert user.role == role
    assert user.hashed_password != password


@pytest.mark.asyncio
async def test_get_user_by_email(db_session):
    """
    Unit test for auth_operation.get_user_by_email
    """
    email = "ali@example.com"
    password = "password123"
    hashed_password = auth.hash_password(password)

    # Ensure user is created for test
    await auth_operation.create_user(
        db=db_session,
        email=email,
        hashed_password=hashed_password,
        role=schemas.UserRole.user
    )

    user = await auth_operation.get_user_by_email(db_session, email)
    assert user is not None
    assert user.email == email


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    """
    API test for successful signup
    """
    payload = {
        "email": "signup@example.com",
        "password": "strongpassword",
        "role": "user"
    }

    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == payload["role"]
    assert "id" in data


@pytest.mark.asyncio
async def test_signup_existing_email(client: AsyncClient):
    """
    API test for signup with existing email
    """
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "role": "user"
    }

    # First signup
    await client.post("/auth/signup", json=payload)
    # Second signup should fail
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    API test for successful login
    """
    email = "login@example.com"
    password = "mypassword"
    # Signup first
    await client.post(
        "/auth/signup",
        json={"email": email, "password": password, "role": "user"}
        )

    form_data = {"username": email, "password": password}
    response = await client.post("/auth/login", data=form_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """
    API test for login with wrong password
    """
    email = "wrongpass@example.com"
    password = "correctpass"
    await client.post(
        "/auth/signup",
        json={"email": email, "password": password, "role": "user"}
        )

    form_data = {"username": email, "password": "wrongpass"}
    response = await client.post("/auth/login", data=form_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """
    API test for login with non-existent user
    """
    form_data = {"username": "nouser@example.com", "password": "any"}
    response = await client.post("/auth/login", data=form_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
