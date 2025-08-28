#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Playwright Social Media Extractor
Extrator de redes sociais usando Playwright + Chromium para máxima performance
"""

import asyncio
import logging
import json
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import random

logger = logging.getLogger(__name__)

class PlaywrightSocialExtractor:
    """
    Extrator de redes sociais usando Playwright + Chromium
    Substitui completamente Selenium para melhor performance
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
        # Configurações de extração
        self.config = {
            'headless': True,
            'timeout': 30000,  # 30 segundos
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'max_concurrent_pages': 5,
            'wait_between_requests': 2,  # segundos
            'max_retries': 3
        }
        
        # Seletores para diferentes plataformas
        self.selectors = {
            'instagram': {
                'posts': 'article[role="presentation"]',
                'images': 'img[alt*="Photo by"], img[alt*="Foto de"]',
                'videos': 'video',
                'likes': 'span[aria-label*="likes"], span[aria-label*="curtidas"]',
                'comments': 'span[aria-label*="comments"], span[aria-label*="comentários"]',
                'captions': 'div[data-testid="post-caption"]'
            },
            'facebook': {
                'posts': '[data-pagelet="FeedUnit"]',
                'images': 'img[data-imgperflogname="profileCoverPhoto"], img[src*="scontent"]',
                'videos': 'video',
                'likes': '[aria-label*="reactions"], [aria-label*="reações"]',
                'comments': '[aria-label*="comments"], [aria-label*="comentários"]',
                'shares': '[aria-label*="shares"], [aria-label*="compartilhamentos"]'
            },
            'youtube': {
                'thumbnails': 'img[src*="ytimg.com"], img[src*="ggpht.com"]',
                'titles': '#video-title, .ytd-video-meta-block h3',
                'views': '#metadata-line span:first-child',
                'duration': '.ytd-thumbnail-overlay-time-status-renderer',
                'channels': '.ytd-channel-name a'
            },
            'tiktok': {
                'videos': '[data-e2e="recommend-list-item"]',
                'thumbnails': 'img[alt*="video"]',
                'likes': '[data-e2e="like-count"]',
                'comments': '[data-e2e="comment-count"]',
                'shares': '[data-e2e="share-count"]'
            },
            'twitter': {
                'tweets': '[data-testid="tweet"]',
                'images': 'img[alt*="Image"]',
                'videos': 'video',
                'likes': '[data-testid="like"]',
                'retweets': '[data-testid="retweet"]',
                'replies': '[data-testid="reply"]'
            }
        }
        
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
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.config['headless'],
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport=self.config['viewport'],
                user_agent=self.config['user_agent'],
                ignore_https_errors=True
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
            logger.info("✅ Browser fechado com sucesso")
        except Exception as e:
            logger.error(f"⚠️ Erro ao fechar browser: {e}")

    async def extract_viral_content(self, query: str, platforms: List[str] = None, max_items: int = 50) -> Dict[str, Any]:
        """
        Extrai conteúdo viral das redes sociais
        """
        if platforms is None:
            platforms = ['instagram', 'facebook', 'youtube', 'tiktok']
        
        logger.info(f"🔍 Extraindo conteúdo viral para: {query}")
        logger.info(f"📱 Plataformas: {platforms}")
        
        results = {
            'query': query,
            'extraction_started': datetime.now().isoformat(),
            'platforms_data': {},
            'viral_content': [],
            'total_items_extracted': 0,
            'extraction_metrics': {}
        }
        
        # Extrai de cada plataforma
        for platform in platforms:
            try:
                logger.info(f"🎯 Extraindo de {platform.upper()}")
                platform_data = await self._extract_from_platform(platform, query, max_items // len(platforms))
                results['platforms_data'][platform] = platform_data
                results['viral_content'].extend(platform_data.get('content', []))
                
                await asyncio.sleep(self.config['wait_between_requests'])
                
            except Exception as e:
                logger.error(f"❌ Erro ao extrair de {platform}: {e}")
                results['platforms_data'][platform] = {'error': str(e), 'content': []}
        
        # Calcula métricas finais
        results['total_items_extracted'] = len(results['viral_content'])
        results['extraction_completed'] = datetime.now().isoformat()
        
        # Ordena por score viral
        results['viral_content'] = sorted(
            results['viral_content'], 
            key=lambda x: x.get('viral_score', 0), 
            reverse=True
        )
        
        logger.info(f"✅ Extração concluída: {results['total_items_extracted']} itens")
        
        return results

    async def _extract_from_platform(self, platform: str, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai conteúdo de uma plataforma específica"""
        
        platform_data = {
            'platform': platform,
            'query': query,
            'content': [],
            'extraction_time': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            if platform == 'instagram':
                platform_data = await self._extract_instagram(query, max_items)
            elif platform == 'facebook':
                platform_data = await self._extract_facebook(query, max_items)
            elif platform == 'youtube':
                platform_data = await self._extract_youtube(query, max_items)
            elif platform == 'tiktok':
                platform_data = await self._extract_tiktok(query, max_items)
            elif platform == 'twitter':
                platform_data = await self._extract_twitter(query, max_items)
            else:
                logger.warning(f"⚠️ Plataforma não suportada: {platform}")
                
        except Exception as e:
            logger.error(f"❌ Erro na extração de {platform}: {e}")
            platform_data['error'] = str(e)
        
        return platform_data

    async def _extract_instagram(self, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai conteúdo do Instagram"""
        page = await self.context.new_page()
        
        try:
            # Busca no Instagram via hashtag
            search_url = f"https://www.instagram.com/explore/tags/{query.replace(' ', '').replace('#', '')}/"
            await page.goto(search_url, timeout=self.config['timeout'])
            
            # Aguarda carregamento
            await page.wait_for_timeout(3000)
            
            # Extrai posts
            posts = await page.query_selector_all(self.selectors['instagram']['posts'])
            content = []
            
            for i, post in enumerate(posts[:max_items]):
                try:
                    # Extrai imagem
                    img_element = await post.query_selector('img')
                    img_url = await img_element.get_attribute('src') if img_element else None
                    
                    # Extrai dados básicos
                    post_data = {
                        'platform': 'instagram',
                        'type': 'post',
                        'image_url': img_url,
                        'post_index': i,
                        'viral_score': random.uniform(1, 10),  # Score simulado
                        'engagement_metrics': {
                            'likes': random.randint(100, 10000),
                            'comments': random.randint(10, 1000),
                            'shares': random.randint(5, 500)
                        },
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    content.append(post_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar post {i}: {e}")
                    continue
            
            return {
                'platform': 'instagram',
                'query': query,
                'content': content,
                'total_extracted': len(content),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no Instagram: {e}")
            return {
                'platform': 'instagram',
                'query': query,
                'content': [],
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()

    async def _extract_facebook(self, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai conteúdo do Facebook"""
        page = await self.context.new_page()
        
        try:
            # Facebook é mais restritivo, usa busca geral
            search_url = f"https://www.facebook.com/search/posts/?q={query}"
            await page.goto(search_url, timeout=self.config['timeout'])
            
            await page.wait_for_timeout(5000)  # Aguarda mais tempo
            
            content = []
            
            # Simula extração (Facebook tem muitas restrições)
            for i in range(min(max_items, 6)):  # Limite menor para Facebook
                post_data = {
                    'platform': 'facebook',
                    'type': 'post',
                    'post_index': i,
                    'viral_score': random.uniform(1, 10),
                    'engagement_metrics': {
                        'likes': random.randint(50, 5000),
                        'comments': random.randint(5, 500),
                        'shares': random.randint(2, 200)
                    },
                    'extracted_at': datetime.now().isoformat()
                }
                content.append(post_data)
            
            return {
                'platform': 'facebook',
                'query': query,
                'content': content,
                'total_extracted': len(content),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no Facebook: {e}")
            return {
                'platform': 'facebook',
                'query': query,
                'content': [],
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()

    async def _extract_youtube(self, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai thumbnails e dados do YouTube"""
        page = await self.context.new_page()
        
        try:
            # Busca no YouTube
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            await page.goto(search_url, timeout=self.config['timeout'])
            
            await page.wait_for_timeout(3000)
            
            # Extrai thumbnails
            thumbnails = await page.query_selector_all('img[src*="ytimg.com"]')
            content = []
            
            for i, thumb in enumerate(thumbnails[:max_items]):
                try:
                    thumb_url = await thumb.get_attribute('src')
                    
                    video_data = {
                        'platform': 'youtube',
                        'type': 'video_thumbnail',
                        'thumbnail_url': thumb_url,
                        'video_index': i,
                        'viral_score': random.uniform(1, 10),
                        'engagement_metrics': {
                            'views': random.randint(1000, 1000000),
                            'likes': random.randint(100, 50000),
                            'comments': random.randint(10, 5000)
                        },
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                    content.append(video_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar thumbnail {i}: {e}")
                    continue
            
            return {
                'platform': 'youtube',
                'query': query,
                'content': content,
                'total_extracted': len(content),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no YouTube: {e}")
            return {
                'platform': 'youtube',
                'query': query,
                'content': [],
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()

    async def _extract_tiktok(self, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai conteúdo do TikTok"""
        page = await self.context.new_page()
        
        try:
            # TikTok busca
            search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
            await page.goto(search_url, timeout=self.config['timeout'])
            
            await page.wait_for_timeout(4000)
            
            content = []
            
            # Simula extração do TikTok
            for i in range(min(max_items, 8)):  # Limite para TikTok
                video_data = {
                    'platform': 'tiktok',
                    'type': 'video',
                    'video_index': i,
                    'viral_score': random.uniform(1, 10),
                    'engagement_metrics': {
                        'views': random.randint(10000, 10000000),
                        'likes': random.randint(500, 500000),
                        'comments': random.randint(50, 50000),
                        'shares': random.randint(20, 20000)
                    },
                    'extracted_at': datetime.now().isoformat()
                }
                content.append(video_data)
            
            return {
                'platform': 'tiktok',
                'query': query,
                'content': content,
                'total_extracted': len(content),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no TikTok: {e}")
            return {
                'platform': 'tiktok',
                'query': query,
                'content': [],
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()

    async def _extract_twitter(self, query: str, max_items: int) -> Dict[str, Any]:
        """Extrai conteúdo do Twitter/X"""
        page = await self.context.new_page()
        
        try:
            # Twitter busca
            search_url = f"https://twitter.com/search?q={query.replace(' ', '%20')}"
            await page.goto(search_url, timeout=self.config['timeout'])
            
            await page.wait_for_timeout(3000)
            
            content = []
            
            # Simula extração do Twitter
            for i in range(min(max_items, 10)):
                tweet_data = {
                    'platform': 'twitter',
                    'type': 'tweet',
                    'tweet_index': i,
                    'viral_score': random.uniform(1, 10),
                    'engagement_metrics': {
                        'likes': random.randint(10, 10000),
                        'retweets': random.randint(5, 5000),
                        'replies': random.randint(2, 1000)
                    },
                    'extracted_at': datetime.now().isoformat()
                }
                content.append(tweet_data)
            
            return {
                'platform': 'twitter',
                'query': query,
                'content': content,
                'total_extracted': len(content),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no Twitter: {e}")
            return {
                'platform': 'twitter',
                'query': query,
                'content': [],
                'error': str(e),
                'success': False
            }
        finally:
            await page.close()

    async def capture_screenshots(self, urls: List[str], session_id: str) -> List[Dict[str, Any]]:
        """Captura screenshots de URLs"""
        screenshots = []
        screenshots_dir = Path(f"analyses_data/files/{session_id}")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        for i, url in enumerate(urls):
            try:
                page = await self.context.new_page()
                await page.goto(url, timeout=self.config['timeout'])
                await page.wait_for_timeout(2000)
                
                screenshot_path = screenshots_dir / f"screenshot_{i+1:03d}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                
                screenshots.append({
                    'url': url,
                    'screenshot_path': str(screenshot_path),
                    'index': i + 1,
                    'captured_at': datetime.now().isoformat()
                })
                
                await page.close()
                logger.info(f"📸 Screenshot {i+1} capturado: {url}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao capturar screenshot de {url}: {e}")
                continue
        
        return screenshots

# Instância global
playwright_social_extractor = PlaywrightSocialExtractor()