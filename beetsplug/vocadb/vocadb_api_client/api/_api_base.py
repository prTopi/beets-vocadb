from beetsplug.vocadb.vocadb_api_client.api_client import ApiClient


class ApiBase:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client: ApiClient = api_client
