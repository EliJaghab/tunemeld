import { handleGraphData, handleServicePlaylist, handleMainPlaylist, handleLastUpdated, handleHeaderArt } from './apiHandlers';
import { handleError, handleOptions } from './utils';

export default {
    async fetch(request: Request, env: any): Promise<Response> {
        const url = new URL(request.url);
        const pathname = url.pathname;

        if (pathname === '/') {

            return new Response('Welcome to the homepage!', {
              headers: { 'Content-Type': 'text/plain' },
            });
          }

        if (pathname.startsWith('/api/')) {
            if (request.method === 'OPTIONS') {
                return handleOptions(request);
            }

            const cache = caches.default;
            let response = await cache.match(request);
            if (response) {
                return response;
            }

            try {
                const searchParams = url.searchParams;
                switch (pathname) {
                    case '/api/graph-data':
                        response = await handleGraphData(searchParams, env);
                        break;
                    case '/api/service-playlist':
                        response = await handleServicePlaylist(searchParams, env);
                        break;
                    case '/api/main-playlist':
                        response = await handleMainPlaylist(searchParams, env);
                        break;
                    case '/api/last-updated':
                        response = await handleLastUpdated(searchParams, env);
                        break;
                    case '/api/header-art':
                        response = await handleHeaderArt(searchParams, env);
                        break;
                    default:
                        response = new Response('Not Found', {
                            status: 404,
                            headers: { 'Access-Control-Allow-Origin': '*' }
                        });
                }
                
                if (response.status === 200) {
                    await cache.put(request, response.clone());
                }

                return response;
            } catch (error) {
                return handleError(error);
            }
        }

        return fetch(request);
    },
};
