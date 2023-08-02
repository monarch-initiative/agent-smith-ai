import requests
import json


class APIWrapper:
    def __init__(self, prefix, spec_url, base_url, callable_endpoints = []):
        self.prefix = prefix
        self.spec_url = spec_url
        self.base_url = base_url
        self.endpoints = self.parse_openapi_spec()

        if len(callable_endpoints) > 0:
            callable_endpoints = [prefix + "-" + ep for ep in callable_endpoints]
            self.endpoints = [ep for ep in self.endpoints if ep['name'] in callable_endpoints]

    def parse_openapi_spec(self):
        try:
            response = requests.get(self.spec_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

        try:
            spec = response.json()
        except json.JSONDecodeError as e:
            return {'error': f'Error parsing JSON: {str(e)}'}

        endpoints = []
        for path, path_item in spec['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'options', 'head', 'patch', 'trace']:
                    if 'description' in operation and 'operationId' in operation:
                        endpoint = {
                            'name': self.prefix + '-' + operation.get('operationId'),
                            'description': operation.get('description'),
                            'parameters': {
                                'type': 'object',
                                'properties': {},
                                'required': [param['name'] for param in operation.get('parameters', []) if param.get('required')],
                            },
                            'method': method,
                            'path': path
                        }
                        for param in operation.get('parameters', []):
                            endpoint['parameters']['properties'][param['name']] = param['schema']
                            endpoint['parameters']['properties'][param['name']]['in'] = param['in']
                        endpoints.append(endpoint)

        return endpoints

    def get_function_schemas(self):
        return self.endpoints
        function_schemas = []
        for ep in self.endpoints:
            if 'error' not in ep:
                schema = {
                    'name': ep['name'],
                    'description': ep['description'],
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            name: {k: v for k, v in info.items() if k != 'in'}
                            for name, info in ep['parameters']['properties'].items()
                        }
                    },
                    'required': ep['required']
                }
                function_schemas.append(schema)
        return function_schemas

    def call_endpoint(self, function_call):
        # Find the endpoint matching the function name
        endpoint = next((ep for ep in self.endpoints if ep['name'] == function_call['name']), None)
        if endpoint is None or 'error' in endpoint:
            return {'status_code': 400, 'data': None, 'error': f"Invalid function name: {function_call['name']}"}

        # Extract the method, path, and parameters
        method = endpoint['method']
        path = endpoint['path']
        all_parameters = function_call['arguments']

        # Separate query and body parameters
        query_params = {name: value for name, value in all_parameters.items()
                        if endpoint['parameters']['properties'][name]['in'] == 'query'}
        body_params = {name: value for name, value in all_parameters.items()
                       if endpoint['parameters']['properties'][name]['in'] == 'body'}

        # Construct the full URL
        url = self.base_url + path

        # Prepare the request
        if body_params:
            req = requests.Request(method, url, params=query_params, json=body_params)
        else:
            req = requests.Request(method, url, params=query_params)
        prepped = req.prepare()

        #print(f'Final URL: {prepped.url}')
        #print(f'Final body: {prepped.body}')

        # Make the API call and return the result
        with requests.Session() as session:
            try:
                response = session.send(prepped)
            except requests.exceptions.RequestException as e:
                return {'status_code': 500, 'data': None, 'error': str(e)}

        if response.status_code >= 400:
            return {
                'status_code': response.status_code,
                'data': None,
                'error': f"API returned HTTP error: {response.status_code}",
                'response_body': response.text
            }

        return {'status_code': response.status_code, 'data': response.json() if response.content else None}


class APIWrapperSet:
    def __init__(self, api_wrappers):
        self.api_wrappers = api_wrappers

    def add_api(self, name: str, spec_url: str, base_url: str, callable_endpoints = []):
        self.api_wrappers.append(APIWrapper(name, spec_url, base_url, callable_endpoints))

    def get_function_schemas(self):
        return [schema for wrapper in self.api_wrappers for schema in wrapper.get_function_schemas()]

    def get_function_names(self):
        return [schema['name'] for schema in self.get_function_schemas()]

    def call_endpoint(self, function_call):
        # Find the wrapper that can handle this function call
        wrapper = None
        for w in self.api_wrappers:
            for ep in w.endpoints:
                if ep['name'] == function_call['name']:
                    wrapper = w
                    break
            if wrapper is not None:
                break

        if wrapper is None:
            return {'status_code': 400, 'data': None, 'error': f"Invalid function name: {function_call['name']}"}

        # Delegate the function call to the appropriate wrapper
        return wrapper.call_endpoint(function_call)
