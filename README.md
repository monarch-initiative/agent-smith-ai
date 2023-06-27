# monarch-assistant

This repo attempts to replicate OpenAI's Plugin ecosystem using their [function-calling models](https://openai.com/blog/function-calling-and-other-api-updates). 

It utilizes the same API wrapper, https://github.com/monarch-initiative/oai-monarch-plugin, and so requires that to be running (on `localhost:3434` by default, or 
as specified via the `MONARCH_WRAPPER_BASE_URL` environment variable). It also requires an `OPENAI_API_KEY`; both of these can be added to a `.env` file in the base
of this repo such as:

```
OPENAI_API_KEY=<your_key>
MONARCH_WRAPPER_BASE_URL=http://localhost:3434
```

Current features:

* Able to plan and chain function/API calls! This isn't consistent for queries that require multiple steps though (at least using gpt-3.5-turbo, gpt-4 not yet tested)
* Allows inspecting function calls and results
* Defines a specific set of "safe" callable functions
* Formats markdown and provides entity links back to monarchinitiative.org 

Current limitations:

* Code is still rough, and major architectural changes are on the table. 
* Providing an API interface to this agent (for use in a web UI, for example) is a work in progress, currently the command-line interface is more robust.
* Not all features of https://github.com/monarch-initiative/oai-monarch-plugin are supported
* The default model is `gpt-3.5-turbo-16k-0613` which provides a 16k context window, but no context window management or conversation summarisation/compression is implemented, so eventually it will fail (especially when calling functions which use a lot of tokens)


### How to

First, get https://github.com/monarch-initiative/oai-monarch-plugin running, by default on `http://localhost:3434`.

Next, create a `.env` file in the root of this repo with entries for `OPENAI_API_KEY` (and `MONARCH_WRAPPER_BASE_URL` if not running the wrapper on http://localhost:3434).

Run `make chat`, which will install dependencies and run the command-line UI. 

Example chat (link formatting not shown, but available in terminal):

```
──────────────────────────────────────── Monarch Assistant ─────────────────────────────────────────

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Hello! I am the Monarch Assistant, an AI-powered chatbot that can answer questions about genes,  │
│ diseases, and phenotypes. I am a work in progress, and you shouldknow the following:             │
│                                                                                                  │
│  • I currently rely on https://github.com/monarch-initiative/oai-monarch-plugin, but am not at   │
│    feature parity.                                                                               │
│  • You can exit by saying 'exit', and you can request that I turn on or off function call        │
│    responses by saying 'show function calls' or 'hide function calls' at any time. They are      │
│    shown by default.                                                                             │
│  • I do not currently implement context-window management, so after a while your conversation    │
│    will produce an error.                                                                        │
│  • For a bit of fun, try asking me to describe my plan. For example, "What are the symptoms of   │
│    Cystic Fibrosis? Describe your plan before you execute it."                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: What time is it?

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ time(params = {})                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
│ 06/27/23 12:36                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ The current time is 06/27/23 12:36.                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Ok, just to check, can you hide the function calls and responses?

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ set_show_function_calls(params = {'show': False})                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Sure, I have hidden the function calls and responses. Let me know if there's anything else I can │
│ help with!                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Can you get me the time again?

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ The current time is 06/27/23 12:36.                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Neat. Let's show function responses again.
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
│ True                                                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Sure, I have enabled the display of function responses. Let me know if there's anything else I   │
│ can assist you with!                                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Thanks :) What are some symptoms associated with Cystic Fibrosis?

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ search_monarch(params = {'term': 'Cystic Fibrosis', 'category': 'biolink:Disease', 'limit': 1})  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
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
│      "total": 16                                                                                 │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ get_disease_phenotype_associations(params = {'disease_id': 'MONDO:0009061', 'limit': 5})         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040280",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0012236",                                                   │
│                  "label": "Elevated sweat chloride (HPO)"                                        │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040281",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0012236",                                                   │
│                  "label": "Elevated sweat chloride (HPO)"                                        │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040283",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0005376",                                                   │
│                  "label": "Recurrent Haemophilus influenzae infections (HPO)"                    │
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
│                  "frequency_qualifier": "HP:0040282",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0006532",                                                   │
│                  "label": "Recurrent pneumonia (HPO)"                                            │
│              }                                                                                   │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 62,                                                                                │
│      "phenotype_url_template": "https://monarchinitiative.org/phenotype/{phenotype_id}"          │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Cystic Fibrosis (CF) is a genetic disorder characterized by the production of sweat with a high  │
│ salt content and mucus secretions with an abnormal viscosity. Some symptoms associated with      │
│ Cystic Fibrosis include:                                                                         │
│                                                                                                  │
│  1 Elevated sweat chloride: This is a common symptom of Cystic Fibrosis, where the sweat has a   │
│    higher than normal concentration of chloride. More information                                │
│  2 Recurrent Haemophilus influenzae infections: Individuals with Cystic Fibrosis may experience  │
│    frequent infections caused by Haemophilus influenzae bacteria. More information               │
│  3 Chronic lung disease: Cystic Fibrosis can lead to chronic lung disease, characterized by      │
│    persistent respiratory symptoms and lung damage. More information                             │
│  4 Recurrent pneumonia: Individuals with Cystic Fibrosis may experience recurrent episodes of    │
│    pneumonia, which is an infection of the lungs. More information                               │
│                                                                                                  │
│ Please note that these are just a few examples of symptoms associated with Cystic Fibrosis.      │
│ There are many other symptoms and complications that can occur.                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: Thanks :) What are some symptoms associated with Acrogeria? This time describe your plan to answer the question before execu
ting it.

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ To find symptoms associated with Acrogeria, I will first search for Acrogeria in the Monarch     │
│ Initiative knowledge graph. Once I have the identifier for Acrogeria, I will retrieve the        │
│ phenotype associations for that disease. This will give me a list of symptoms associated with    │
│ Acrogeria. Finally, I will provide a description of the symptoms to the user.                    │
│                                                                                                  │
│ Let me execute this plan and provide you with the symptoms associated with Acrogeria.            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ search_monarch(params = {'term': 'Acrogeria', 'category': 'biolink:Disease', 'limit': 1})        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "results": [                                                                                │
│          {                                                                                       │
│              "id": "MONDO:0008716",                                                              │
│              "name": "acrogeria",                                                                │
│              "categories": [                                                                     │
│                  "biolink:Disease"                                                               │
│              ],                                                                                  │
│              "description": "A congenital skin condition characterized by premature aging, more  │
│  especially in the form of unusually fragile, thin skin on the hands and feet. Its onset is in   │
│  early childhood; it progresses over the next few years and then remains stable. A bruising      │
│  tendency has been observed."                                                                    │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 1                                                                                  │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ get_disease_phenotype_associations(params = {'disease_id': 'MONDO:0008716', 'limit': 5})         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Function Response ──────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  {                                                                                               │
│      "associations": [                                                                           │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040282",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0007392",                                                   │
│                  "label": "Excessive wrinkled skin (HPO)"                                        │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040281",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0007400",                                                   │
│                  "label": "Irregular hyperpigmentation (HPO)"                                    │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040281",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0007495",                                                   │
│                  "label": "Prematurely aged appearance (HPO)"                                    │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040281",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0008065",                                                   │
│                  "label": "Aplasia/Hypoplasia of the skin (HPO)"                                 │
│              }                                                                                   │
│          },                                                                                      │
│          {                                                                                       │
│              "metadata": {                                                                       │
│                  "frequency_qualifier": "HP:0040281",                                            │
│                  "onset_qualifier": null                                                         │
│              },                                                                                  │
│              "publications": [],                                                                 │
│              "phenotype": {                                                                      │
│                  "metadata": {},                                                                 │
│                  "publications": [],                                                             │
│                  "phenotype_id": "HP:0000951",                                                   │
│                  "label": "Abnormality of the skin (HPO)"                                        │
│              }                                                                                   │
│          }                                                                                       │
│      ],                                                                                          │
│      "total": 19,                                                                                │
│      "phenotype_url_template": "https://monarchinitiative.org/phenotype/{phenotype_id}"          │
│  }                                                                                               │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Acrogeria is a congenital skin condition characterized by premature aging, particularly in the   │
│ form of unusually fragile, thin skin on the hands and feet. Its onset is in early childhood,     │
│ progresses over the next few years, and then remains stable. A bruising tendency has also been   │
│ observed.                                                                                        │
│                                                                                                  │
│ Some symptoms associated with Acrogeria include:                                                 │
│                                                                                                  │
│  1 Excessive wrinkled skin: Individuals with Acrogeria may have excessive wrinkling of the skin. │
│    More information                                                                              │
│  2 Irregular hyperpigmentation: Irregular patches of darker skin, known as hyperpigmentation,    │
│    can occur in individuals with Acrogeria. More information                                     │
│  3 Prematurely aged appearance: Acrogeria can give individuals a prematurely aged appearance.    │
│    More information                                                                              │
│  4 Aplasia/Hypoplasia of the skin: Some individuals with Acrogeria may have underdeveloped or    │
│    absent skin in certain areas. More information                                                │
│  5 Abnormality of the skin: Acrogeria can cause various abnormalities of the skin. More          │
│    information                                                                                   │
│                                                                                                  │
│ Please note that these are just a few examples of symptoms associated with Acrogeria. There may  │
│ be other symptoms and variations in individuals with this condition.                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
User: exit

╭─ Function Call ──────────────────────────────────────────────────────────────────────────────────╮
│ set_show_function_calls(params = {'show': False})                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Assistant ──────────────────────────────────────────────────────────────────────────────────────╮
│ Okay, I will exit now. If you have any more questions in the future, feel free to ask. Have a    │
│ great day!                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```