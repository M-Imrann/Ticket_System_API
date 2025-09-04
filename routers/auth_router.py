from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, auth, database
from operations import auth_operation


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=schemas.UserRead)
async def signup(
        payload: schemas.UserCreate,
        db: AsyncSession = Depends(database.get_db)
        ):
    """
    Register a new user.

    Args:
        payload: User registration data.
        db: Database session dependency.

    Returns:
        The created user object if successful.

    Raises:
        HTTPException: If the email is already registered.
    """
    # Check if user already exists
    existing_user = await auth_operation.get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    # Create new user
    user = await auth_operation.create_user(
        db=db,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        role=payload.role,
    )
    return user


@router.post("/login", response_model=schemas.Token)
async def login(
        form: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(database.get_db)
        ):
    """
    Authenticate user and return access token.

    Args:
        form: OAuth2 password request form dependency.
        db: Database session dependency.

    Returns:
        Token object if authentication is successful.

    Raises:
        HTTPException: If credentials are incorrect.
    """
    # Authenticate user
    user = await auth.authenticate_user(
        db,
        email=form.username,
        password=form.password
    )
    if user is None:
        # Determine if user exists for better error message
        user_exists = await auth_operation.get_user_by_email(db, form.username)
        if not user_exists:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Incorrect password"
            )
    # Create JWT token
    token = auth.create_access_token({"sub": user.email})
    return schemas.Token(access_token=token)
