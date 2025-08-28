#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Playwright Social Extractor
Extração real de imagens do Instagram usando Playwright
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re

try:
    from playwright.async_api import async_playwright, Browser, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logging.warning("Playwright não disponível")

logger = logging.getLogger(__name__)

class PlaywrightSocialExtractor:
    """Extrator de conteúdo social usando Playwright"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context = None
        self.playwright = None
        self.headless = os.getenv('PLAYWRIGHT_HEADLESS', 'True').lower() == 'true'
        self.timeout = int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000'))

    async def __aenter__(self):
        """Context manager entry"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close_browser()

    async def start_browser(self):
        """Inicia o browser Playwright"""
        if not HAS_PLAYWRIGHT:
            raise Exception("Playwright não está instalado")

        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR'
            )
            logger.info("✅ Browser Playwright iniciado")
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
            logger.info("✅ Browser fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar browser: {e}")

    async def extract_instagram_images(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extrai imagens do Instagram baseado na query"""
        if not self.browser:
            await self.start_browser()

        try:
            page = await self.context.new_page()

            # Navega para Instagram (busca via Google)
            search_url = f"https://www.google.com/search?q=site:instagram.com {query}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)

            # Espera carregar
            await page.wait_for_timeout(3000)

            # Busca links do Instagram
            instagram_links = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="instagram.com"]'));
                    return links.map(link => link.href)
                        .filter(href => href.includes('/p/') || href.includes('/reel/'))
                        .slice(0, 15);
                }
            ''')

            images_data = []

            for link in instagram_links[:limit]:
                try:
                    image_data = await self._extract_single_instagram_post(page, link)
                    if image_data:
                        images_data.append(image_data)
                        logger.info(f"📸 Imagem extraída do Instagram: {link}")

                    await page.wait_for_timeout(2000)  # Rate limiting

                except Exception as e:
                    logger.debug(f"Erro ao extrair {link}: {e}")
                    continue

            await page.close()
            logger.info(f"✅ {len(images_data)} imagens do Instagram extraídas")
            return images_data

        except Exception as e:
            logger.error(f"❌ Erro na extração do Instagram: {e}")
            return []

    async def _extract_single_instagram_post(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de um post específico do Instagram"""
        try:
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await page.wait_for_timeout(3000)

            # Extrai dados do post
            post_data = await page.evaluate('''
                () => {
                    // Busca imagem principal
                    const img = document.querySelector('article img') ||
                              document.querySelector('img[style*="object-fit"]') ||
                              document.querySelector('div[role="img"] img');

                    // Busca caption/texto
                    const caption = document.querySelector('article span') ||
                                  document.querySelector('[data-testid="caption"]') ||
                                  document.querySelector('span');

                    // Busca autor
                    const author = document.querySelector('header a') ||
                                 document.querySelector('[data-testid="username"]');

                    return {
                        image_url: img ? img.src : null,
                        alt_text: img ? img.alt : null,
                        caption: caption ? caption.textContent : null,
                        author: author ? author.textContent : null,
                        likes: document.querySelector('[data-testid="like-count"]')?.textContent || null
                    };
                }
            ''')

            if post_data['image_url']:
                return {
                    'platform': 'instagram',
                    'post_url': url,
                    'image_url': post_data['image_url'],
                    'alt_text': post_data['alt_text'] or '',
                    'caption': post_data['caption'] or '',
                    'author': post_data['author'] or '',
                    'likes': post_data['likes'] or '',
                    'extracted_at': datetime.now().isoformat()
                }

            return None

        except Exception as e:
            logger.debug(f"Erro ao extrair post {url}: {e}")
            return None

    async def extract_facebook_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extrai posts do Facebook (implementação básica)"""
        # Facebook requer autenticação, implementação limitada
        logger.warning("⚠️ Extração do Facebook limitada sem autenticação")
        return []

    async def extract_youtube_thumbnails(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extrai thumbnails do YouTube baseado na query"""
        if not self.browser:
            await self.start_browser()

        try:
            page = await self.context.new_page()

            # Navega para YouTube (busca via Google)
            search_url = f"https://www.google.com/search?q=site:youtube.com {query}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)

            # Espera carregar
            await page.wait_for_timeout(3000)

            # Busca links do YouTube
            youtube_links = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="youtube.com/watch?v="]'));
                    return links.map(link => link.href)
                        .slice(0, 15);
                }
            ''')

            thumbnails_data = []

            for link in youtube_links[:limit]:
                try:
                    thumbnail_data = await self._extract_single_youtube_video(page, link)
                    if thumbnail_data:
                        thumbnails_data.append(thumbnail_data)
                        logger.info(f"🎥 Thumbnail extraído do YouTube: {link}")

                    await page.wait_for_timeout(2000)  # Rate limiting

                except Exception as e:
                    logger.debug(f"Erro ao extrair {link}: {e}")
                    continue

            await page.close()
            logger.info(f"✅ {len(thumbnails_data)} thumbnails do YouTube extraídos")
            return thumbnails_data

        except Exception as e:
            logger.error(f"❌ Erro na extração do YouTube: {e}")
            return []

    async def _extract_single_youtube_video(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de um vídeo específico do YouTube"""
        try:
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await page.wait_for_timeout(3000)

            # Extrai dados do vídeo
            video_data = await page.evaluate('''
                () => {
                    const thumbnail = document.querySelector('img[alt="Thumbnail"]') ||
                                      document.querySelector('img[src*="ytimg.com"]');
                    const title = document.querySelector('h1.title') ||
                                  document.querySelector('yt-formatted-string[class="title style-scope ytd-video-primary-info-renderer"]');
                    const author = document.querySelector('yt-formatted-string[class="style-scope ytd-channel-name"] a') ||
                                   document.querySelector('link[itemprop="name"]') ||
                                   document.querySelector('[data-testid="owner-name"] a');

                    return {
                        thumbnail_url: thumbnail ? thumbnail.src : null,
                        title: title ? title.textContent.trim() : null,
                        author: author ? author.textContent.trim() : null
                    };
                }
            ''')

            if video_data['thumbnail_url']:
                return {
                    'platform': 'youtube',
                    'video_url': url,
                    'thumbnail_url': video_data['thumbnail_url'],
                    'title': video_data['title'] or '',
                    'author': video_data['author'] or '',
                    'extracted_at': datetime.now().isoformat()
                }

            return None

        except Exception as e:
            logger.debug(f"Erro ao extrair vídeo {url}: {e}")
            return None

    async def extract_tiktok_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extrai conteúdo do TikTok baseado na query"""
        if not self.browser:
            await self.start_browser()

        try:
            page = await self.context.new_page()

            # Navega para TikTok (busca via Google)
            search_url = f"https://www.google.com/search?q=site:tiktok.com {query}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)

            # Espera carregar
            await page.wait_for_timeout(3000)

            # Busca links do TikTok
            tiktok_links = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="tiktok.com/@"]'));
                    return links.map(link => link.href)
                        .filter(href => href.includes('/video/'))
                        .slice(0, 15);
                }
            ''')

            content_data = []

            for link in tiktok_links[:limit]:
                try:
                    item_data = await self._extract_single_tiktok_post(page, link)
                    if item_data:
                        content_data.append(item_data)
                        logger.info(f"🎵 Conteúdo extraído do TikTok: {link}")

                    await page.wait_for_timeout(2000)  # Rate limiting

                except Exception as e:
                    logger.debug(f"Erro ao extrair {link}: {e}")
                    continue

            await page.close()
            logger.info(f"✅ {len(content_data)} conteúdos do TikTok extraídos")
            return content_data

        except Exception as e:
            logger.error(f"❌ Erro na extração do TikTok: {e}")
            return []

    async def _extract_single_tiktok_post(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de um post específico do TikTok"""
        try:
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await page.wait_for_timeout(3000)

            # Extrai dados do post
            post_data = await page.evaluate('''
                () => {
                    const video = document.querySelector('video');
                    const description = document.querySelector('h2[data-e2e="browse-video-desc"] p') ||
                                        document.querySelector('[data-e2e="video-desc"] p');
                    const author = document.querySelector('h3[data-e2e="browse-user-name"] a, h3[data-e2e="video-author-uniqueid"] a');

                    return {
                        video_url: video ? video.src : null,
                        image_url: video ? video.poster : null, # Usa o poster como imagem fallback
                        description: description ? description.textContent : null,
                        author: author ? author.textContent : null
                    };
                }
            ''')

            if post_data['image_url'] or post_data['video_url']:
                return {
                    'platform': 'tiktok',
                    'post_url': url,
                    'image_url': post_data['image_url'] or post_data['video_url'], # Prioriza poster, fallback para src do vídeo
                    'description': post_data['description'] or '',
                    'author': post_data['author'] or '',
                    'extracted_at': datetime.now().isoformat()
                }
            return None

        except Exception as e:
            logger.debug(f"Erro ao extrair post {url}: {e}")
            return None

    async def search_visual_content_all(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Busca conteúdo visual em todas as plataformas suportadas"""
        results = {
            'instagram': [],
            'facebook': [],
            'youtube': [],
            'tiktok': []
        }

        try:
            # Executa extrações em paralelo
            tasks = [
                self.extract_instagram_images(query, limit),
                self.extract_facebook_posts(query, limit),
                self.extract_youtube_thumbnails(query, limit),
                self.extract_tiktok_content(query, limit)
            ]
            
            extracted_data = await asyncio.gather(*tasks)

            results['instagram'] = extracted_data[0]
            results['facebook'] = extracted_data[1]
            results['youtube'] = extracted_data[2]
            results['tiktok'] = extracted_data[3]

            logger.info(f"🔍 Busca visual completa para: {query}")
            return results

        except Exception as e:
            logger.error(f"❌ Erro na busca visual geral: {e}")
            return results

# Instância global
playwright_extractor = PlaywrightSocialExtractor()

async def extract_social_images(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Função helper para extrair imagens sociais"""
    async with PlaywrightSocialExtractor() as extractor:
        return await extractor.extract_instagram_images(query, limit)

async def extract_youtube_content(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Função helper para extrair thumbnails do YouTube"""
    async with PlaywrightSocialExtractor() as extractor:
        return await extractor.extract_youtube_thumbnails(query, limit)

async def extract_tiktok_visuals(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Função helper para extrair conteúdo visual do TikTok"""
    async with PlaywrightSocialExtractor() as extractor:
        return await extractor.extract_tiktok_content(query, limit)

async def search_all_visual_content(query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Função principal para busca de conteúdo visual em todas as plataformas"""
    async with PlaywrightSocialExtractor() as extractor:
        return await extractor.search_visual_content_all(query, limit)

if __name__ == "__main__":
    # Teste rápido
    async def test_extraction():
        query = "digital marketing trends"
        print(f"\n--- Testando Extração do Instagram para: '{query}' ---")
        insta_images = await extract_social_images(query, 5)
        print(f"Instagram: {len(insta_images)} imagens encontradas.")
        # print(json.dumps(insta_images, indent=2))

        print(f"\n--- Testando Extração do YouTube para: '{query}' ---")
        youtube_content = await extract_youtube_content(query, 5)
        print(f"YouTube: {len(youtube_content)} thumbnails encontrados.")
        # print(json.dumps(youtube_content, indent=2))

        print(f"\n--- Testando Extração do TikTok para: '{query}' ---")
        tiktok_content = await extract_tiktok_visuals(query, 5)
        print(f"TikTok: {len(tiktok_content)} conteúdos encontrados.")
        # print(json.dumps(tiktok_content, indent=2))

        print(f"\n--- Testando Busca Visual Geral para: '{query}' ---")
        all_content = await search_all_visual_content(query, 5)
        print(f"Busca Geral: Instagram={len(all_content['instagram'])}, YouTube={len(all_content['youtube'])}, TikTok={len(all_content['tiktok'])}")
        # print(json.dumps(all_content, indent=2))

    asyncio.run(test_extraction())