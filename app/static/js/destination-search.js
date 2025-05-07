/**
 * Destination Search Library
 * 
 * Provides client-side integration with destination search APIs.
 * Performs parallel searches across multiple sources and combines results.
 */

const DestinationSearch = (function() {
    'use strict';

    // Default configuration
    const DEFAULT_CONFIG = {
        sources: ['database', 'google', 'openstreetmap'],
        prioritize: 'database',
        limit: 8,
        timeout: 5000, // 5 seconds
        minQueryLength: 2,
        cacheLifetime: 5 * 60 * 1000 // 5 minutes in milliseconds
    };

    // API endpoints for each source
    const ENDPOINTS = {
        database: '/api/destinations/database/',
        google: '/api/destinations/google-places/',
        openstreetmap: '/api/destinations/openstreetmap/'
    };

    // In-memory cache for search results
    const cache = {
        // Structure: { 
        //   'query-source': {
        //     timestamp: Date.now(),
        //     results: [...]
        //   }
        // }
        data: {},
        
        /**
         * Set cache entry
         * @param {string} query - The search query
         * @param {string} source - The data source
         * @param {Array} results - The search results
         */
        set: function(query, source, results) {
            const key = `${query}-${source}`;
            this.data[key] = {
                timestamp: Date.now(),
                results: results
            };
        },
        
        /**
         * Get cache entry if valid
         * @param {string} query - The search query
         * @param {string} source - The data source
         * @param {number} lifetime - Max age in milliseconds
         * @returns {Array|null} The cached results or null if not found/expired
         */
        get: function(query, source, lifetime) {
            const key = `${query}-${source}`;
            const entry = this.data[key];
            
            if (!entry) return null;
            
            // Check if entry is expired
            const age = Date.now() - entry.timestamp;
            if (age > lifetime) {
                delete this.data[key];
                return null;
            }
            
            return entry.results;
        },
        
        /**
         * Clear all cache entries
         */
        clear: function() {
            this.data = {};
        }
    };

    /**
     * Fetch results from a specific source with timeout
     * @param {string} query - The search query
     * @param {string} source - The data source to search
     * @param {number} timeout - Timeout in milliseconds
     * @param {number} cacheLifetime - Cache lifetime in milliseconds
     * @returns {Promise<Array>} Promise that resolves to search results
     */
    async function fetchSourceWithTimeout(query, source, timeout, cacheLifetime) {
        // First check cache
        const cachedResults = cache.get(query, source, cacheLifetime);
        if (cachedResults) {
            console.log(`Using cached results for ${query} from ${source}`);
            return cachedResults;
        }
        
        // Create the endpoint URL
        const endpoint = ENDPOINTS[source];
        if (!endpoint) {
            console.error(`Unknown source: ${source}`);
            return [];
        }
        
        const url = `${endpoint}?query=${encodeURIComponent(query)}`;
        
        // Create a promise that will reject after timeout
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error(`Request to ${source} timed out`)), timeout);
        });
        
        try {
            // Race between the fetch and the timeout
            const response = await Promise.race([
                fetch(url),
                timeoutPromise
            ]);
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status} from ${source}`);
            }
            
            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(`API error from ${source}: ${data.message || 'Unknown error'}`);
            }
            
            // Filter for cities and countries for Google and OpenStreetMap
            let filteredResults = data.results;
            if (source === 'google' || source === 'openstreetmap') {
                filteredResults = data.results.filter(item => item.type === 'city' || item.type === 'country');
            }
            // Cache the results
            cache.set(query, source, filteredResults);
            
            return filteredResults;
        } catch (error) {
            console.warn(`Error fetching from ${source}:`, error.message);
            return [];
        }
    }

    /**
     * Deduplicate results from multiple sources, prioritizing certain sources
     * @param {Object} resultsBySource - Object mapping sources to their results
     * @param {string} prioritySource - Source to prioritize during deduplication
     * @param {number} limit - Maximum number of results to return
     * @returns {Array} Deduplicated results
     */
    function deduplicateResults(resultsBySource, prioritySource, limit) {
        // First, flatten all results into a single array with source information
        let allResults = [];
        for (const source in resultsBySource) {
            const sourceResults = resultsBySource[source];
            allResults = allResults.concat(sourceResults);
        }
        
        // Use a map to deduplicate by name + country
        const dedupMap = new Map();
        
        // Process results from priority source first
        if (resultsBySource[prioritySource]) {
            resultsBySource[prioritySource].forEach(result => {
                const key = (result.name + '-' + (result.country || '')).toLowerCase();
                dedupMap.set(key, result);
            });
        }
        
        // Then process other sources
        for (const source in resultsBySource) {
            if (source === prioritySource) continue;
            
            resultsBySource[source].forEach(result => {
                const key = (result.name + '-' + (result.country || '')).toLowerCase();
                // Only add if not already added from priority source
                if (!dedupMap.has(key)) {
                    dedupMap.set(key, result);
                }
            });
        }
        
        // Convert back to array and limit results
        return Array.from(dedupMap.values()).slice(0, limit);
    }

    return {
        /**
         * Search for destinations across multiple sources
         * @param {string} query - The search query
         * @param {Object} options - Search options
         * @returns {Promise<Array>} Promise that resolves to search results
         */
        search: async function(query, options = {}) {
            // Merge default config with provided options
            const config = { ...DEFAULT_CONFIG, ...options };
            
            // Validate query
            if (!query || query.length < config.minQueryLength) {
                console.warn(`Query too short (min: ${config.minQueryLength})`);
                return [];
            }
            
            // Normalize query to trim whitespace
            query = query.trim();
            
            // Start parallel requests to all specified sources
            const sources = config.sources.filter(source => ENDPOINTS[source]);
            
            if (sources.length === 0) {
                console.warn('No valid sources specified');
                return [];
            }
            
            console.log(`Searching for "${query}" across sources:`, sources);
            
            const sourcePromises = {};
            sources.forEach(source => {
                sourcePromises[source] = fetchSourceWithTimeout(
                    query, 
                    source, 
                    config.timeout,
                    config.cacheLifetime
                );
            });
            
            // Wait for all promises to settle (either resolve or reject)
            const results = await Promise.all(
                Object.keys(sourcePromises).map(source => 
                    sourcePromises[source]
                        .then(data => ({ source, data }))
                        .catch(error => ({ source, error }))
                )
            );
            
            // Organize results by source
            const resultsBySource = {};
            results.forEach(result => {
                resultsBySource[result.source] = result.data || [];
            });
            
            // Deduplicate and limit results
            const finalResults = deduplicateResults(
                resultsBySource,
                config.prioritize,
                config.limit
            );
            
            console.log(`Found ${finalResults.length} unique destinations for "${query}"`);
            return finalResults;
        },
        
        /**
         * Search all sources (convenience method)
         * @param {string} query - The search query
         * @returns {Promise<Array>} Promise that resolves to search results
         */
        searchAll: function(query) {
            return this.search(query);
        },
        
        /**
         * Search only local database (convenience method)
         * @param {string} query - The search query
         * @returns {Promise<Array>} Promise that resolves to search results
         */
        searchLocal: function(query) {
            return this.search(query, { sources: ['database'] });
        },
        
        /**
         * Clear the results cache
         */
        clearCache: function() {
            cache.clear();
        }
    };
})(); 