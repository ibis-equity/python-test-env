import asyncio
import httpx
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AsyncAPIClient:
    """
    Async HTTP client for making asynchronous API calls.
    Supports GET, POST, PUT, DELETE operations with timeout and error handling.
    """
    
    def __init__(self, base_url: str = "", timeout: int = 30):
        """
        Initialize the async API client.
        
        Args:
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx.get()
        
        Returns:
            Response JSON as dictionary
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"GET request to {url}")
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return {
                'status_code': response.status_code,
                'data': response.json(),
                'timestamp': datetime.now().isoformat()
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on GET {endpoint}: {str(e)}")
            raise
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            **kwargs: Additional arguments for httpx.post()
        
        Returns:
            Response JSON as dictionary
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"POST request to {url} with data: {data}")
            response = await self.client.post(url, json=data, **kwargs)
            response.raise_for_status()
            return {
                'status_code': response.status_code,
                'data': response.json(),
                'timestamp': datetime.now().isoformat()
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on POST {endpoint}: {str(e)}")
            raise
    
    async def put(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            **kwargs: Additional arguments for httpx.put()
        
        Returns:
            Response JSON as dictionary
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"PUT request to {url} with data: {data}")
            response = await self.client.put(url, json=data, **kwargs)
            response.raise_for_status()
            return {
                'status_code': response.status_code,
                'data': response.json(),
                'timestamp': datetime.now().isoformat()
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on PUT {endpoint}: {str(e)}")
            raise
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx.delete()
        
        Returns:
            Response JSON as dictionary
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"DELETE request to {url}")
            response = await self.client.delete(url, **kwargs)
            response.raise_for_status()
            return {
                'status_code': response.status_code,
                'data': response.json() if response.text else {},
                'timestamp': datetime.now().isoformat()
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on DELETE {endpoint}: {str(e)}")
            raise


async def fetch_multiple_apis(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch data from multiple API endpoints concurrently.
    
    Args:
        urls: List of API URLs to fetch
    
    Returns:
        List of responses from all APIs
    
    Example:
        results = await fetch_multiple_apis([
            'https://api.github.com/users/github',
            'https://api.github.com/users/google'
        ])
    """
    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for url, response in zip(urls, responses):
            if isinstance(response, Exception):
                logger.error(f"Error fetching {url}: {str(response)}")
                results.append({
                    'url': url,
                    'status_code': None,
                    'error': str(response),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                results.append({
                    'url': url,
                    'status_code': response.status_code,
                    'data': response.json() if response.headers.get('content-type') == 'application/json' else response.text,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results


async def fetch_with_retry(url: str, max_retries: int = 3, delay: int = 1) -> Dict[str, Any]:
    """
    Fetch data from API with automatic retry on failure.
    
    Args:
        url: API URL to fetch
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    
    Returns:
        Response data or error information
    
    Example:
        result = await fetch_with_retry('https://api.example.com/data', max_retries=3)
    """
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                response = await client.get(url)
                response.raise_for_status()
                
                return {
                    'url': url,
                    'status_code': response.status_code,
                    'data': response.json(),
                    'attempt': attempt + 1,
                    'timestamp': datetime.now().isoformat()
                }
            
            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed for {url}")
                    return {
                        'url': url,
                        'status_code': None,
                        'error': str(e),
                        'attempts': max_retries,
                        'timestamp': datetime.now().isoformat()
                    }


async def main():
    """
    Example usage of async API calls.
    """
    print("=== Async API Call Examples ===\n")
    
    # Example 1: Single API call
    print("1. Single API Call Example")
    try:
        async with AsyncAPIClient(base_url="https://api.github.com") as client:
            result = await client.get("/users/github")
            print(f"Status: {result['status_code']}")
            print(f"User: {result['data'].get('login')}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 2: Multiple concurrent API calls
    print("2. Multiple Concurrent API Calls")
    urls = [
        "https://api.github.com/users/github",
        "https://api.github.com/users/google",
        "https://api.github.com/users/microsoft"
    ]
    try:
        results = await fetch_multiple_apis(urls)
        for result in results:
            if 'error' not in result:
                print(f"User: {result['data'].get('login')} - Repos: {result['data'].get('public_repos')}")
            else:
                print(f"Error fetching {result['url']}: {result['error']}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 3: Fetch with retry
    print("3. Fetch with Retry Example")
    try:
        result = await fetch_with_retry("https://api.github.com/users/github", max_retries=2)
        print(f"Status: {result.get('status_code')}")
        print(f"Attempt: {result.get('attempt')}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    # Run the async examples
    asyncio.run(main())
