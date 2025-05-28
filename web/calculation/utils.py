import json
import traceback
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from loguru import logger


def log_error(error, source, user=None):
    """
    Log an error to the database and console
    """
    from .models import ErrorLog
    
    error_detail = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
    }
    
    error_log = ErrorLog.objects.create(
        error_type=type(error).__name__,
        error_message=str(error),
        source=source,
        traceback=traceback.format_exc(),
        user=user,
        details=json.dumps(error_detail, ensure_ascii=False)
    )
    
    logger.error(f"Error in {source}: {error}")
    logger.error(traceback.format_exc())
    
    return error_log


def handle_view_exception(view_func):
    """
    Decorator for view functions to catch and log exceptions
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            error_log = log_error(
                error=e,
                source=f"{view_func.__module__}.{view_func.__name__}",
                user=request.user if request.user.is_authenticated else None
            )
            
            # If this is an AJAX request, return JSON error
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Произошла ошибка при обработке запроса.',
                    'error_id': error_log.id,
                    'detail': str(e) if settings.DEBUG else None
                }, status=500)
            
            # Otherwise render error template
            return render(request, 'calculation/error.html', {
                'error_log': error_log,
                'show_details': settings.DEBUG,
            })
    
    return wrapper


def handle_service_exception(service_func):
    """
    Decorator for service functions to catch and log exceptions
    """
    @wraps(service_func)
    def wrapper(*args, **kwargs):
        try:
            return service_func(*args, **kwargs)
        except Exception as e:
            error_log = log_error(
                error=e,
                source=f"{service_func.__module__}.{service_func.__name__}"
            )
            
            logger.error(f"Service error in {service_func.__name__}: {e}")
            
            # Re-raise with additional context
            raise type(e)(f"{str(e)} (Error ID: {error_log.id})") from e
    
    return wrapper


def handle_api_exception(api_func):
    """
    Decorator for API interaction functions to catch and log exceptions
    """
    @wraps(api_func)
    def wrapper(*args, **kwargs):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            error_source = f"{api_func.__module__}.{api_func.__name__}"
            
            # Special handling for API-related exceptions
            if hasattr(e, 'response'):
                try:
                    response_text = e.response.text
                    status_code = e.response.status_code
                    error_detail = {
                        'status_code': status_code,
                        'response_text': response_text,
                        'url': e.response.url,
                        'method': e.response.request.method,
                    }
                    
                    logger.error(f"API error in {error_source}: {status_code}")
                    logger.error(f"API response: {response_text}")
                    
                    from .models import ErrorLog
                    error_log = ErrorLog.objects.create(
                        error_type="APIError",
                        error_message=f"API responded with {status_code}",
                        source=error_source,
                        traceback=traceback.format_exc(),
                        details=json.dumps(error_detail, ensure_ascii=False)
                    )
                    
                    # Re-raise with additional context
                    raise type(e)(f"API responded with {status_code} (Error ID: {error_log.id})") from e
                    
                except Exception as inner_e:
                    # Fall back to standard error handling if we can't parse the response
                    error_log = log_error(inner_e, error_source)
                    raise type(e)(f"{str(e)} (Error ID: {error_log.id})") from e
            else:
                # Standard error handling
                error_log = log_error(e, error_source)
                raise type(e)(f"{str(e)} (Error ID: {error_log.id})") from e
    
    return wrapper