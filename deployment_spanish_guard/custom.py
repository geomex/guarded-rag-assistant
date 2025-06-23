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
    """Load the blocked patterns and prompt feature name from runtime parameters."""
    blocked_patterns = json.loads(RuntimeParameters.get("blocked_patterns"))
    prompt_feature_name = RuntimeParameters.get("prompt_feature_name")
    
    # Compile regex patterns for efficient matching
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in blocked_patterns]
    
    return compiled_patterns, prompt_feature_name


def score(data, model, **kwargs):
    """Score the data to detect blocked questions."""
    compiled_patterns, prompt_feature_name = model

    output = []
    positive_label = kwargs["positive_class_label"]
    negative_label = kwargs["negative_class_label"]
    
    for prompt in data[prompt_feature_name]:
        # Check if any blocked pattern matches
        is_blocked = any(pattern.search(prompt) for pattern in compiled_patterns)
        
        output.append(
            {positive_label: float(is_blocked), negative_label: 1 - float(is_blocked)}
        )
    
    return pd.DataFrame(output) 