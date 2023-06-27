import os
from datetime import datetime
import json
import requests
from asteval import Interpreter
from collections import Counter
from math import log2
from typing import Optional, Literal

import dotenv
dotenv.load_dotenv()


MONARCH_WRAPPER_BASE_URL = "http://localhost:3434"
if "MONARCH_WRAPPER_BASE_URL" in os.environ:
    MONARCH_WRAPPER_BASE_URL = os.environ["MONARCH_WRAPPER_BASE_URL"]

class SafeEval:
    """A class that provides a safe set of callable functions for use in the OpenAI plugin.
    It uses the asteval library to evaluate the functions.
    Example usage: safe_eval = SafeEval(); safe_eval.evaluate('time()')  # returns the current time)"""
    def __init__(self):
        self.interpreter = Interpreter()
        self._add_methods()

    def _add_methods(self):
        """Adds all methods of the class to the interpreter's symbol table, so they can be called by the user."""
        # Get all methods of the class
        methods = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("_")]
        # Add them to the interpreter's symbol table
        for method in methods:
            self.interpreter.symtable[method] = getattr(self, method)


    def evaluate(self, expression: str) -> str:
        """Evaluates the given expression using the interpreter's symbol table."""
        try:
            return self.interpreter(expression)
        except Exception as e:
            return f"Error: {e}. Are you trying to use functionality that is not available?"


    def generate_function_schemas(self):
        """Generates a list of JSON schemas describing the safe functions."""
        function_schemas = []
        # Get all methods of the class
        methods = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("_")]
        # Iterate over the methods and build the schema for each
        for method_name in methods:
            method = getattr(self, method_name)
            if hasattr(method, "schema"):
                function_schemas.append(method.schema)

        return function_schemas


    def get_function(self, name: str):
        """Returns the function with the given name."""
        return getattr(self, name)


    def echo(self, x):
        """Returns the given input string."""
        return x
    echo.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'x': {'type': 'string', 'description': 'The input to return'}
            }
        },
        "name": "echo",
        "description": "Returns the given input string.",
        "required": ["x"]
    }

    def time(self):
        """Returns the current time."""
        now = datetime.now()
        formatted_now = now.strftime("%m/%d/%y %H:%M")
        return formatted_now
    time.schema = {
        "parameters": {        
            "type": "object",
            "properties": {}
        },
        "name": "time",
        "description": "Returns the current time."
    }

    def set_show_function_calls(self, show: bool) -> bool:
        os.environ["SHOW_FUNCTION_CALLS"] = str(show)
        return show
    set_show_function_calls.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'show': {
                    'type': 'boolean', 
                    'description': 'Whether to show function calls in the output.'
                }
            }
        },
        "name": "set_show_function_calls",
        "description": "Sets whether to show function calls in the output.",
        "required": ["show"]
    }

    def entropy(self, lst):
        """Returns the entropy of the given list."""
        counter = Counter(lst)
        probabilities = [count/len(lst) for count in counter.values()]
        return -sum(p * log2(p) for p in probabilities)
    entropy.schema = {
        "parameters": {
        "type": "object",
        "properties": {
            'lst': {'type': 'array', 
                    'description': 'The list to calculate the entropy of.', 
                    'items': {'type': 'number'}}
            }
        },
        "name": "entropy",
        "description": "Returns the entropy of the given list.",
        "required": ["lst"]
    }

    def search_monarch(self, term: str, category: Literal["biolink:Disease", "biolink:PhenotypicQuality", "biolink:Gene"] = "biolink:Disease", limit: Optional[int] = 5, offset: Optional[int] = 0) -> str:
        """Returns the search results for the given term"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/search?term={term}&category={category}&limit={limit}&offset={offset}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    search_monarch.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'term': {'type': 'string', 'description': 'The term to search for.'},
                'category': {'type': 'string', 'description': 'The category to search in.', 'enum': ['biolink:Disease', 'biolink:PhenotypicQuality', 'biolink:Gene'], 'default': 'biolink:Disease'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results.', 'default': 0}
            }
        },
        "name": "search_monarch",
        "description": "Returns the search results for the given term",
        "required": ["term"]
    }


    def get_disease_gene_associations(self, disease_id: str, limit: int = 10, offset: int = 1) -> str:
        """Returns the genes associated with the given disease"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/disease-genes?disease_id={disease_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_disease_gene_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'disease_id': {'type': 'string', 'description': 'The disease ID to get the gene associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }
        },
        "name": "get_disease_gene_associations",
        "description": "Returns the genes associated with the given disease",
        "required": ["disease_id"]
    }

    def get_disease_phenotype_associations(self, disease_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the phenotypes associated with the given disease"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/disease-phenotypes?disease_id={disease_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_disease_phenotype_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'disease_id': {'type': 'string', 'description': 'The disease ID to get the phenotype associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }
        },
        "name": "get_disease_phenotype_associations",
        "description": "Returns the phenotypes associated with the given disease",
        "required": ["disease_id"]
    }

   

    def get_phenotype_gene_associations(self, phenotype_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the genes associated with the given phenotype"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/phenotype-genes?phenotype_id={phenotype_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_phenotype_gene_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'phenotype_id': {'type': 'string', 'description': 'The phenotype ID to get the gene associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }
        },
        "name": "get_phenotype_gene_associations",
        "description": "Returns the genes associated with the given phenotype"
    }

    
    def get_phenotype_disease_associations(self, phenotype_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the diseases associated with the given phenotype"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/phenotype-diseases?phenotype_id={phenotype_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_phenotype_disease_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'phenotype_id': {'type': 'string', 'description': 'The phenotype ID to get the disease associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }
        },
        "name": "get_phenotype_disease_associations",
        "description": "Returns the diseases associated with the given phenotype"
    }
    
    def get_gene_disease_associations(self, gene_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the diseases associated with the given gene"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/gene-diseases?gene_id={gene_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_gene_disease_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'gene_id': {'type': 'string', 'description': 'The gene ID to get the disease associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }   
        },
        "name": "get_gene_disease_associations",
        "description": "Returns the diseases associated with the given gene"
    }

    
    def get_gene_phenotype_associations(self, gene_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the phenotypes associated with the given gene"""

        url = f"{MONARCH_WRAPPER_BASE_URL}/gene-phenotypes?gene_id={gene_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    get_gene_phenotype_associations.schema = {
        "parameters": {
            "type": "object",
            "properties": {
                'gene_id': {'type': 'string', 'description': 'The gene ID to get the phenotype associations for.'},
                'limit': {'type': 'number', 'description': 'The maximum number of results to return.', 'default': 5},
                'offset': {'type': 'number', 'description': 'The offset to start returning results', 'default': 0}
            }
        },
        "name": "get_gene_phenotype_associations",
        "description": "Returns the phenotypes associated with the given gene"
    }
