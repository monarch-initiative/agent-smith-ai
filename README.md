# Agent Smith (AI)

Agent smith makes it easy to instantiate AI agents that can safely and easily call APIs and locally defined functions to interact with the world.

<!-- <img src="https://imgix.bustle.com/uploads/image/2021/12/7/cc0e73f8-0020-4c7f-9564-da20f309622d-agent-smith.jpg?w=350" alt="Agent Smith Matrix" /> -->

Be aware of the following:

* It is designed to use OpenAI's [function-calling models](https://platform.openai.com/docs/guides/gpt/function-calling) and thus requires an OpenAI API key.


## Examples

The `examples` directory provides some examples, including:

* `monarch_basic.py`: Illustrates how to extend the basic UtilityAgent to register APIs and define callable local methods, and how to interact with the agent by processing produced Message objects.
* `monarch_cli.py`: Illustrates extending the CLIAgent, which itself extends the UtilityAgent to provide a command-line chat interface.

Here's an example conversation from `monarch_cli.py` (sadly, markdown-defined colors and links are not shown here):


```
╭──────────────────────────────────────────── Welcome ─────────────────────────────────────────────╮
│ Hello! I'm the Monarch Assistant, an AI-powered chatbot that can answer questions about genes,   │
│ diseases, and phenotypes, based on information hosted at https://monarchinitiative.org.          │
│                                                                                                  │
│  • You can exit by saying 'exit', and you can request that I turn on or off function call        │
│    responses by saying 'show function calls' or 'hide function calls' at any time. They are      │
│    shown by default.                                                                             │
│  • I do not currently implement context-window management, so after a while your conversation    │
│    will produce an error.                                                                        │
│  • For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of   │
│    Cystic Fibrosis? Describe your plan before you execute it."                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: What are the symptoms of Cystic Fibrosis? Describe your plan before you execute it.

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│ To find the symptoms of Cystic Fibrosis, I will first search for the disease using the term      │
│ "Cystic Fibrosis" in the Monarch Initiative knowledge graph. Once I have the ontology identifier │
│ for Cystic Fibrosis, I will use it to retrieve the associated phenotypes. These phenotypes       │
│ represent the symptoms of the disease. I will then provide a description of the symptoms of      │
│ Cystic Fibrosis based on the retrieved information.                                              │
│                                                                                                  │
│ Here is my plan:                                                                                 │
│                                                                                                  │
│  1 Search for the disease "Cystic Fibrosis" in the Monarch Initiative knowledge graph.           │
│  2 Retrieve the ontology identifier for Cystic Fibrosis.                                         │
│  3 Use the ontology identifier to retrieve the associated phenotypes.                            │
│  4 Provide a description of the symptoms of Cystic Fibrosis based on the retrieved information.  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│                                                                                                  │
│  monarch-search_entity(params = {'term': 'Cystic Fibrosis', 'category': 'biolink:Disease',       │
│  'limit': 1})                                                                                    │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-search_entity function) -> Monarch Assistant ────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "results": [                                                                                │
│          {                                                                                       │
│              "id": "MONDO:0009061",                                                              │
│              "name": "cystic fibrosis",                                                          │
│              "categories": [                                                                     │
│                  "biolink:Disease"                                                               │
│              ],                                                                                  │
│              "description": "Cystic fibrosis (CF) is a genetic disorder characterized by the     │
│  production of sweat with a high salt content and mucus secretions with an abnormal viscosity."  │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 3                                                                                  │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-get_disease_phenotype_associations function) ───╮
│                                                                                                  │
│  monarch-get_disease_phenotype_associations(params = {'disease_id': 'MONDO:0009061', 'limit':    │
│  10})                                                                                            │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-get_disease_phenotype_associations function) -> Monarch Assistant ───╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0004401",                                                   │
│                  "label": "Meconium ileus (HPO)"                                                 │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0006528",                                                   │
│                  "label": "Chronic lung disease (HPO)"                                           │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0006538",                                                   │
│                  "label": "Recurrent bronchopulmonary infections (HPO)"                          │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0100582",                                                   │
│                  "label": "Nasal polyposis (HPO)"                                                │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002035",                                                   │
│                  "label": "Rectal prolapse (HPO)"                                                │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002099",                                                   │
│                  "label": "Asthma (HPO)"                                                         │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002150",                                                   │
│                  "label": "Hypercalciuria (HPO)"                                                 │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002595",                                                   │
│                  "label": "Ileus (HPO)"                                                          │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0002613",                                                   │
│                  "label": "Biliary cirrhosis (HPO)"                                              │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": null,                                                    │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0003251",                                                   │
│                  "label": "Male infertility (HPO)"                                               │
│              }                                                                                   │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 62,                                                                                │
│      "phenotype_url_template": "https://monarchinitiative.org/phenotype/{phenotype_id}"          │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The symptoms of Cystic Fibrosis include:                                                         │
│                                                                                                  │
│   1 Meconium ileus: This is a condition where the meconium, the first stool of a newborn, is     │
│     thick and sticky, causing a blockage in the intestines. More information                     │
│   2 Chronic lung disease: Cystic Fibrosis can lead to the development of chronic lung disease,   │
│     characterized by persistent respiratory symptoms such as coughing, wheezing, and shortness   │
│     of breath. More information                                                                  │
│   3 Recurrent bronchopulmonary infections: Individuals with Cystic Fibrosis are prone to         │
│     frequent and recurrent infections in the bronchial tubes and lungs. More information         │
│   4 Nasal polyposis: Cystic Fibrosis can cause the development of polyps in the nasal passages,  │
│     leading to nasal congestion and difficulty breathing through the nose. More information      │
│   5 Rectal prolapse: In some cases, Cystic Fibrosis can result in the protrusion of the rectum   │
│     through the anus. More information                                                           │
│   6 Asthma: Individuals with Cystic Fibrosis may also experience symptoms of asthma, such as     │
│     wheezing and difficulty breathing. More information                                          │
│   7 Hypercalciuria: Cystic Fibrosis can lead to increased levels of calcium in the urine, which  │
│     may result in the formation of kidney stones. More information                               │
│   8 Ileus: This refers to a blockage or obstruction in the intestines, which can occur in        │
│     individuals with Cystic Fibrosis. More information                                           │
│   9 Biliary cirrhosis: In rare cases, Cystic Fibrosis can lead to the development of liver       │
│     disease, specifically biliary cirrhosis. More information                                    │
│  10 Male infertility: Men with Cystic Fibrosis may experience infertility due to the absence or  │
│     blockage of the vas deferens, the tube that carries sperm from the testes. More information  │
│                                                                                                  │
│ Please note that this is not an exhaustive list of symptoms, and the severity and presentation   │
│ of symptoms can vary among individuals with Cystic Fibrosis. It is important to consult with a   │
│ healthcare professional for a comprehensive evaluation and diagnosis.                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: That's nice. I know you can call local functions too - can you do that and tell me what time it is?

╭─ Monarch Assistant -> Monarch Assistant (time function) ─────────────────────────────────────────╮
│                                                                                                  │
│  time(params = {})                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (time function) -> Monarch Assistant ─────────────────────────────────────────╮
│                                                                                                  │
│  "08/02/23 10:28"                                                                                │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The current time is 10:28 AM on August 2, 2023.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Fun! Can you hide the function calls, and then tell me the entropy of a standard scrabble set?

╭─ Monarch Assistant -> Monarch Assistant (hide_function_calls function) ──────────────────────────╮
│                                                                                                  │
│  hide_function_calls(params = {})                                                                │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The entropy of a standard Scrabble set is approximately 4.37.                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Nice :) What time is it now?

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The current time is 10:29 AM on August 2, 2023.                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Ok, show the function calls again, and tell me more about the CFTR gene.
╭─ Monarch Assistant (show_function_calls function) -> Monarch Assistant ──────────────────────────╮
│                                                                                                  │
│  null                                                                                            │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-search_entity function) ────────────────────────╮
│                                                                                                  │
│  monarch-search_entity(params = {'term': 'CFTR', 'category': 'biolink:Gene', 'limit': 1})        │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-search_entity function) -> Monarch Assistant ────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "results": [                                                                                │
│          {                                                                                       │
│              "id": "HGNC:1884",                                                                  │
│              "name": "CFTR",                                                                     │
│              "categories": [                                                                     │
│                  "biolink:Gene"                                                                  │
│              ],                                                                                  │
│              "description": null                                                                 │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 41                                                                                 │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> Monarch Assistant (monarch-get_gene_disease_associations function) ────────╮
│                                                                                                  │
│  monarch-get_gene_disease_associations(params = {'gene_id': 'HGNC:1884', 'limit': 10})           │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Monarch Assistant (monarch-get_gene_disease_associations function) -> Monarch Assistant ────────╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "causal"                                                        │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0009061",                                                  │
│                  "label": "cystic fibrosis"                                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "causal"                                                        │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0010178",                                                  │
│                  "label": "congenital bilateral aplasia of vas deferens from CFTR mutation"      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008185",                                                  │
│                  "label": "hereditary chronic pancreatitis"                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008185",                                                  │
│                  "label": "hereditary chronic pancreatitis"                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0008887",                                                  │
│                  "label": "bronchiectasis with or without elevated sweat chloride 1"             │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0009061",                                                  │
│                  "label": "cystic fibrosis"                                                      │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018393",                                                  │
│                  "label": "male infertility with azoospermia or oligozoospermia due to single    │
│  gene mutation"                                                                                  │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018801",                                                  │
│                  "label": "congenital bilateral absence of vas deferens"                         │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0018956",                                                  │
│                  "label": "idiopathic bronchiectasis"                                            │
│              },                                                                                  │
│              "type": null                                                                        │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "relationship": "correlated"                                                    │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "disease": {                                                                        │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "disease_id": "MONDO:0044663",                                                  │
│                  "label": "aquagenic palmoplantar keratoderma"                                   │
│              },                                                                                  │
│              "type": null                                                                        │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 10,                                                                                │
│      "disease_url_template": "https://monarchinitiative.org/disease/{disease_id}"                │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Monarch Assistant -> User ──────────────────────────────────────────────────────────────────────╮
│ The CFTR gene, also known as the Cystic Fibrosis Transmembrane Conductance Regulator gene, is    │
│ associated with several diseases. Here are some of the diseases associated with the CFTR gene:   │
│                                                                                                  │
│  1 Cystic Fibrosis: The CFTR gene is causally associated with Cystic Fibrosis, a genetic         │
│    disorder characterized by the production of sweat with a high salt content and mucus          │
│    secretions with an abnormal viscosity. More information                                       │
│  2 Congenital Bilateral Aplasia of Vas Deferens from CFTR Mutation: Mutations in the CFTR gene   │
│    can lead to the congenital absence of the vas deferens, which can cause infertility in males. │
│    More information                                                                              │
│  3 Hereditary Chronic Pancreatitis: The CFTR gene is correlated with hereditary chronic          │
│    pancreatitis, a condition characterized by inflammation of the pancreas that persists over    │
│    time. More information                                                                        │
│  4 Bronchiectasis with or without Elevated Sweat Chloride 1: Mutations in the CFTR gene can also │
│    be correlated with bronchiectasis, a condition characterized by the abnormal widening of the  │
│    bronchial tubes. More information                                                             │
│                                                                                                  │
│ Please note that this is not an exhaustive list of diseases associated with the CFTR gene. The   │
│ CFTR gene plays a crucial role in various physiological processes, and mutations in this gene    │
│ can have diverse effects on different organ systems.                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```