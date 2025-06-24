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
import textwrap

import datarobot as dr
import pulumi_datarobot as datarobot
from datarobot_pulumi_utils.schema.custom_models import (
    CustomModelArgs,
    DeploymentArgs,
    RegisteredModelArgs,
)
from datarobot_pulumi_utils.schema.guardrails import (
    Condition,
    CustomModelGuardConfigurationArgs,
    GuardConditionComparator,
    GuardrailTemplateNames,
    Intervention,
    ModerationAction,
    Stage,
)

from docsassist.i18n import gettext

from .settings_main import (
    PROJECT_ROOT,
    default_prediction_server_id,
    project_name,
    runtime_environment_moderations,
)

# Spanish Guardrail Settings
spanish_guard_target_name = "blocked"
spanish_guard_positive_class_label = "true"
spanish_guard_negative_class_label = "false"

# Blocked question patterns for Spanish RAG agent
blocked_question_patterns = [
    # Approval/rejection questions
    r'\b(será|sera)\s+aprobado\b',
    r'\b(evitar|evitar)\s+que\s+me\s+rechacen\b',
    r'\b(aprobado|rechazado)\b.*\b(pregunta|duda)\b',
    
    # Legal interpretation requests
    r'\b(ley|legal)\b.*\b(exactamente|exacto)\b',
    r'\b(qué|que)\s+dice\s+la\s+ley\b',
    r'\b(interpretación|interpretacion)\s+legal\b',
    
    # Document download requests
    r'\b(descargar|download)\b.*\b(documento|política|politica)\b',
    r'\b(documento|política|politica)\s+completo\b',
    r'\b(todo|completo)\s+el\s+documento\b',
    
    # Policy correctness questions
    r'\b(política|politica)\s+(correcta|incorrecta)\b',
    r'\b(es\s+correcta|está\s+bien)\b.*\b(política|politica)\b',
    
    # Workaround requests
    r'\b(dividir|split)\s+el\s+préstamo\b',
    r'\b(pasar|evitar)\s+el\s+filtro\b',
    r'\b(como|como)\s+evitar\b',
]

spanish_guard_custom_model_args = CustomModelArgs(
    name=f"Spanish Query Guard Custom Model [{project_name}]",
    resource_name=f"Spanish Query Guard Custom Model [{project_name}]",
    description="Este modelo está diseñado para detectar preguntas bloqueadas en el asistente RAG en español",
    base_environment_id=runtime_environment_moderations.id,
    target_name=spanish_guard_target_name,
    target_type=dr.enums.TARGET_TYPE.BINARY,
    positive_class_label=spanish_guard_positive_class_label,
    negative_class_label=spanish_guard_negative_class_label,
    runtime_parameter_values=[
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="blocked_patterns",
            type="string",
            value=json.dumps(blocked_question_patterns),
        ),
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="prompt_feature_name",
            type="string",
            value="guardrailText",
        ),
    ],
    folder_path=str(PROJECT_ROOT / "deployment_spanish_guard"),
)

spanish_guard_registered_model_args = RegisteredModelArgs(
    resource_name=f"Spanish Query Guard Registered Model [{project_name}]",
)

spanish_guard_deployment_args = DeploymentArgs(
    resource_name=f"Spanish Query Guard Deployment [{project_name}]",
    label=f"Spanish Query Guard Deployment [{project_name}]",
    predictions_settings=(
        None
        if default_prediction_server_id
        else datarobot.DeploymentPredictionsSettingsArgs(min_computes=0, max_computes=1)
    ),
)

spanish_guard_configuration_args = CustomModelGuardConfigurationArgs(
    template_name=GuardrailTemplateNames.CUSTOM_DEPLOYMENT,
    name=f"Spanish Query Guard Configuration [{project_name}]",
    stages=[Stage.PROMPT],
    intervention=Intervention(
        action=ModerationAction.BLOCK,
        condition=Condition(
            comparand=1,
            comparator=GuardConditionComparator.EQUALS,
        ).model_dump_json(),
        message=textwrap.dedent(
            gettext(
                """\
                He detectado que su pregunta contiene contenido que no puedo procesar. 
                
                Por favor, reformule su pregunta para enfocarse en información de políticas 
                de los documentos autorizados: Malla de Electrodomésticos, Malla de Motos, 
                Malla de Efectivo (vigentes del mes actual), Guía de Excepciones y 
                Bitácora de Política BIC12.
                
                No puedo:
                - Proporcionar recomendaciones o predicciones sobre aprobaciones
                - Dar interpretaciones legales exactas
                - Permitir descargas de documentos completos
                - Evaluar la corrección de políticas
                - Proporcionar consejos para evadir filtros"""
            )
        ),
    ),
    input_column_name="guardrailText",
    output_column_name=f"{spanish_guard_target_name}_{spanish_guard_positive_class_label}_PREDICTION",
)

# Document scope validation guardrail
document_scope_guard_target_name = "out_of_scope"
document_scope_guard_positive_class_label = "true"
document_scope_guard_negative_class_label = "false"

document_scope_guard_custom_model_args = CustomModelArgs(
    name=f"Document Scope Guard Custom Model [{project_name}]",
    resource_name=f"Document Scope Guard Custom Model [{project_name}]",
    description="Este modelo valida que las consultas estén dentro del alcance de los documentos autorizados",
    base_environment_id=runtime_environment_moderations.id,
    target_name=document_scope_guard_target_name,
    target_type=dr.enums.TARGET_TYPE.BINARY,
    positive_class_label=document_scope_guard_positive_class_label,
    negative_class_label=document_scope_guard_negative_class_label,
    runtime_parameter_values=[
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="authorized_documents",
            type="string",
            value=json.dumps([
                "Malla de Electrodomésticos",
                "Malla de Motos", 
                "Malla de Efectivo",
                "Guía de Excepciones",
                "Bitácora de Política BIC12"
            ]),
        ),
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="prompt_feature_name",
            type="string",
            value="guardrailText",
        ),
    ],
    folder_path=str(PROJECT_ROOT / "deployment_document_scope_guard"),
)

document_scope_guard_registered_model_args = RegisteredModelArgs(
    resource_name=f"Document Scope Guard Registered Model [{project_name}]",
)

document_scope_guard_deployment_args = DeploymentArgs(
    resource_name=f"Document Scope Guard Deployment [{project_name}]",
    label=f"Document Scope Guard Deployment [{project_name}]",
    predictions_settings=(
        None
        if default_prediction_server_id
        else datarobot.DeploymentPredictionsSettingsArgs(min_computes=0, max_computes=1)
    ),
)

document_scope_guard_configuration_args = CustomModelGuardConfigurationArgs(
    template_name=GuardrailTemplateNames.CUSTOM_DEPLOYMENT,
    name=f"Document Scope Guard Configuration [{project_name}]",
    stages=[Stage.PROMPT],
    intervention=Intervention(
        action=ModerationAction.BLOCK,
        condition=Condition(
            comparand=1,
            comparator=GuardConditionComparator.EQUALS,
        ).model_dump_json(),
        message=textwrap.dedent(
            gettext(
                """\
                Su pregunta parece estar fuera del alcance de los documentos autorizados.
                
                Solo puedo responder consultas basadas en:
                - Malla de Electrodomésticos (mes actual)
                - Malla de Motos (mes actual)
                - Malla de Efectivo (mes actual)
                - Guía de Excepciones
                - Bitácora de Política BIC12
                
                Por favor, reformule su pregunta o contacte al departamento correspondiente 
                para obtener ayuda con temas fuera de este alcance."""
            )
        ),
    ),
    input_column_name="guardrailText",
    output_column_name=f"{document_scope_guard_target_name}_{document_scope_guard_positive_class_label}_PREDICTION",
)

# Spanish Prompt Injection Guard - Custom implementation for Spanish business terms
spanish_prompt_injection_guard_target_name = "prompt_injection"
spanish_prompt_injection_guard_positive_class_label = "true"
spanish_prompt_injection_guard_negative_class_label = "false"

# Legitimate Spanish business terms that should NOT be flagged as prompt injection
legitimate_business_terms = [
    "matriz de datos", "matriz", "datos", "información", "política", "politica",
    "trabajador", "empleado", "cliente", "segmento", "verificación", "verificacion",
    "período", "periodo", "requerido", "formal", "independiente", "vip", "vip1",
    "electrodomésticos", "electrodomesticos", "motos", "efectivo", "excepciones",
    "bitácora", "bitacora", "bic12", "malla", "guía", "guia", "política", "politica"
]

# Actual prompt injection patterns in Spanish
spanish_prompt_injection_patterns = [
    r'\b(ignora|olvida)\s+(anterior|todo|todo lo anterior)\b',
    r'\b(actúa|actua)\s+como\s+(si fueras|si fueras)\b',
    r'\b(eres|tu eres)\s+(un|una)\s+(programador|desarrollador|hacker)\b',
    r'\b(escribe|genera)\s+(código|codigo)\s+(para|que)\b',
    r'\b(bypass|evadir|saltar)\s+(seguridad|filtros|restricciones)\b',
    r'\b(sistema|prompt)\s+(anterior|previo)\s+(no|no existe)\b',
    r'\b(instrucciones|instrucciones)\s+(secretas|ocultas|especiales)\b',
    r'\b(rol|role)\s+(de|del)\s+(sistema|asistente)\b',
    r'\b(confidencial|secreto)\s+(información|informacion)\b',
    r'\b(acceso|acceder)\s+(a|al)\s+(sistema|base de datos)\b'
]

spanish_prompt_injection_guard_custom_model_args = CustomModelArgs(
    name=f"Spanish Prompt Injection Guard Custom Model [{project_name}]",
    resource_name=f"Spanish Prompt Injection Guard Custom Model [{project_name}]",
    description="Este modelo detecta inyecciones de prompt en español, excluyendo términos empresariales legítimos",
    base_environment_id=runtime_environment_moderations.id,
    target_name=spanish_prompt_injection_guard_target_name,
    target_type=dr.enums.TARGET_TYPE.BINARY,
    positive_class_label=spanish_prompt_injection_guard_positive_class_label,
    negative_class_label=spanish_prompt_injection_guard_negative_class_label,
    runtime_parameter_values=[
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="legitimate_terms",
            type="string",
            value=json.dumps(legitimate_business_terms),
        ),
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="injection_patterns",
            type="string",
            value=json.dumps(spanish_prompt_injection_patterns),
        ),
        datarobot.CustomModelRuntimeParameterValueArgs(
            key="prompt_feature_name",
            type="string",
            value="guardrailText",
        ),
    ],
    folder_path=str(PROJECT_ROOT / "deployment_spanish_prompt_injection_guard"),
)

spanish_prompt_injection_guard_registered_model_args = RegisteredModelArgs(
    resource_name=f"Spanish Prompt Injection Guard Registered Model [{project_name}]",
)

spanish_prompt_injection_guard_deployment_args = DeploymentArgs(
    resource_name=f"Spanish Prompt Injection Guard Deployment [{project_name}]",
    label=f"Spanish Prompt Injection Guard Deployment [{project_name}]",
    predictions_settings=(
        None
        if default_prediction_server_id
        else datarobot.DeploymentPredictionsSettingsArgs(min_computes=0, max_computes=1)
    ),
)

spanish_prompt_injection_guard_configuration_args = CustomModelGuardConfigurationArgs(
    template_name=GuardrailTemplateNames.CUSTOM_DEPLOYMENT,
    name=f"Spanish Prompt Injection Guard Configuration [{project_name}]",
    stages=[Stage.PROMPT],
    intervention=Intervention(
        action=ModerationAction.BLOCK,
        condition=Condition(
            comparand=1,
            comparator=GuardConditionComparator.EQUALS,
        ).model_dump_json(),
        message=textwrap.dedent(
            gettext(
                """\
                He detectado que su pregunta contiene una inyección de prompt. 
                
                Por favor, reformule su pregunta para enfocarse en información 
                de políticas de los documentos autorizados sin intentar 
                modificar mi comportamiento o acceder a información del sistema."""
            )
        ),
    ),
    input_column_name="guardrailText",
    output_column_name=f"{spanish_prompt_injection_guard_target_name}_{spanish_prompt_injection_guard_positive_class_label}_PREDICTION",
) 