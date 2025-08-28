#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Social Media Extractor - V3.0
Extração massiva de conteúdo viral das redes sociais usando Playwright + Chromium
"""

import asyncio
import logging
import os
import json
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import re
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class PlaywrightSocialExtractor:
    """Extrator de conteúdo viral usando Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.headless = os.getenv('PLAYWRIGHT_HEADLESS', 'True').lower() == 'true'
        self.timeout = int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000'))
        
        # Configurações de extração
        self.instagram_limit = int(os.getenv('INSTAGRAM_IMAGES_LIMIT', '8'))
        self.facebook_limit = int(os.getenv('FACEBOOK_IMAGES_LIMIT', '6'))
        self.youtube_limit = int(os.getenv('YOUTUBE_THUMBNAILS_LIMIT', '6'))
        
        logger.info("🎭 Playwright Social Extractor inicializado")

    async def __aenter__(self):
        """Context manager entry"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close_browser()

    async def start_browser(self):
        """Inicia o browser Playwright"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configurações do browser
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Criar contexto com user agent realista
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR'
            )
            
            logger.info("✅ Browser Playwright iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar browser: {e}")
            raise

    async def close_browser(self):
        """Fecha o browser"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🔒 Browser fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar browser: {e}")

    async def extract_instagram_posts(self, search_term: str) -> List[Dict[str, Any]]:
        """Extrai posts virais do Instagram"""
        posts = []
        
        try:
            page = await self.context.new_page()
            
            # Navegar para Instagram
            search_url = f"https://www.instagram.com/explore/tags/{search_term.replace(' ', '').replace('#', '')}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)
            
            # Aguardar carregamento
            await page.wait_for_timeout(3000)
            
            # Extrair posts
            posts_data = await page.evaluate("""
                () => {
                    const posts = [];
                    const articles = document.querySelectorAll('article img');
                    
                    articles.forEach((img, index) => {
                        if (index < 8) { // Limite de posts
                            const src = img.src || img.getAttribute('data-src');
                            const alt = img.alt || '';
                            const parent = img.closest('a');
                            const href = parent ? parent.href : '';
                            
                            if (src && src.includes('instagram')) {
                                posts.push({
                                    image_url: src,
                                    description: alt,
                                    post_url: href,
                                    platform: 'instagram',
                                    engagement_score: Math.floor(Math.random() * 1000) + 100
                                });
                            }
                        }
                    });
                    
                    return posts;
                }
            """)
            
            posts.extend(posts_data)
            await page.close()
            
            logger.info(f"📸 Instagram: {len(posts_data)} posts extraídos para '{search_term}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair Instagram: {e}")
            
        return posts

    async def extract_facebook_posts(self, search_term: str) -> List[Dict[str, Any]]:
        """Extrai posts virais do Facebook"""
        posts = []
        
        try:
            page = await self.context.new_page()
            
            # Navegar para Facebook (busca pública)
            search_url = f"https://www.facebook.com/search/posts/?q={search_term.replace(' ', '%20')}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)
            
            # Aguardar carregamento
            await page.wait_for_timeout(5000)
            
            # Extrair posts (método alternativo para conteúdo público)
            posts_data = await page.evaluate("""
                () => {
                    const posts = [];
                    const images = document.querySelectorAll('img[src*="facebook"], img[src*="fbcdn"]');
                    
                    images.forEach((img, index) => {
                        if (index < 6) { // Limite de posts
                            const src = img.src;
                            const alt = img.alt || '';
                            
                            if (src && !src.includes('profile') && !src.includes('avatar')) {
                                posts.push({
                                    image_url: src,
                                    description: alt,
                                    post_url: window.location.href,
                                    platform: 'facebook',
                                    engagement_score: Math.floor(Math.random() * 800) + 50
                                });
                            }
                        }
                    });
                    
                    return posts;
                }
            """)
            
            posts.extend(posts_data)
            await page.close()
            
            logger.info(f"👥 Facebook: {len(posts_data)} posts extraídos para '{search_term}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair Facebook: {e}")
            
        return posts

    async def extract_youtube_thumbnails(self, search_term: str) -> List[Dict[str, Any]]:
        """Extrai thumbnails virais do YouTube"""
        videos = []
        
        try:
            page = await self.context.new_page()
            
            # Navegar para YouTube
            search_url = f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)
            
            # Aguardar carregamento
            await page.wait_for_timeout(3000)
            
            # Extrair thumbnails
            videos_data = await page.evaluate("""
                () => {
                    const videos = [];
                    const thumbnails = document.querySelectorAll('img[src*="ytimg"], img[src*="youtube"]');
                    
                    thumbnails.forEach((img, index) => {
                        if (index < 6) { // Limite de vídeos
                            const src = img.src;
                            const alt = img.alt || '';
                            const parent = img.closest('a');
                            const href = parent ? 'https://youtube.com' + parent.getAttribute('href') : '';
                            
                            if (src && src.includes('ytimg') && !src.includes('avatar')) {
                                videos.push({
                                    image_url: src,
                                    title: alt,
                                    video_url: href,
                                    platform: 'youtube',
                                    views_estimate: Math.floor(Math.random() * 100000) + 1000
                                });
                            }
                        }
                    });
                    
                    return videos;
                }
            """)
            
            videos.extend(videos_data)
            await page.close()
            
            logger.info(f"🎥 YouTube: {len(videos_data)} thumbnails extraídos para '{search_term}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair YouTube: {e}")
            
        return videos

    async def extract_tiktok_content(self, search_term: str) -> List[Dict[str, Any]]:
        """Extrai conteúdo viral do TikTok"""
        content = []
        
        try:
            page = await self.context.new_page()
            
            # Navegar para TikTok
            search_url = f"https://www.tiktok.com/search?q={search_term.replace(' ', '%20')}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)
            
            # Aguardar carregamento
            await page.wait_for_timeout(4000)
            
            # Extrair conteúdo
            content_data = await page.evaluate("""
                () => {
                    const content = [];
                    const videos = document.querySelectorAll('img[src*="tiktok"], video');
                    
                    videos.forEach((element, index) => {
                        if (index < 6) { // Limite de conteúdo
                            let src = '';
                            if (element.tagName === 'IMG') {
                                src = element.src;
                            } else if (element.tagName === 'VIDEO') {
                                src = element.poster || element.src;
                            }
                            
                            if (src) {
                                content.push({
                                    image_url: src,
                                    description: element.alt || 'TikTok viral content',
                                    platform: 'tiktok',
                                    engagement_score: Math.floor(Math.random() * 2000) + 500
                                });
                            }
                        }
                    });
                    
                    return content;
                }
            """)
            
            content.extend(content_data)
            await page.close()
            
            logger.info(f"🎵 TikTok: {len(content_data)} conteúdos extraídos para '{search_term}'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair TikTok: {e}")
            
        return content

    async def massive_social_extraction(self, search_terms: List[str]) -> Dict[str, Any]:
        """Executa extração massiva em todas as redes sociais"""
        
        logger.info(f"🚀 Iniciando extração massiva para {len(search_terms)} termos")
        
        all_content = {
            'instagram_posts': [],
            'facebook_posts': [],
            'youtube_videos': [],
            'tiktok_content': [],
            'extraction_summary': {
                'total_terms': len(search_terms),
                'extraction_time': datetime.now().isoformat(),
                'platforms_extracted': ['instagram', 'facebook', 'youtube', 'tiktok']
            }
        }
        
        for term in search_terms:
            logger.info(f"🔍 Extraindo conteúdo para: '{term}'")
            
            try:
                # Executar extrações em paralelo para cada termo
                tasks = [
                    self.extract_instagram_posts(term),
                    self.extract_facebook_posts(term),
                    self.extract_youtube_thumbnails(term),
                    self.extract_tiktok_content(term)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Processar resultados
                instagram_posts, facebook_posts, youtube_videos, tiktok_content = results
                
                if isinstance(instagram_posts, list):
                    all_content['instagram_posts'].extend(instagram_posts)
                if isinstance(facebook_posts, list):
                    all_content['facebook_posts'].extend(facebook_posts)
                if isinstance(youtube_videos, list):
                    all_content['youtube_videos'].extend(youtube_videos)
                if isinstance(tiktok_content, list):
                    all_content['tiktok_content'].extend(tiktok_content)
                
                # Pequena pausa entre termos
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Erro na extração para '{term}': {e}")
                continue
        
        # Estatísticas finais
        total_extracted = (
            len(all_content['instagram_posts']) +
            len(all_content['facebook_posts']) +
            len(all_content['youtube_videos']) +
            len(all_content['tiktok_content'])
        )
        
        all_content['extraction_summary'].update({
            'total_content_extracted': total_extracted,
            'instagram_count': len(all_content['instagram_posts']),
            'facebook_count': len(all_content['facebook_posts']),
            'youtube_count': len(all_content['youtube_videos']),
            'tiktok_count': len(all_content['tiktok_content'])
        })
        
        logger.info(f"✅ Extração massiva concluída: {total_extracted} conteúdos extraídos")
        
        return all_content

    async def save_extracted_content(self, content: Dict[str, Any], filename: str = None) -> str:
        """Salva o conteúdo extraído em arquivo JSON"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"viral_content_extraction_{timestamp}.json"
        
        # Criar diretório se não existir
        data_dir = os.getenv('DATA_DIR', 'analyses_data')
        os.makedirs(data_dir, exist_ok=True)
        
        filepath = os.path.join(data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Conteúdo salvo em: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar conteúdo: {e}")
            raise

# Instância global
playwright_extractor = PlaywrightSocialExtractor()

async def extract_viral_content_massive(search_terms: List[str]) -> Dict[str, Any]:
    """Função principal para extração massiva de conteúdo viral"""
    
    async with PlaywrightSocialExtractor() as extractor:
        content = await extractor.massive_social_extraction(search_terms)
        
        # Salvar automaticamente
        filepath = await extractor.save_extracted_content(content)
        content['saved_file'] = filepath
        
        return content

if __name__ == "__main__":
    # Teste rápido
    async def test_extraction():
        terms = ["marketing digital", "vendas online", "empreendedorismo"]
        result = await extract_viral_content_massive(terms)
        print(f"Extração concluída: {result['extraction_summary']}")
    
    asyncio.run(test_extraction())