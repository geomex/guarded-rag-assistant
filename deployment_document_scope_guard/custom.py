# Copyright 2024 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re

import pandas as pd
from datarobot_drum import RuntimeParameters


def load_model(code_dir):
    """Load the authorized documents and prompt feature name from runtime parameters."""
    authorized_documents = json.loads(RuntimeParameters.get("authorized_documents"))
    prompt_feature_name = RuntimeParameters.get("prompt_feature_name")
    
    # Create patterns to match document names
    document_patterns = []
    for doc in authorized_documents:
        # Create flexible patterns for document names
        doc_lower = doc.lower()
        # Handle accented characters and variations
        doc_pattern = re.sub(r'[áéíóúñ]', r'[áéíóúñ]', doc_lower)
        document_patterns.append(re.compile(doc_pattern, re.IGNORECASE))
    
    return document_patterns, prompt_feature_name


def score(data, model, **kwargs):
    """Score the data to detect out-of-scope queries."""
    document_patterns, prompt_feature_name = model

    output = []
    positive_label = kwargs["positive_class_label"]
    negative_label = kwargs["negative_class_label"]
    
    for prompt in data[prompt_feature_name]:
        prompt_lower = prompt.lower()
        
        # Check if query mentions any authorized document
        mentions_authorized_doc = any(pattern.search(prompt_lower) for pattern in document_patterns)
        
        # If no authorized documents are mentioned, it might be out of scope
        # This is a simplified check - in practice, you'd do more sophisticated analysis
        is_out_of_scope = not mentions_authorized_doc
        
        output.append(
            {positive_label: float(is_out_of_scope), negative_label: 1 - float(is_out_of_scope)}
        )
    
    return pd.DataFrame(output) 