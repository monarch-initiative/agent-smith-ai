import os
from datetime import datetime
import json
import requests
from asteval import Interpreter
from collections import Counter
from math import log2
from typing import Optional, Literal


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

    def echo(self, x):
        """Returns the given input."""
        return x

    def time(self):
        """Returns the current time."""
        now = datetime.now()
        formatted_now = now.strftime("%m/%d/%y %H:%M")
        return formatted_now

    def entropy(self, lst):
        """Returns the entropy of the given list."""
        counter = Counter(lst)
        probabilities = [count/len(lst) for count in counter.values()]
        return -sum(p * log2(p) for p in probabilities)
    
    # endpoints: {"openapi":"3.0.2","info":{"url": "http://localhost:3434/", "title":"Monarch","version":"0.1.0"},"paths":{"/search":{"get":{"summary":"Search for entities in the Monarch knowledge graph","description":"Search for entities in the Monarch knowledge graph","operationId":"search_entity","parameters":[{"description":"The ontology term to search for.","required":true,"schema":{"title":"Term","type":"string","description":"The ontology term to search for."},"name":"term","in":"query"},{"description":"A single category to search within as a string. Valid categories are: biolink:Disease, biolink:PhenotypicQuality, and biolink:Gene","required":false,"schema":{"title":"Category","type":"string","description":"A single category to search within as a string. Valid categories are: biolink:Disease, biolink:PhenotypicQuality, and biolink:Gene","default":"biolink:Disease"},"example":"biolink:Disease","name":"category","in":"query"},{"description":"The maximum number of search results to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of search results to return.","default":2},"name":"limit","in":"query"},{"description":"Offset for pagination of results","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"Search results for the given ontology term","content":{"application/json":{"schema":{"$ref":"#/components/schemas/SearchResultItems"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/disease-genes":{"get":{"summary":"Get a list of genes associated with a disease","description":"Get a list of genes associated with a disease","operationId":"get_disease_gene_associations","parameters":[{"description":"The ontology identifier of the disease.","required":true,"schema":{"title":"Disease Id","type":"string","description":"The ontology identifier of the disease."},"example":"MONDO:0009061","name":"disease_id","in":"query"},{"description":"The maximum number of associations to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of associations to return.","default":10},"name":"limit","in":"query"},{"description":"Offset for pagination of results","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A GeneAssociations object containing a list of GeneAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/GeneAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/disease-phenotypes":{"get":{"summary":"Get a list of phenotypes associated with a disease","description":"Get a list of phenotypes associated with a disease","operationId":"get_disease_phenotype_associations","parameters":[{"description":"The ontology identifier of the disease.","required":true,"schema":{"title":"Disease Id","type":"string","description":"The ontology identifier of the disease."},"example":"MONDO:0009061","name":"disease_id","in":"query"},{"description":"The maximum number of associations to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of associations to return.","default":10},"name":"limit","in":"query"},{"description":"Offset for pagination of results.","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results.","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A PhenotypeAssociations object containing a list of PhenotypeAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/PhenotypeAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/gene-diseases":{"get":{"summary":"Get a list of diseases associated with a gene","description":"Get a list of diseases associated with a gene","operationId":"get_gene_disease_associations","parameters":[{"description":"The ontology identifier of the gene.","required":true,"schema":{"title":"Gene Id","type":"string","description":"The ontology identifier of the gene."},"example":"HGNC:1884","name":"gene_id","in":"query"},{"description":"The maximum number of associations to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of associations to return.","default":10},"name":"limit","in":"query"},{"description":"Offset for pagination of results","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A DiseaseAssociations object containing a list of DiseaseAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/DiseaseAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/gene-phenotypes":{"get":{"summary":"Get a list of phenotypes associated with a gene","description":"Get a list of phenotypes associated with a gene","operationId":"get_gene_phenotype_associations","parameters":[{"description":"The ontology identifier of the gene.","required":true,"schema":{"title":"Gene Id","type":"string","description":"The ontology identifier of the gene."},"example":"HGNC:1884","name":"gene_id","in":"query"},{"description":"The maximum number of associations to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of associations to return.","default":10},"name":"limit","in":"query"},{"description":"Offset for pagination of results","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A PhenotypeAssociations object containing a list of PhenotypeAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/PhenotypeAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/phenotype-diseases":{"get":{"summary":"Get a list of diseases associated with a phenotype","description":"Get a list of diseases associated with a phenotype","operationId":"get_phenotype_disease_associations","parameters":[{"description":"The ontology identifier of the phenotype.","required":true,"schema":{"title":"Phenotype Id","type":"string","description":"The ontology identifier of the phenotype."},"example":"HP:0002721","name":"phenotype_id","in":"query"},{"required":false,"schema":{"title":"Limit","type":"integer","default":10},"name":"limit","in":"query"},{"required":false,"schema":{"title":"Offset","type":"integer","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A DiseaseAssociations object containing a list of DiseaseAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/DiseaseAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}},"/phenotype-genes":{"get":{"summary":"Get a list of genes associated with a phenotype","description":"Get a list of genes associated with a phenotype","operationId":"get_phenotype_gene_associations","parameters":[{"description":"The ontology identifier of the phenotype.","required":true,"schema":{"title":"Phenotype Id","type":"string","description":"The ontology identifier of the phenotype."},"example":"HP:0002721","name":"phenotype_id","in":"query"},{"description":"The maximum number of associations to return.","required":false,"schema":{"title":"Limit","type":"integer","description":"The maximum number of associations to return.","default":10},"name":"limit","in":"query"},{"description":"Offset for pagination of results","required":false,"schema":{"title":"Offset","type":"integer","description":"Offset for pagination of results","default":1},"name":"offset","in":"query"}],"responses":{"200":{"description":"A GeneAssociations object containing a list of GeneAssociation objects","content":{"application/json":{"schema":{"$ref":"#/components/schemas/GeneAssociations"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}}},"components":{"schemas":{"Disease":{"title":"Disease","required":["id","label"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the disease.","example":"MONDO:0009061"},"label":{"title":"Label","type":"string","description":"The human-readable label of the disease.","example":"cystic fibrosis"}}},"DiseaseAssociation":{"title":"DiseaseAssociation","required":["id","disease"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the association."},"disease":{"$ref":"#/components/schemas/Disease"}}},"DiseaseAssociations":{"title":"DiseaseAssociations","required":["associations","total"],"type":"object","properties":{"associations":{"title":"Associations","type":"array","items":{"$ref":"#/components/schemas/DiseaseAssociation"},"description":"The list of DiseaseAssociation objects."},"total":{"title":"Total","type":"integer","description":"The total number of disease associations available."}}},"Gene":{"title":"Gene","required":["id","label"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the gene.","example":"HGNC:1884"},"label":{"title":"Label","type":"string","description":"The human-readable label of the gene.","example":"CFTR"}}},"GeneAssociation":{"title":"GeneAssociation","required":["id","gene"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the association."},"gene":{"$ref":"#/components/schemas/Gene"}}},"GeneAssociations":{"title":"GeneAssociations","required":["associations","total"],"type":"object","properties":{"associations":{"title":"Associations","type":"array","items":{"$ref":"#/components/schemas/GeneAssociation"},"description":"The list of GeneAssociation objects."},"total":{"title":"Total","type":"integer","description":"The total number of gene associations available."}}},"HTTPValidationError":{"title":"HTTPValidationError","type":"object","properties":{"detail":{"title":"Detail","type":"array","items":{"$ref":"#/components/schemas/ValidationError"}}}},"Phenotype":{"title":"Phenotype","required":["id","label"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the phenotype.","example":"HP:0002721"},"label":{"title":"Label","type":"string","description":"The human-readable label of the phenotype.","example":"Immunodeficiency"}}},"PhenotypeAssociation":{"title":"PhenotypeAssociation","required":["id","phenotype"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the association."},"frequency_qualifier":{"title":"Frequency Qualifier","type":"string","description":"The frequency qualifier of the association."},"onset_qualifier":{"title":"Onset Qualifier","type":"string","description":"The onset qualifier of the association."},"phenotype":{"$ref":"#/components/schemas/Phenotype"}}},"PhenotypeAssociations":{"title":"PhenotypeAssociations","required":["associations","total"],"type":"object","properties":{"associations":{"title":"Associations","type":"array","items":{"$ref":"#/components/schemas/PhenotypeAssociation"},"description":"The list of PhenotypeAssociation objects."},"total":{"title":"Total","type":"integer","description":"The total number of phenotype associations available."}}},"SearchResultItem":{"title":"SearchResultItem","required":["id","name","categories"],"type":"object","properties":{"id":{"title":"Id","type":"string","description":"The ontology identifier of the search result.","example":"MONDO:0009061"},"name":{"title":"Name","type":"string","description":"The name of the search result.","example":"cystic fibrosis"},"categories":{"title":"Categories","type":"array","items":{"type":"string"},"description":"The categories of the search result.","example":["biolink:Disease"]},"description":{"title":"Description","type":"string","description":"The description of the search result.","example":"Cystic fibrosis (CF) is a genetic disorder characterized by the production of sweat with a high salt content and mucus secretions with an abnormal viscosity."}}},"SearchResultItems":{"title":"SearchResultItems","required":["results","total"],"type":"object","properties":{"results":{"title":"Results","type":"array","items":{"$ref":"#/components/schemas/SearchResultItem"},"description":"A list of SearchResultItem objects."},"total":{"title":"Total","type":"integer","description":"The total number of search results available."}}},"ValidationError":{"title":"ValidationError","required":["loc","msg","type"],"type":"object","properties":{"loc":{"title":"Location","type":"array","items":{"anyOf":[{"type":"string"},{"type":"integer"}]}},"msg":{"title":"Message","type":"string"},"type":{"title":"Error Type","type":"string"}}}}}}

    

    def search_monarch(self, term: str, category: Literal["biolink:Disease", "biolink:PhenotypicQuality", "biolink:Gene"] = "biolink:Disease", limit: Optional[int] = 5, offset: Optional[int] = 0) -> str:
        """Returns the search results for the given term from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/search?term={term}&category={category}&limit={limit}&offset={offset}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)


    def get_disease_gene_associations(self, disease_id: str, limit: Optional[int], offset: Optional[int]) -> str:
        """Returns the genes associated with the given disease from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/disease-genes?disease_id={disease_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()


        return json.dumps(response_json)


    def get_disease_phenotype_associations(self, disease_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the phenotypes associated with the given disease from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/disease-phenotypes?disease_id={disease_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    

    def get_phenotype_gene_associations(self, phenotype_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the genes associated with the given phenotype from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/phenotype-genes?phenotype_id={phenotype_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    
    def get_phenotype_disease_associations(self, phenotype_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the diseases associated with the given phenotype from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/phenotype-diseases?phenotype_id={phenotype_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    
    def get_gene_disease_associations(self, gene_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the diseases associated with the given gene from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/gene-diseases?gene_id={gene_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)
    
    def get_gene_phenotype_associations(self, gene_id: str, limit: Optional[int] = 10, offset: Optional[int] = 0) -> str:
        """Returns the phenotypes associated with the given gene from the oai-monarch-wrapper."""

        url = f"{MONARCH_WRAPPER_BASE_URL}/gene-phenotypes?gene_id={gene_id}&limit={limit}&offset={offset + 1}"
        response_json = requests.get(url).json()

        return json.dumps(response_json)