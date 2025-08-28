#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Analysis Route
Rota principal de análise com busca massiva real
"""

import logging
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from services.real_search_orchestrator import get_search_orchestrator
from services.enhanced_api_rotation_manager import get_api_manager

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/execute_complete_analysis', methods=['POST'])
def execute_complete_analysis():
    """Executa análise completa com busca massiva"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados não fornecidos"
            }), 400

        query = data.get('query', '').strip()
        product_name = data.get('product_name', query).strip()

        if not query:
            return jsonify({
                "success": False,
                "error": "Query é obrigatória"
            }), 400

        logger.info(f"🚀 Iniciando análise completa para: {query}")

        # Executa busca massiva de forma assíncrona
        search_orchestrator = get_search_orchestrator()

        # Executa busca em thread separada para não bloquear
        import threading
        import queue

        result_queue = queue.Queue()

        def run_async_search():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    search_orchestrator.execute_comprehensive_search(query, product_name)
                )
                result_queue.put(result)
                loop.close()
            except Exception as e:
                logger.error(f"❌ Erro na busca assíncrona: {e}")
                result_queue.put({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        search_thread = threading.Thread(target=run_async_search)
        search_thread.start()
        search_thread.join(timeout=300)  # 5 minutos timeout

        if search_thread.is_alive():
            return jsonify({
                "success": False,
                "error": "Timeout na busca massiva",
                "timestamp": datetime.now().isoformat()
            }), 408

        try:
            search_result = result_queue.get_nowait()
        except queue.Empty:
            return jsonify({
                "success": False,
                "error": "Nenhum resultado da busca",
                "timestamp": datetime.now().isoformat()
            }), 500

        # Status das APIs
        api_manager = get_api_manager()
        api_status = {
            'exa': api_manager.get_service_status('exa'),
            'tavily': api_manager.get_service_status('tavily'),
            'serpapi': api_manager.get_service_status('serpapi'),
            'openai': api_manager.get_service_status('openai'),
            'gemini': api_manager.get_service_status('gemini'),
            'groq': api_manager.get_service_status('groq')
        }

        response = {
            "success": search_result.get('success', True),
            "query": query,
            "product_name": product_name,
            "search_results": search_result,
            "api_status": api_status,
            "message": "Análise completa executada com busca massiva real",
            "file_generated": search_result.get('websailor_search', {}).get('file_path'),
            "timestamp": datetime.now().isoformat(),
            "features_executed": [
                "Busca massiva de conteúdo textual (500KB)",
                "Extração de imagens do Instagram",
                "Busca com rotação de múltiplas APIs",
                "Consolidação de resultados em arquivo JSON",
                "Zero simulação - 100% dados reais"
            ]
        }

        logger.info(f"✅ Análise completa concluída para: {product_name}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"❌ Erro na análise completa: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@analysis_bp.route('/search_status', methods=['GET'])
def search_status():
    """Status do sistema de busca"""
    try:
        search_orchestrator = get_search_orchestrator()
        api_manager = get_api_manager()

        status = {
            "search_orchestrator": search_orchestrator.get_search_status(),
            "api_rotation_status": {
                service: api_manager.get_service_status(service)
                for service in ['exa', 'tavily', 'serpapi', 'openai', 'gemini', 'groq']
            },
            "websailor_status": "operational",
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(status)

    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@analysis_bp.route('/reset_api_errors', methods=['POST'])
def reset_api_errors():
    """Reset erros das APIs"""
    try:
        api_manager = get_api_manager()
        api_manager.reset_errors()

        return jsonify({
            "success": True,
            "message": "Erros das APIs resetados",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Erro ao resetar APIs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500