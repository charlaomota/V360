#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced API Rotation Manager
Sistema robusto de rotação de APIs para busca massiva
"""

import os
import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class EnhancedAPIRotationManager:
    """Gerenciador de rotação de APIs com fallback automático"""

    def __init__(self):
        self.api_configs = self._load_api_configs()
        self.current_indices = {}
        self.error_counts = {}
        self.last_used = {}
        self.cooldown_periods = {}

        # Inicializa contadores
        for service in self.api_configs:
            self.current_indices[service] = 0
            self.error_counts[service] = {}
            self.last_used[service] = {}
            self.cooldown_periods[service] = {}

            for api_key in self.api_configs[service]:
                self.error_counts[service][api_key] = 0
                self.last_used[service][api_key] = datetime.now() - timedelta(hours=1)
                self.cooldown_periods[service][api_key] = 0

    def _load_api_configs(self) -> Dict[str, List[str]]:
        """Carrega configurações de APIs do ambiente"""
        configs = {}

        # OpenAI APIs
        openai_keys = []
        for i in range(1, 11):  # Até 10 chaves
            key = os.getenv(f'OPENAI_API_KEY_{i}') or os.getenv(f'OPENAI_API_KEY{i}')
            if key:
                openai_keys.append(key)
        if os.getenv('OPENAI_API_KEY'):
            openai_keys.append(os.getenv('OPENAI_API_KEY'))
        if openai_keys:
            configs['openai'] = openai_keys

        # Gemini APIs
        gemini_keys = []
        for i in range(1, 11):
            key = os.getenv(f'GEMINI_API_KEY_{i}') or os.getenv(f'GEMINI_API_KEY{i}')
            if key:
                gemini_keys.append(key)
        if os.getenv('GEMINI_API_KEY'):
            gemini_keys.append(os.getenv('GEMINI_API_KEY'))
        if gemini_keys:
            configs['gemini'] = gemini_keys

        # Groq APIs
        groq_keys = []
        for i in range(1, 11):
            key = os.getenv(f'GROQ_API_KEY_{i}') or os.getenv(f'GROQ_API_KEY{i}')
            if key:
                groq_keys.append(key)
        if os.getenv('GROQ_API_KEY'):
            groq_keys.append(os.getenv('GROQ_API_KEY'))
        if groq_keys:
            configs['groq'] = groq_keys

        # Exa APIs
        exa_keys = []
        for i in range(1, 11):
            key = os.getenv(f'EXA_API_KEY_{i}') or os.getenv(f'EXA_API_KEY{i}')
            if key:
                exa_keys.append(key)
        if os.getenv('EXA_API_KEY'):
            exa_keys.append(os.getenv('EXA_API_KEY'))
        if exa_keys:
            configs['exa'] = exa_keys

        # Tavily APIs
        tavily_keys = []
        for i in range(1, 11):
            key = os.getenv(f'TAVILY_API_KEY_{i}') or os.getenv(f'TAVILY_API_KEY{i}')
            if key:
                tavily_keys.append(key)
        if os.getenv('TAVILY_API_KEY'):
            tavily_keys.append(os.getenv('TAVILY_API_KEY'))
        if tavily_keys:
            configs['tavily'] = tavily_keys

        # SerpAPI APIs
        serpapi_keys = []
        for i in range(1, 11):
            key = os.getenv(f'SERPAPI_KEY_{i}') or os.getenv(f'SERPAPI_KEY{i}')
            if key:
                serpapi_keys.append(key)
        if os.getenv('SERPAPI_KEY'):
            serpapi_keys.append(os.getenv('SERPAPI_KEY'))
        if serpapi_keys:
            configs['serpapi'] = serpapi_keys

        # Supabase URLs e Keys
        supabase_urls = []
        supabase_keys = []
        for i in range(1, 11):
            url = os.getenv(f'SUPABASE_URL_{i}') or os.getenv(f'SUPABASE_URL{i}')
            key = os.getenv(f'SUPABASE_KEY_{i}') or os.getenv(f'SUPABASE_KEY{i}')
            if url and key:
                supabase_urls.append(url)
                supabase_keys.append(key)

        if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'):
            supabase_urls.append(os.getenv('SUPABASE_URL'))
            supabase_keys.append(os.getenv('SUPABASE_KEY'))

        if supabase_urls and supabase_keys:
            configs['supabase_urls'] = supabase_urls
            configs['supabase_keys'] = supabase_keys

        logger.info(f"✅ APIs carregadas: {list(configs.keys())}")
        for service, keys in configs.items():
            logger.info(f"  {service}: {len(keys)} chaves disponíveis")

        return configs

    def get_next_api(self, service: str) -> Optional[str]:
        """Obtém próxima API disponível com rotação inteligente"""
        if service not in self.api_configs:
            logger.warning(f"Serviço {service} não configurado")
            return None

        available_apis = self.api_configs[service]
        if not available_apis:
            return None

        # Tenta encontrar API sem cooldown
        for _ in range(len(available_apis)):
            current_api = available_apis[self.current_indices[service]]

            # Verifica se está em cooldown
            if self._is_api_available(service, current_api):
                self._update_usage(service, current_api)
                return current_api

            # Próxima API
            self.current_indices[service] = (self.current_indices[service] + 1) % len(available_apis)

        # Se todas estão em cooldown, usa a com menor tempo
        best_api = min(available_apis,
                      key=lambda api: self.last_used[service].get(api, datetime.min))

        self._update_usage(service, best_api)
        return best_api

    def _is_api_available(self, service: str, api_key: str) -> bool:
        """Verifica se API está disponível"""
        now = datetime.now()

        # Verifica cooldown
        cooldown = self.cooldown_periods[service].get(api_key, 0)
        last_use = self.last_used[service].get(api_key, datetime.min)

        if (now - last_use).total_seconds() < cooldown:
            return False

        # Verifica contagem de erros
        error_count = self.error_counts[service].get(api_key, 0)
        if error_count > 5:  # Máximo 5 erros consecutivos
            return False

        return True

    def _update_usage(self, service: str, api_key: str):
        """Atualiza registro de uso da API"""
        self.last_used[service][api_key] = datetime.now()

        # Reset erro count em uso bem-sucedido
        if api_key in self.error_counts[service]:
            self.error_counts[service][api_key] = 0

    def report_error(self, service: str, api_key: str, error_type: str = "generic"):
        """Reporta erro de API"""
        if service in self.error_counts and api_key in self.error_counts[service]:
            self.error_counts[service][api_key] += 1

            # Aumenta cooldown baseado no tipo de erro
            if error_type == "rate_limit":
                self.cooldown_periods[service][api_key] = 300  # 5 minutos
            elif error_type == "quota_exceeded":
                self.cooldown_periods[service][api_key] = 3600  # 1 hora
            else:
                self.cooldown_periods[service][api_key] = 60  # 1 minuto

            logger.warning(f"❌ Erro em {service}: {api_key[:10]}... - Tipo: {error_type}")

    def get_service_status(self, service: str) -> Dict[str, Any]:
        """Obtém status detalhado do serviço"""
        if service not in self.api_configs:
            return {"status": "not_configured", "available_apis": 0}

        total_apis = len(self.api_configs[service])
        available_apis = sum(1 for api in self.api_configs[service]
                           if self._is_api_available(service, api))

        return {
            "status": "healthy" if available_apis > 0 else "degraded",
            "total_apis": total_apis,
            "available_apis": available_apis,
            "current_index": self.current_indices.get(service, 0)
        }

    def reset_errors(self, service: str = None):
        """Reset contadores de erro"""
        if service:
            if service in self.error_counts:
                for api_key in self.error_counts[service]:
                    self.error_counts[service][api_key] = 0
                    self.cooldown_periods[service][api_key] = 0
                logger.info(f"✅ Erros resetados para {service}")
        else:
            for svc in self.error_counts:
                for api_key in self.error_counts[svc]:
                    self.error_counts[svc][api_key] = 0
                    self.cooldown_periods[svc][api_key] = 0
            logger.info("✅ Todos os erros resetados")

# Instância global
enhanced_api_rotation_manager = EnhancedAPIRotationManager()

def get_api_rotation_manager() -> EnhancedAPIRotationManager:
    """Retorna instância do gerenciador de rotação de APIs"""
    return enhanced_api_rotation_manager

def get_api_manager() -> EnhancedAPIRotationManager:
    """Retorna instância do gerenciador"""
    return enhanced_api_rotation_manager