#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Real Search Orchestrator
Orquestrador de busca real com rotação de APIs e extração massiva
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Assuming these modules are available in the same directory or a sibling directory
# If they are in a parent directory, the import path might need adjustment (e.g., from ..services.enhanced_api_rotation_manager)
try:
    from .enhanced_api_rotation_manager import get_api_manager
except ImportError:
    # Fallback for testing or if run directly without package structure
    from enhanced_api_rotation_manager import get_api_manager

try:
    from .alibaba_websailor import get_websailor
except ImportError:
    # Fallback for testing or if run directly without package structure
    from alibaba_websailor import get_websailor


logger = logging.getLogger(__name__)

class RealSearchOrchestrator:
    """Orquestrador principal de busca real"""

    def __init__(self):
        self.api_manager = get_api_manager()
        self.websailor = get_websailor()

    async def execute_comprehensive_search(self, query: str, product_name: str) -> Dict[str, Any]:
        """Executa busca abrangente com múltiplas APIs"""
        try:
            logger.info(f"🚀 Iniciando busca abrangente para: {query}")

            # Inicia busca massiva do Alibaba WebSailor
            # Assuming websailor.execute_massive_search returns a dictionary
            websailor_result = await self.websailor.execute_massive_search(query, product_name)

            # Busca com múltiplas APIs usando rotação
            api_results = await self._search_with_multiple_apis(query)

            # Consolida resultados
            consolidated_result = {
                'query': query,
                'product_name': product_name,
                'timestamp': datetime.now().isoformat(),
                'websailor_search': websailor_result if websailor_result else {},
                'api_search_results': api_results if api_results else {},
                'success': True
            }

            logger.info(f"✅ Busca abrangente concluída para: {product_name}")
            return consolidated_result

        except Exception as e:
            logger.error(f"❌ Erro na busca abrangente: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _search_with_multiple_apis(self, query: str) -> Dict[str, Any]:
        """Busca usando múltiplas APIs com rotação"""
        results = {}

        # Busca com Exa
        exa_result = await self._search_with_exa(query)
        if exa_result and exa_result.get('results'): # Check if results are present
            results['exa'] = exa_result

        # Busca com Tavily
        tavily_result = await self._search_with_tavily(query)
        if tavily_result and tavily_result.get('results'): # Check if results are present
            results['tavily'] = tavily_result

        # Busca com SerpAPI
        serpapi_result = await self._search_with_serpapi(query)
        if serpapi_result and serpapi_result.get('results'): # Check if results are present
            results['serpapi'] = serpapi_result

        return results

    async def _search_with_exa(self, query: str) -> Optional[Dict[str, Any]]:
        """Busca usando Exa API com rotação"""
        try:
            exa_key = self.api_manager.get_next_api('exa')
            if not exa_key:
                logger.warning("Nenhuma chave Exa disponível")
                return None

            # Import exa_py dynamically to avoid issues if not installed
            try:
                from exa_py import Exa
            except ImportError:
                logger.error("Exa library not installed. Please install it: pip install exa-py")
                return None

            exa = Exa(api_key=exa_key)

            search_result = exa.search_and_contents(
                query=query,
                num_results=10,
                text=True,
                highlights=True
            )

            processed_results = []
            if search_result and hasattr(search_result, 'results'):
                for result in search_result.results:
                    processed_results.append({
                        'title': result.title,
                        'url': result.url,
                        'text': result.text[:1000] if result.text else '',
                        'highlights': result.highlights[:3] if result.highlights else [],
                        'published_date': str(result.published_date) if result.published_date else None
                    })

            logger.info(f"✅ Exa: {len(processed_results)} resultados")
            return {
                'results': processed_results,
                'total_results': len(processed_results),
                'api_used': exa_key[:10] + "..." if exa_key else "N/A"
            }

        except Exception as e:
            logger.error(f"❌ Erro no Exa: {e}", exc_info=True)
            if exa_key:
                error_type = "rate_limit" if "rate" in str(e).lower() else "generic"
                self.api_manager.report_error('exa', exa_key, error_type)
            return None

    async def _search_with_tavily(self, query: str) -> Optional[Dict[str, Any]]:
        """Busca usando Tavily API com rotação"""
        try:
            tavily_key = self.api_manager.get_next_api('tavily')
            if not tavily_key:
                logger.warning("Nenhuma chave Tavily disponível")
                return None

            import requests # Keep import here if only used in this function

            payload = {
                "api_key": tavily_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_domains": [], # Example: ["wikipedia.org"]
                "exclude_domains": [], # Example: ["example.com"]
                "max_results": 10
            }

            # Using asyncio compatible requests if available, or standard requests with careful handling
            # For simplicity, sticking with standard requests here, assuming it's run in an async context where blocking is managed.
            response = requests.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()

            data = response.json()

            processed_results = []
            for result in data.get('results', []):
                processed_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', '')[:1000],
                    'score': result.get('score', 0)
                })

            logger.info(f"✅ Tavily: {len(processed_results)} resultados")
            return {
                'results': processed_results,
                'answer': data.get('answer', ''),
                'total_results': len(processed_results),
                'api_used': tavily_key[:10] + "..." if tavily_key else "N/A"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro no Tavily (request error): {e}", exc_info=True)
            if tavily_key:
                error_type = "rate_limit" if "rate" in str(e).lower() else "generic"
                self.api_manager.report_error('tavily', tavily_key, error_type)
            return None
        except Exception as e:
            logger.error(f"❌ Erro no Tavily: {e}", exc_info=True)
            if tavily_key:
                error_type = "rate_limit" if "rate" in str(e).lower() else "generic"
                self.api_manager.report_error('tavily', tavily_key, error_type)
            return None

    async def _search_with_serpapi(self, query: str) -> Optional[Dict[str, Any]]:
        """Busca usando SerpAPI com rotação"""
        try:
            serpapi_key = self.api_manager.get_next_api('serpapi')
            if not serpapi_key:
                logger.warning("Nenhuma chave SerpAPI disponível")
                return None

            import requests # Keep import here if only used in this function

            params = {
                'q': query,
                'api_key': serpapi_key,
                'engine': 'google', # Defaulting to Google, could be parameterized
                'num': 10
            }

            response = requests.get('https://serpapi.com/search', params=params)
            response.raise_for_status()

            data = response.json()

            processed_results = []
            for result in data.get('organic_results', []):
                processed_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'position': result.get('position', 0)
                })

            logger.info(f"✅ SerpAPI: {len(processed_results)} resultados")
            return {
                'results': processed_results,
                'total_results': len(processed_results),
                'api_used': serpapi_key[:10] + "..." if serpapi_key else "N/A"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro no SerpAPI (request error): {e}", exc_info=True)
            if serpapi_key:
                error_type = "rate_limit" if "rate" in str(e).lower() else "generic"
                self.api_manager.report_error('serpapi', serpapi_key, error_type)
            return None
        except Exception as e:
            logger.error(f"❌ Erro no SerpAPI: {e}", exc_info=True)
            if serpapi_key:
                error_type = "rate_limit" if "rate" in str(e).lower() else "generic"
                self.api_manager.report_error('serpapi', serpapi_key, error_type)
            return None

    def get_search_status(self) -> Dict[str, Any]:
        """Obtém status dos serviços de busca"""
        # Ensure api_manager is initialized and has the get_service_status method
        api_status = {}
        if self.api_manager:
            api_status = {
                'exa': self.api_manager.get_service_status('exa') if hasattr(self.api_manager, 'get_service_status') else 'unavailable',
                'tavily': self.api_manager.get_service_status('tavily') if hasattr(self.api_manager, 'get_service_status') else 'unavailable',
                'serpapi': self.api_manager.get_service_status('serpapi') if hasattr(self.api_manager, 'get_service_status') else 'unavailable'
            }
        else:
            api_status = {
                'exa': 'unavailable',
                'tavily': 'unavailable',
                'serpapi': 'unavailable'
            }

        # Assuming websailor is always operational if the class is instantiated
        websailor_status = 'operational' if self.websailor else 'unavailable'

        return {
            'api_status': api_status,
            'websailor_status': websailor_status,
            'timestamp': datetime.now().isoformat()
        }

# Instância global
real_search_orchestrator = RealSearchOrchestrator()

def get_search_orchestrator() -> RealSearchOrchestrator:
    """Retorna instância do orquestrador"""
    return real_search_orchestrator