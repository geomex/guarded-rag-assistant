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

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Set
from dataclasses import dataclass


class DocumentType(str, Enum):
    """Approved document types for the Spanish RAG agent."""
    MALLA_ELECTRODOMESTICOS = "Malla de Electrodomésticos"
    MALLA_MOTOS = "Malla de Motos"
    MALLA_EFECTIVO = "Malla de Efectivo"
    GUIA_EXCEPCIONES = "Guía de Excepciones"
    BITACORA_POLITICA_BIC12 = "Bitácora de Política BIC12"


@dataclass
class DocumentMetadata:
    """Metadata for document validation."""
    document_type: DocumentType
    document_date: Optional[datetime]
    is_current_month: bool
    source: str
    content: str


class DocumentValidator:
    """Validates documents based on type, date, and content requirements."""
    
    def __init__(self):
        self.approved_document_types: Set[DocumentType] = {
            DocumentType.MALLA_ELECTRODOMESTICOS,
            DocumentType.MALLA_MOTOS,
            DocumentType.MALLA_EFECTIVO,
            DocumentType.GUIA_EXCEPCIONES,
            DocumentType.BITACORA_POLITICA_BIC12,
        }
        
        # Monthly documents that must be current
        self.monthly_documents: Set[DocumentType] = {
            DocumentType.MALLA_ELECTRODOMESTICOS,
            DocumentType.MALLA_MOTOS,
            DocumentType.MALLA_EFECTIVO,
        }
        
        # Documents that don't require monthly validation
        self.static_documents: Set[DocumentType] = {
            DocumentType.GUIA_EXCEPCIONES,
            DocumentType.BITACORA_POLITICA_BIC12,
        }
    
    def extract_document_metadata(self, content: str, source: str) -> DocumentMetadata:
        """Extract metadata from document content and source."""
        document_type = self._identify_document_type(content, source)
        document_date = self._extract_document_date(content, source)
        is_current_month = self._is_current_month(document_date, document_type)
        
        return DocumentMetadata(
            document_type=document_type,
            document_date=document_date,
            is_current_month=is_current_month,
            source=source,
            content=content
        )
    
    def _identify_document_type(self, content: str, source: str) -> DocumentType:
        """Identify the document type based on content and source."""
        content_lower = content.lower()
        source_lower = source.lower()
        
        # Check for document type indicators in content and source
        if any(keyword in content_lower for keyword in ["electrodomésticos", "electrodomesticos"]):
            return DocumentType.MALLA_ELECTRODOMESTICOS
        elif any(keyword in content_lower for keyword in ["motos", "motocicletas"]):
            return DocumentType.MALLA_MOTOS
        elif any(keyword in content_lower for keyword in ["efectivo", "cash"]):
            return DocumentType.MALLA_EFECTIVO
        elif any(keyword in content_lower for keyword in ["excepciones", "exceptions"]):
            return DocumentType.GUIA_EXCEPCIONES
        elif any(keyword in content_lower for keyword in ["bitácora", "bitacora", "bic12"]):
            return DocumentType.BITACORA_POLITICA_BIC12
        else:
            # Default based on source filename
            if "electrodomesticos" in source_lower:
                return DocumentType.MALLA_ELECTRODOMESTICOS
            elif "motos" in source_lower:
                return DocumentType.MALLA_MOTOS
            elif "efectivo" in source_lower:
                return DocumentType.MALLA_EFECTIVO
            elif "excepciones" in source_lower:
                return DocumentType.GUIA_EXCEPCIONES
            elif "bic12" in source_lower or "bitacora" in source_lower:
                return DocumentType.BITACORA_POLITICA_BIC12
            else:
                # Default to a static document if we can't identify
                return DocumentType.GUIA_EXCEPCIONES
    
    def _extract_document_date(self, content: str, source: str) -> Optional[datetime]:
        """Extract document date from content or source."""
        # Look for date patterns in content
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre\s+(\d{4})',  # Month YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # For now, return current date as placeholder
                # In a real implementation, you'd parse the actual date
                return datetime.now()
        
        return None
    
    def _is_current_month(self, document_date: Optional[datetime], document_type: DocumentType) -> bool:
        """Check if document is from current month (for monthly documents)."""
        if document_type not in self.monthly_documents:
            return True  # Static documents are always considered current
        
        if document_date is None:
            return False  # If we can't determine date, assume it's not current
        
        current_date = datetime.now()
        return (document_date.year == current_date.year and 
                document_date.month == current_date.month)
    
    def is_document_approved(self, metadata: DocumentMetadata) -> bool:
        """Check if document meets approval criteria."""
        # Check if document type is approved
        if metadata.document_type not in self.approved_document_types:
            return False
        
        # Check if monthly document is current
        if metadata.document_type in self.monthly_documents and not metadata.is_current_month:
            return False
        
        return True
    
    def filter_documents(self, documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """Filter documents to only include approved ones."""
        return [doc for doc in documents if self.is_document_approved(doc)]
    
    def get_validation_message(self, metadata: DocumentMetadata) -> Optional[str]:
        """Get validation message for rejected documents."""
        if metadata.document_type not in self.approved_document_types:
            return f"Documento no autorizado: {metadata.document_type.value}"
        
        if (metadata.document_type in self.monthly_documents and 
            not metadata.is_current_month):
            return f"Documento desactualizado: {metadata.document_type.value} debe ser del mes actual"
        
        return None


class QueryValidator:
    """Validates user queries against guardrails."""
    
    def __init__(self):
        self.blocked_patterns = [
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
        
        self.blocked_patterns_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.blocked_patterns]
    
    def is_query_blocked(self, query: str) -> tuple[bool, Optional[str]]:
        """Check if query should be blocked and return reason."""
        query_lower = query.lower()
        
        for pattern in self.blocked_patterns_compiled:
            if pattern.search(query_lower):
                return True, self._get_block_reason(pattern.pattern)
        
        return False, None
    
    def _get_block_reason(self, pattern: str) -> str:
        """Get human-readable reason for blocked query."""
        if "aprobado" in pattern or "rechacen" in pattern:
            return "No puedo proporcionar recomendaciones o predicciones sobre resultados de aprobación."
        elif "ley" in pattern or "legal" in pattern:
            return "No puedo proporcionar interpretaciones legales ni texto legal exacto."
        elif "descargar" in pattern or "completo" in pattern:
            return "No puedo proporcionar documentos completos ni permitir descargas."
        elif "correcta" in pattern or "bien" in pattern:
            return "No puedo evaluar la corrección de políticas."
        elif "dividir" in pattern or "filtro" in pattern:
            return "No puedo proporcionar consejos sobre cómo evadir filtros o políticas."
        else:
            return "Su pregunta contiene contenido que no puedo procesar."
    
    def validate_query_scope(self, query: str, available_documents: List[DocumentMetadata]) -> tuple[bool, Optional[str]]:
        """Check if query is within scope of available documents."""
        # This is a simplified check - in practice, you'd do semantic analysis
        query_lower = query.lower()
        
        # Check if query mentions document types not available
        mentioned_types = set()
        for doc_type in DocumentType:
            if doc_type.value.lower() in query_lower:
                mentioned_types.add(doc_type)
        
        available_types = {doc.document_type for doc in available_documents}
        unavailable_types = mentioned_types - available_types
        
        if unavailable_types:
            return False, f"Su pregunta hace referencia a documentos no disponibles: {', '.join([t.value for t in unavailable_types])}"
        
        return True, None 