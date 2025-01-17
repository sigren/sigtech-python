import os
import requests
import time
import logging
import urllib.parse
from typing import Optional, List
from sigtech.api.client.utils import snake_to_camel, singular
from sigtech.api.client.response import Response

logger = logging.getLogger(__name__)


class Client:
    """
    This is the Client class that represents an API client for SigTech.
    """

    def __init__(self, api_key: Optional[str] = None, url: Optional[str] = None,
                 session: Optional[requests.Session] = None, _base_url: Optional[str] = None,
                 wait_timeout: Optional[int] = 60):
        """
        Initialize a Client object.

        :param api_key: The API key for SigTech. Defaults to None.
        :param url: The URL of the API. Defaults to None.
        :param session: The current session. Defaults to None.
        :param _base_url: The base URL of the API. Defaults to None.
        :param wait_timeout: Timeout for waiting for final object status in seconds. Defaults to 60 seconds.
        """
        self._url = url or os.environ.get('SIGTECH_API_URL', 'https://api.sigtech.com')
        self._base_url = _base_url or self._url
        self._api_key = api_key or os.environ.get('SIGTECH_API_KEY', '')

        if self._api_key == '':
            raise ValueError('Please provide a SigTech API key.')

        self._session = session or requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
        })

        self.wait_timeout = wait_timeout

    @property
    def namespace(self) -> str:
        """
        Returns the namespace of the Client.

        :return: The namespace.
        """
        return self._url.split("/")[-1]

    def create(self, **kwargs) -> Response:
        """
        Create a new resource.

        :param kwargs: The arguments for creating a resource.
        :return: A Response object representing the result.
        """
        obj = {snake_to_camel(k): v for (k, v) in kwargs.items()}
        logger.debug(f"POST {self._url} {obj}")
        resp = self._session.post(self._url, json=obj)
        if resp.status_code != 200:
            logger.error(f"API REQUEST ERROR - {resp.content}")
            resp.raise_for_status()
        return Response(resp.json(), name=singular(self.namespace), client=self, kwargs=kwargs)

    def list(self) -> List[Response]:
        """
        List all resources.

        :return: A list of Response objects representing the resources.
        """
        logger.debug(f"GET {self._url}")
        resp = self._session.get(self._url)
        if resp.status_code != 200:
            logger.error(f"API REQUEST ERROR - {resp.content}")
            resp.raise_for_status()
        return [Response(o, name=singular(self.namespace)) for o in resp.json()[self.namespace]]

    def get(self, id: Optional[str] = '', **kwargs) -> Response:
        """
        Get a specific resource.

        :param id: The ID of the resource. Defaults to ''.
        :param kwargs: The arguments for getting a resource.
        :return: A Response object representing the resource.
        """
        url = f"{self._url}/{id}".rstrip("/")
        if kwargs:
            d = {snake_to_camel(k): v for (k, v) in kwargs.items()}
            url += '?' + urllib.parse.urlencode(d)
        logger.debug(f"GET {url}")
        resp = self._session.get(url)

        if resp.status_code != 200:
            logger.error(f"API REQUEST ERROR - {resp.content}")
            resp.raise_for_status()

        return Response(resp.json(), name=singular(self.namespace), client=self)

    def query_object(self, session_id: str, object_id: str) -> Response:
        """
        Query a specific object in a session.

        :param session_id: The ID of the session.
        :param object_id: The ID of the object.
        :return: A Response object representing the object.
        """
        resp = Client(
            api_key=self._api_key,
            url=f"{self._base_url}/sessions/{session_id}/objects/{object_id}",
            session=self._session
        ).get()
        return resp

    def wait_for_object_status(self, session_id: str, object_id: str, property_name: Optional[str]=None, timeout: Optional[int]=None) -> Response:
        """
        Wait for a specific object in a session to reach a final status or to contain a property.

        :param session_id: The ID of the session.
        :param object_id: The ID of the object.
        :param property_name: The property to wait for. Defaults to None.
        :param timeout: The maximum time to wait in seconds. Defaults to None.
        :return: A Response object representing the object.
        """
        timeout = timeout or self.wait_timeout
        t0 = time.monotonic()
        status = None
        sleep_count = 1

        while status != "SUCCEEDED":
            resp = self.query_object(session_id, object_id)

            status = resp.status

            if status == 'FAILED':
                logger.debug(f"FAILED TASK {str(resp)}")
                break

            if property_name is not None:
                if getattr(resp, property_name) is not None:
                    status = "SUCCEEDED"
                else:
                    status = 'RUNNING'

            time.sleep(sleep_count)
            t1 = time.monotonic()
            sleep_count = min(max(1, timeout - (t1 - t0)), sleep_count * 2)

            if (t1 - t0) > timeout:
                raise TimeoutError(f"Timeout waiting for object_id={object_id}")

        return resp

    def __getattr__(self, item: str) -> 'Client':
        """
        Get an attribute of the Client.

        :param item: The name of the attribute.
        :return: The attribute.
        """
        return Client(self._api_key, f"{self._url}/{item}", self._session, self._base_url)
