from greenspot.api.server import app

def test_global_exception_handler_configured():
    assert Exception in app.exception_handlers or 500 in app.exception_handlers

def test_cors_middleware_configured():
    has_cors = any(mw.cls.__name__ == 'CORSMiddleware' for mw in app.user_middleware)
    assert has_cors
