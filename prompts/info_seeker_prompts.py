from langchain_core.prompts import ChatPromptTemplate

NORMALIZER_PROMPT = ChatPromptTemplate.from_template(
    """Given the following list of documents, please process them as instructed.

**Documents:**
{documents}

**Instructions:**
1.  **Extract Key Facts**: Identify and list the most important, standalone facts from the documents. Each fact should be a concise statement.
2.  **Extract Entities**: Identify and list the key people, organizations, and locations mentioned across all documents.
3.  **Create Timeline**: If the documents describe a sequence of events, create a timeline with dates and brief descriptions.
4.  **Format Output**: Return the information in a clean JSON object. Do not include any other text or commentary.

**JSON Output Format:**
{{
    "key_facts": ["<fact 1>", "<fact 2>", ...],
    "entities": ["<entity 1>", "<entity 2>", ...],
    "timeline": ["<YYYY-MM-DD: event description>", ...]
}}
"""
)

FACT_CHECKER_PROMPT = ChatPromptTemplate.from_template(
    """You are a meticulous fact-checker. Your task is to verify a list of claims against a set of provided source documents.

**Source Documents:**
{documents}

**Claims to Verify:**
{claims}

**Instructions:**
1.  For each claim, carefully check if it is supported by the information in the source documents.
2.  You MUST NOT use any external knowledge. Base your judgment solely on the provided text.
3.  Assign a verdict for each claim: 'Supported', 'Contradicted', or 'Unclear'.
4.  List the URLs of the source documents that support your verdict.
5.  Assign a confidence level: 'High' (supported by >=2 sources), 'Medium' (supported by 1 source), or 'Low' (unclear or contradicted).
6.  If you cannot verify a claim, list it as 'unresolved'.
7.  Format the output as a JSON object containing a list of verified facts.

**JSON Output Format:**
{{
    "facts_verified": [
        {{
            "claim": "<claim text>",
            "verdict": "<Supported/Contradicted/Unclear>",
            "sources": ["<url1>", "<url2>", ...],
            "confidence": "<High/Medium/Low>"
        }}
    ],
    "unresolved": ["<unresolved claim 1>", ...]
}}
"""
)

SUMMARIZER_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert summarizer. Your task is to create a concise, neutral summary from a list of verified facts.

**User Query:**
{query}

**Verified Facts:**
{verified_facts}

**Unresolved Claims:**
{unresolved_claims}

**Instructions:**
1.  Synthesize the 'Supported' facts into a brief, easy-to-read summary of no more than 5 bullet points.
2.  Focus on the most decision-relevant points related to the user's query.
3.  Extract any key statistics or notable quotes from the facts.
4.  List any open questions that arise from the 'Unresolved Claims' or gaps in the information.
5.  Do NOT introduce any new information. Your summary must be based solely on the provided facts.
6.  If confidence in the facts is low, this should be reflected in the tone of the summary (e.g., 'Some sources suggest...').
7.  Format the output as a clean JSON object.

**JSON Output Format:**
{{
    "tldr_bullets": ["<bullet 1>", "<bullet 2>", ...],
    "key_stats": ["<stat 1>", "<stat 2>", ...],
    "notable_quotes": ["<quote 1>", ...],
    "open_questions": ["<question 1>", ...]
}}
"""
)

EXPLAINER_PROMPT = ChatPromptTemplate.from_template(
    """You are a friendly and skilled explainer. Your goal is to make complex topics easy to understand for a curious beginner.

**Summary of Findings:**
{summary_tldr}

**Instructions:**
1.  Identify the top 2-3 key concepts, terms, or entities from the summary that a beginner might not understand.
2.  For each concept, provide a simple, one-paragraph explanation.
3.  Explain these concepts in the simplest, most neutral, and factual terms possible, avoiding jargon.
4.  Do NOT introduce new facts. Base your explanations on the context provided in the summary.
5.  Format the output as a clean JSON object.

**JSON Output Format:**
{{
    "explanations": [
        {{
            "concept": "<concept name>",
            "explanation": "<simple, one-paragraph explanation>"
        }}
    ]
}}
"""
)

COMPARER_PROMPT = ChatPromptTemplate.from_template(
    """You are a systematic researcher. Your task is to create a comparison table based on a user's query and a set of verified facts.

**User Query:**
{query}

**Verified Facts:**
{verified_facts}

**Instructions:**
1.  Analyze the user's query to identify the items to be compared (e.g., 'LangGraph vs. AutoGen').
2.  From the verified facts, determine relevant comparison criteria (e.g., 'Ease of Use', 'Flexibility', 'Community Support').
3.  Create a comparison table with one row for each criterion and one column for each item being compared.
4.  Populate the table cells with information synthesized *only* from the verified facts.
5.  If a fact is not available for a specific cell, mark it as 'N/A'.
6.  Format the output as a clean JSON object.

**JSON Output Format:**
{{
    "title": "<Title of Comparison, e.g., LangGraph vs. AutoGen>",
    "items_to_compare": ["<Item 1>", "<Item 2>", ...],
    "comparison_table": [
        {{
            "criterion": "<Criterion 1>",
            "values": ["<Value for Item 1>", "<Value for Item 2>", ...]
        }},
        {{
            "criterion": "<Criterion 2>",
            "values": ["<Value for Item 1>", "<Value for Item 2>", ...]
        }}
    ]
}}
"""
)

SUPERVISOR_PROMPT = ChatPromptTemplate.from_template(
    """You are the supervisor of a multi-agent research team. Your job is to manage the workflow to answer a user's query.

**User Query:**
{query}

**Current State:**
{state}

**Available Agents:**
- web_search: Performs a web search using OpenAI's built-in tool to gather initial documents and sources.
- normalizer: Cleans, deduplicates, and extracts key facts from documents.
- fact_checker: Verifies the extracted facts against the sources.
- summarizer: Creates a TL;DR summary from the verified facts.
- explainer: Simplifies key concepts for a beginner.
- comparer: Creates a comparison table if the query requires it.
- output_decider: Assembles the final research package.

**Workflow Rules:**
1.  The workflow always starts with `web_search`.
2.  After `web_search` (state has `retrieval_result`), run `normalizer`.
3.  After `normalizer` (state has `normalized_data`), run `fact_checker`.
4.  After `fact_checker` (state has `fact_check_result`), run `summarizer`.
5.  After `summarizer` (state has `summary_result`), run `explainer`.
6.  The `comparer` agent is OPTIONAL. Only run it after `explainer` if the user's query explicitly asks for a comparison (e.g., 'compare X and Y', 'X vs Y').
7.  After all other processing is done, run `output_decider` to assemble the final package.
8.  Once `output_decider` is complete, the task is finished. Respond with `FINISH`.

Your response MUST be a JSON object that adheres to the format instructions below. Do not include any other text, explanations, or markdown formatting.

{format_instructions}

Return the JSON object for the next agent to run.
"""
)
