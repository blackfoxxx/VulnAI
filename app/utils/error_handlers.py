from fastapi import Request
from fastapi.responses import JSONResponse
from .logger import log_error

class VulnLearnAIError(Exception):
    """Base exception class for VulnLearnAI"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(VulnLearnAIError):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AuthenticationError(VulnLearnAIError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class TrainingError(VulnLearnAIError):
    """Raised when model training fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

async def vulnlearnai_exception_handler(request: Request, exc: VulnLearnAIError):
    """Handle VulnLearnAI specific exceptions"""
    log_error(f"VulnLearnAI Error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message
        }
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    log_error(f"Validation Error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "message": exc.message
        }
    )

async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    log_error(f"Authentication Error: {exc.message}")
    return JSONResponse(
        status_code=401,
        content={
            "error": "AuthenticationError",
            "message": exc.message
        }
    )

async def training_exception_handler(request: Request, exc: TrainingError):
    """Handle model training errors"""
    log_error(f"Training Error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "TrainingError",
            "message": exc.message
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions"""
    log_error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(VulnLearnAIError, vulnlearnai_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(TrainingError, training_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
