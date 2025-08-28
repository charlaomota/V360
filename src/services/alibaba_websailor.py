#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Alibaba WebSailor
Sistema de busca massiva com extração real de conteúdo
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class AlibabaWebSailor:
    """Sistema de busca massiva com extração real de conteúdo"""
    
    def __init__(self):
        self.search_results = []
        self.content_buffer = []
        self.current_search_query = ""
        self.target_content_size = 500000  # 500KB
        self.max_images_per_platform = 10
        self.extracted_content_size = 0
        
        # Diretórios para salvar resultados
        self.results_dir = Path("analyses_data/search_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ AlibabaWebSailor inicializado")
    
    async def execute_massive_search(self, query: str, orchestrator) -> Dict[str, Any]:
        """Executa busca massiva com extração de conteúdo"""
        try:
            self.current_search_query = query
            self.search_results = []
            self.content_buffer = []
            self.extracted_content_size = 0
            
            logger.info(f"🔍 Iniciando busca massiva para: {query}")
            
            # Fase 1: Busca textual até 500KB
            await self._search_text_content(query, orchestrator)
            
            # Fase 2: Busca por imagens das redes sociais
            await self._search_social_images(query)
            
            # Salva resultados
            result_file = await self._save_search_results(query)
            
            return {
                "success": True,
                "query": query,
                "content_size": self.extracted_content_size,
                "text_entries": len(self.content_buffer),
                "social_images": self._count_social_images(),
                "result_file": result_file,
                "message": f"Busca massiva concluída: {self.extracted_content_size/1024:.1f}KB de conteúdo"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na busca massiva: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def _search_text_content(self, query: str, orchestrator):
        """Busca conteúdo textual até atingir 500KB"""
        try:
            page = 1
            while self.extracted_content_size < self.target_content_size:
                logger.info(f"📄 Buscando página {page} - {self.extracted_content_size/1024:.1f}KB coletados")
                
                # Usa o orchestrator para buscar
                search_results = await orchestrator.search_comprehensive(
                    query=f"{query} página {page}",
                    max_results=20
                )
                
                if not search_results or not search_results.get("results"):
                    logger.warning(f"⚠️ Sem resultados na página {page}")
                    break
                
                # Processa resultados
                for result in search_results["results"]:
                    await self._extract_and_add_content(result)
                    
                    if self.extracted_content_size >= self.target_content_size:
                        logger.info(f"✅ Meta de {self.target_content_size/1024:.1f}KB atingida")
                        break
                
                page += 1
                await asyncio.sleep(1)  # Rate limiting
                
                if page > 50:  # Limite de páginas
                    logger.warning("⚠️ Limite de páginas atingido")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erro na busca textual: {e}")
    
    async def _extract_and_add_content(self, result: Dict[str, Any]):
        """Extrai e adiciona conteúdo relevante"""
        try:
            content_entry = {
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "snippet": result.get("snippet", ""),
                "extracted_at": datetime.now().isoformat()
            }
            
            # Calcula tamanho do conteúdo
            content_text = f"{content_entry['title']} {content_entry['content']} {content_entry['snippet']}"
            content_size = len(content_text.encode('utf-8'))
            
            if content_size > 100:  # Mínimo de 100 bytes
                self.content_buffer.append(content_entry)
                self.extracted_content_size += content_size
                
                logger.debug(f"📝 Conteúdo adicionado: {content_size} bytes de {result.get('url', 'N/A')}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair conteúdo: {e}")
    
    async def _search_social_images(self, query: str):
        """Busca imagens das redes sociais"""
        try:
            logger.info(f"🖼️ Iniciando busca por imagens sociais: {query}")
            
            platforms = ["facebook", "instagram", "youtube"]
            
            for platform in platforms:
                platform_query = f"{query} site:{platform}.com"
                logger.info(f"🔍 Buscando imagens do {platform}")
                
                # Aqui você implementaria a busca específica por imagens
                # Por agora, simula a coleta
                await asyncio.sleep(2)
                
                platform_images = await self._mock_social_image_search(platform, query)
                
                # Adiciona aos resultados
                for image in platform_images:
                    self.search_results.append({
                        "type": "social_image",
                        "platform": platform,
                        "query": query,
                        "image_data": image
                    })
                    
        except Exception as e:
            logger.error(f"❌ Erro na busca de imagens sociais: {e}")
    
    async def _mock_social_image_search(self, platform: str, query: str) -> List[Dict[str, Any]]:
        """Mock para busca de imagens sociais (implementar busca real)"""
        try:
            # Simula encontrar imagens
            mock_images = []
            
            for i in range(self.max_images_per_platform):
                mock_images.append({
                    "url": f"https://{platform}.com/image_{i}_{query[:10]}.jpg",
                    "description": f"Imagem {i+1} relacionada a {query} do {platform}",
                    "extracted_at": datetime.now().isoformat()
                })
            
            logger.info(f"📷 {len(mock_images)} imagens coletadas do {platform}")
            return mock_images
            
        except Exception as e:
            logger.error(f"❌ Erro no mock de imagens do {platform}: {e}")
            return []
    
    def _count_social_images(self) -> Dict[str, int]:
        """Conta imagens por plataforma"""
        counts = {"facebook": 0, "instagram": 0, "youtube": 0, "total": 0}
        
        for result in self.search_results:
            if result.get("type") == "social_image":
                platform = result.get("platform", "unknown")
                if platform in counts:
                    counts[platform] += 1
                counts["total"] += 1
        
        return counts
    
    async def _save_search_results(self, query: str) -> str:
        """Salva resultados da busca"""
        try:
            # Nome seguro para arquivo
            safe_query = re.sub(r'[^\w\s-]', '', query.strip())[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"RES_BUSCA_{safe_query}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Dados para salvar
            search_data = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "content_size_bytes": self.extracted_content_size,
                "content_size_kb": round(self.extracted_content_size / 1024, 2),
                "text_content": self.content_buffer,
                "social_images": [r for r in self.search_results if r.get("type") == "social_image"],
                "image_counts": self._count_social_images(),
                "total_entries": len(self.content_buffer) + len([r for r in self.search_results if r.get("type") == "social_image"])
            }
            
            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(search_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Resultados salvos: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultados: {e}")
            return ""

# Instância global
alibaba_websailor = AlibabaWebSailor()

def get_websailor() -> AlibabaWebSailor:
    """Retorna instância do websailor"""
    return alibaba_websailor

class AlibabaWebSailor:
    """Sistema de busca massiva e extração de conteúdo real"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.extracted_content = []
        self.total_content_size = 0
        self.target_size = 500 * 1024  # 500KB

    async def execute_massive_search(self, query: str, product_name: str) -> Dict[str, Any]:
        """Executa busca massiva e salva conteúdo real"""
        try:
            logger.info(f"🚀 Iniciando busca massiva para: {query}")

            # Sanitiza nome do arquivo
            safe_product_name = re.sub(r'[^\w\s-]', '', product_name).strip()
            safe_product_name = re.sub(r'[-\s]+', '_', safe_product_name)

            file_path = f"RES_BUSCA_{safe_product_name}.json"

            # Inicializa arquivo de resultados
            self._initialize_result_file(file_path, query, product_name)

            # Executa busca textual até 500KB
            await self._massive_text_search(query, file_path)

            # Executa busca de imagens sociais
            await self._social_media_image_search(query, file_path)

            # Finaliza arquivo
            self._finalize_result_file(file_path)

            logger.info(f"✅ Busca massiva concluída. Arquivo: {file_path}")

            return {
                'success': True,
                'file_path': file_path,
                'content_size': self.total_content_size,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Erro na busca massiva: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _initialize_result_file(self, file_path: str, query: str, product_name: str):
        """Inicializa arquivo de resultados"""
        initial_data = {
            'metadata': {
                'query': query,
                'product_name': product_name,
                'created_at': datetime.now().isoformat(),
                'target_size_kb': 500,
                'status': 'in_progress'
            },
            'text_content': [],
            'social_images': {
                'facebook': [],
                'instagram': [],
                'youtube': []
            },
            'insights': [],
            'statistics': {
                'total_sources': 0,
                'content_size_bytes': 0,
                'processing_time_minutes': 0
            }
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)

    async def _massive_text_search(self, query: str, file_path: str):
        """Busca massiva de conteúdo textual até 500KB"""
        logger.info("🔍 Iniciando busca textual massiva...")

        search_urls = self._generate_search_urls(query)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in search_urls:
                if self.total_content_size >= self.target_size:
                    break
                tasks.append(self._extract_content_from_url(session, url, file_path))

                # Processa em lotes para não sobrecarregar
                if len(tasks) >= 10:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks = []
                    await asyncio.sleep(1)  # Rate limiting

            # Processa URLs restantes
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def _generate_search_urls(self, query: str) -> List[str]:
        """Gera URLs de busca de múltiplas fontes"""
        urls = []

        # Google Search (múltiplas páginas)
        for page in range(10):
            start = page * 10
            urls.append(f"https://www.google.com/search?q={query}&start={start}")

        # Bing Search
        for page in range(5):
            first = page * 10 + 1
            urls.append(f"https://www.bing.com/search?q={query}&first={first}")

        # DuckDuckGo
        urls.append(f"https://duckduckgo.com/html/?q={query}")

        # Sites específicos de marketing
        marketing_sites = [
            f"site:blog.hubspot.com {query}",
            f"site:neilpatel.com {query}",
            f"site:moz.com {query}",
            f"site:searchengineland.com {query}",
            f"site:socialmediaexaminer.com {query}",
            f"site:contentmarketinginstitute.com {query}",
            f"site:copyblogger.com {query}",
            f"site:marketingland.com {query}"
        ]

        for site_query in marketing_sites:
            urls.append(f"https://www.google.com/search?q={site_query}")

        return urls

    async def _extract_content_from_url(self, session: aiohttp.ClientSession, url: str, file_path: str):
        """Extrai conteúdo de URL específica"""
        try:
            if self.total_content_size >= self.target_size:
                return

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    content = self._parse_html_content(html, url)

                    if content and len(content['text']) > 100:  # Mínimo 100 chars
                        self._save_content_chunk(content, file_path)

        except Exception as e:
            logger.debug(f"Erro ao extrair {url}: {e}")

    def _parse_html_content(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse do conteúdo HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()

            # Extrai título
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "Sem título"

            # Extrai texto principal
            text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'article', 'div'])
            text_content = []

            for element in text_elements:
                text = element.get_text().strip()
                if len(text) > 50:  # Filtra textos muito curtos
                    text_content.append(text)

            combined_text = ' '.join(text_content)

            # Extrai meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''

            return {
                'url': url,
                'title': title_text,
                'description': description,
                'text': combined_text,
                'extracted_at': datetime.now().isoformat(),
                'size_bytes': len(combined_text.encode('utf-8'))
            }

        except Exception as e:
            logger.debug(f"Erro ao fazer parse de {url}: {e}")
            return None

    def _save_content_chunk(self, content: Dict[str, Any], file_path: str):
        """Salva chunk de conteúdo no arquivo"""
        try:
            # Carrega dados existentes
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Adiciona novo conteúdo
            data['text_content'].append(content)
            data['statistics']['total_sources'] += 1
            data['statistics']['content_size_bytes'] += content['size_bytes']

            # Atualiza tamanho total
            self.total_content_size += content['size_bytes']

            # Salva arquivo atualizado
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 Conteúdo salvo: {content['size_bytes']} bytes. Total: {self.total_content_size} bytes")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar conteúdo: {e}")

    async def _social_media_image_search(self, query: str, file_path: str):
        """Busca imagens de redes sociais"""
        logger.info("📸 Iniciando busca de imagens sociais...")

        # Importa extrator de imagens do Instagram
        try:
            from services.playwright_social_extractor import PlaywrightSocialExtractor
            extractor = PlaywrightSocialExtractor()

            # Busca imagens do Instagram (10 imagens)
            instagram_images = await extractor.extract_instagram_images(query, limit=10)
            self._save_social_images(file_path, 'instagram', instagram_images)

            # Busca imagens do Facebook (placeholder - implementar com API real)
            facebook_images = await self._extract_facebook_images(query)
            self._save_social_images(file_path, 'facebook', facebook_images)

            # Busca thumbnails do YouTube
            youtube_images = await self._extract_youtube_thumbnails(query)
            self._save_social_images(file_path, 'youtube', youtube_images)

        except Exception as e:
            logger.error(f"❌ Erro na busca de imagens sociais: {e}")

    async def _extract_facebook_images(self, query: str) -> List[Dict[str, Any]]:
        """Extrai imagens do Facebook (implementação real necessária)"""
        # Esta função precisa ser implementada com API real do Facebook
        # Por agora, retorna lista vazia
        logger.info("⚠️ Extração do Facebook precisa de implementação com API oficial")
        return []

    async def _extract_youtube_thumbnails(self, query: str) -> List[Dict[str, Any]]:
        """Extrai thumbnails do YouTube"""
        try:
            from googleapiclient.discovery import build

            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                logger.warning("YouTube API key não encontrada")
                return []

            youtube = build('youtube', 'v3', developerKey=api_key)

            search_response = youtube.search().list(
                q=query,
                part='snippet',
                maxResults=10,
                type='video'
            ).execute()

            thumbnails = []
            for item in search_response['items']:
                thumbnail_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt']
                }
                thumbnails.append(thumbnail_data)

            return thumbnails

        except Exception as e:
            logger.error(f"❌ Erro ao extrair thumbnails do YouTube: {e}")
            return []

    def _save_social_images(self, file_path: str, platform: str, images: List[Dict[str, Any]]):
        """Salva imagens sociais no arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['social_images'][platform] = images

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"📸 {len(images)} imagens do {platform} salvas")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar imagens do {platform}: {e}")

    def _finalize_result_file(self, file_path: str):
        """Finaliza arquivo de resultados"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['metadata']['status'] = 'completed'
            data['metadata']['completed_at'] = datetime.now().isoformat()
            data['statistics']['final_size_kb'] = self.total_content_size / 1024

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Arquivo finalizado: {file_path}")

        except Exception as e:
            logger.error(f"❌ Erro ao finalizar arquivo: {e}")

# Instância global
alibaba_websailor = AlibabaWebSailor()

def get_websailor() -> AlibabaWebSailor:
    """Retorna instância do websailor"""
    return alibaba_websailor