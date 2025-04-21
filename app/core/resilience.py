"""
Resilience utilities for handling cross-service communication failures.

This module provides utility functions and classes to implement resilience patterns
such as retry with exponential backoff, circuit breakers, and fallbacks.
"""
import logging
import time
import random
import asyncio
from functools import wraps
from typing import Callable, TypeVar, Any, Dict, Optional, Union, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

# Type variables for function signatures
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class CircuitState(Enum):
    """States for the circuit breaker pattern."""
    CLOSED = "CLOSED"  # Normal operation, requests are allowed through
    OPEN = "OPEN"      # Circuit is open, requests are not allowed
    HALF_OPEN = "HALF_OPEN"  # Testing if the service is back online


class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern to prevent repeated calls to failing services.
    
    The circuit breaker tracks failures and opens the circuit when a threshold is reached,
    preventing further calls for a specified timeout period. After the timeout, it allows
    a test request to determine if the service has recovered.
    """
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_success_threshold: int = 1,
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before trying again
            half_open_success_threshold: Number of successful calls needed to close the circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_success_threshold = half_open_success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.success_count = 0
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed through the circuit breaker.
        
        Returns:
            bool: True if the request should be allowed, False otherwise
        """
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            current_time = time.time()
            if current_time - self.last_failure_time >= self.recovery_timeout:
                logger.info(f"Circuit {self.name} transitioning from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def on_success(self) -> None:
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                logger.info(f"Circuit {self.name} transitioning from HALF_OPEN to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def on_failure(self) -> None:
        """Record a failed request."""
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit {self.name} transitioning from CLOSED to OPEN due to {self.failure_count} failures")
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit {self.name} transitioning from HALF_OPEN back to OPEN due to failure")
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()


# Global registry of circuit breakers to maintain state across function calls
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.
    
    Args:
        name: The identifier for the circuit breaker
        
    Returns:
        CircuitBreaker: The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]


def with_retry(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions_to_retry: Tuple[Exception, ...] = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for each retry attempt
        jitter: Whether to add randomness to the delay
        exceptions_to_retry: Tuple of exceptions that should trigger a retry
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for retry_count in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    if retry_count == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(max_delay, base_delay * (backoff_factor ** retry_count))
                    
                    # Add jitter if enabled (prevents thundering herd)
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry {retry_count + 1}/{max_retries} for {func.__name__} "
                        f"after error: {str(e)}. Waiting {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            # This should never be reached due to the raise inside the loop
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for retry_count in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    if retry_count == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(max_delay, base_delay * (backoff_factor ** retry_count))
                    
                    # Add jitter if enabled (prevents thundering herd)
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry {retry_count + 1}/{max_retries} for {func.__name__} "
                        f"after error: {str(e)}. Waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            
            # This should never be reached due to the raise inside the loop
            raise last_exception
        
        # Return the appropriate wrapper based on if the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def with_circuit_breaker(
    circuit_name: str,
    fallback_function: Optional[Callable[..., Any]] = None,
    exceptions_to_trip: Tuple[Exception, ...] = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator that applies circuit breaker pattern to a function.
    
    Args:
        circuit_name: Name of the circuit breaker
        fallback_function: Function to call when circuit is open
        exceptions_to_trip: Exceptions that should count as failures
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            circuit = get_circuit_breaker(circuit_name)
            
            if not circuit.allow_request():
                logger.warning(f"Circuit {circuit_name} is OPEN, request not allowed")
                if fallback_function:
                    return fallback_function(*args, **kwargs)
                raise RuntimeError(f"Service unavailable: circuit {circuit_name} is OPEN")
            
            try:
                result = func(*args, **kwargs)
                circuit.on_success()
                return result
            except exceptions_to_trip as e:
                circuit.on_failure()
                raise
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            circuit = get_circuit_breaker(circuit_name)
            
            if not circuit.allow_request():
                logger.warning(f"Circuit {circuit_name} is OPEN, request not allowed")
                if fallback_function:
                    if asyncio.iscoroutinefunction(fallback_function):
                        return await fallback_function(*args, **kwargs)
                    else:
                        return fallback_function(*args, **kwargs)
                raise RuntimeError(f"Service unavailable: circuit {circuit_name} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                circuit.on_success()
                return result
            except exceptions_to_trip as e:
                circuit.on_failure()
                raise
        
        # Return the appropriate wrapper based on if the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


async def resilient_http_call(
    client: Any,
    method: str,
    url: str,
    circuit_name: str,
    max_retries: int = 3,
    timeout: float = 10.0,
    **kwargs: Any
) -> Any:
    """
    Make a resilient HTTP call using both retry and circuit breaker patterns.
    
    Args:
        client: HTTP client to use (typically httpx.AsyncClient)
        method: HTTP method (GET, POST, etc.)
        url: URL to call
        circuit_name: Name for the circuit breaker
        max_retries: Maximum number of retries
        timeout: Timeout for the HTTP request
        **kwargs: Additional arguments to pass to the request
        
    Returns:
        Any: Response from the HTTP call
    """
    circuit = get_circuit_breaker(circuit_name)
    
    if not circuit.allow_request():
        logger.warning(f"Circuit {circuit_name} is OPEN, request not allowed")
        raise RuntimeError(f"Service unavailable: circuit {circuit_name} is OPEN")
    
    # Set a default timeout if not already in kwargs
    if 'timeout' not in kwargs:
        kwargs['timeout'] = timeout
    
    last_exception = None
    
    for retry_count in range(max_retries + 1):
        try:
            # Make the HTTP request
            response = await getattr(client, method.lower())(url, **kwargs)
            
            # Check if the response was successful
            response.raise_for_status()
            
            # Record success and return response
            circuit.on_success()
            return response
            
        except Exception as e:
            last_exception = e
            
            # Record failure in circuit breaker
            circuit.on_failure()
            
            if retry_count == max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for {url}")
                raise
            
            # Calculate delay with exponential backoff
            delay = 0.5 * (2 ** retry_count)
            delay = min(10.0, delay * (0.5 + random.random()))  # Add jitter
            
            logger.warning(
                f"Retry {retry_count + 1}/{max_retries} for {url} "
                f"after error: {str(e)}. Waiting {delay:.2f}s"
            )
            await asyncio.sleep(delay)
    
    # This should never be reached due to the raise inside the loop
    raise last_exception


# Example fallback functions
def default_fallback_value(default_value: Any) -> Callable[..., Any]:
    """
    Create a fallback function that returns a default value.
    
    Args:
        default_value: The value to return from the fallback
        
    Returns:
        Callable: A fallback function
    """
    def fallback(*args: Any, **kwargs: Any) -> Any:
        return default_value
    return fallback


def log_and_rethrow_fallback(error_message: str) -> Callable[..., Any]:
    """
    Create a fallback function that logs an error and re-raises the exception.
    
    Args:
        error_message: The error message to log
        
    Returns:
        Callable: A fallback function that raises an exception
    """
    def fallback(*args: Any, **kwargs: Any) -> Any:
        logger.error(error_message)
        raise RuntimeError(error_message)
    return fallback
