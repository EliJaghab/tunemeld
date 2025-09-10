import { getDjangoApiBaseUrl } from "./config.js";

class GraphQLClient {
  constructor() {
    this.endpoint = `${getDjangoApiBaseUrl()}/gql/`;
  }

  async query(query, variables = {}) {
    const startTime = Date.now();

    try {
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          variables,
        }),
      });

      const duration = Date.now() - startTime;

      if (!response.ok) {
        const errorDetails = {
          status: response.status,
          statusText: response.statusText,
          url: this.endpoint,
          duration: duration + "ms",
          headers: Object.fromEntries(response.headers.entries()),
        };

        let responseBody = null;
        try {
          responseBody = await response.text();
        } catch (e) {
          responseBody = "Unable to read response body";
        }

        const error = new Error(`GraphQL HTTP Error: ${response.status} ${response.statusText}`);
        error.details = errorDetails;
        error.responseBody = responseBody;
        error.isNetworkError = false;
        error.isHttpError = true;
        throw error;
      }

      const result = await response.json();

      if (result.errors) {
        const error = new Error(`GraphQL Query Error: ${result.errors.map(e => e.message).join(", ")}`);
        error.graphqlErrors = result.errors;
        error.duration = duration + "ms";
        error.endpoint = this.endpoint;
        error.isNetworkError = false;
        error.isGraphqlError = true;
        throw error;
      }

      return result.data;
    } catch (error) {
      const duration = Date.now() - startTime;

      // If it's already our custom error, just add duration and re-throw
      if (error.isNetworkError !== undefined) {
        error.duration = duration + "ms";
        console.error("GraphQL query failed:", error);
        throw error;
      }

      let enhancedError;
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        enhancedError = new Error(`Network Connection Failed: Unable to reach GraphQL server at ${this.endpoint}`);
        enhancedError.originalMessage = error.message;
        enhancedError.isNetworkError = true;
        enhancedError.isConnectionError = true;
      } else if (error.name === "AbortError") {
        enhancedError = new Error(`Request Timeout: GraphQL query timed out after ${duration}ms`);
        enhancedError.originalMessage = error.message;
        enhancedError.isNetworkError = true;
        enhancedError.isTimeoutError = true;
      } else {
        enhancedError = new Error(`Unexpected Error: ${error.message}`);
        enhancedError.originalMessage = error.message;
        enhancedError.isUnexpectedError = true;
      }

      enhancedError.duration = duration + "ms";
      enhancedError.endpoint = this.endpoint;
      enhancedError.stack = error.stack;

      console.error("GraphQL query failed:", enhancedError);
      throw enhancedError;
    }
  }

  async getAvailableGenres() {
    const query = `
      query GetAvailableGenres {
        genres {
          id
          name
          displayName
        }
        defaultGenre
      }
    `;

    const data = await this.query(query);
    return {
      genres: data.genres,
      defaultGenre: data.defaultGenre,
    };
  }

  async getAvailableServices() {
    const query = `
      query GetAvailableServices {
        serviceOrder
      }
    `;

    const data = await this.query(query);
    return data.serviceOrder;
  }

  async getPlaylist(genre, service) {
    const query = `
      query GetPlaylist($genre: String!, $service: String!) {
        playlist(genre: $genre, service: $service) {
          genreName
          serviceName
          tracks {
            rank(genre: $genre, service: $service)
            isrc
            trackName
            artistName
            albumName
            albumCoverUrl
            youtubeUrl
            spotifyUrl
            appleMusicUrl
            soundcloudUrl
            spotifySource {
              name
              displayName
              url
              iconUrl
            }
            appleMusicSource {
              name
              displayName
              url
              iconUrl
            }
            soundcloudSource {
              name
              displayName
              url
              iconUrl
            }
            youtubeSource {
              name
              displayName
              url
              iconUrl
            }
            viewCountDataJson
          }
        }
      }
    `;

    return await this.query(query, { genre, service });
  }

  async getLastUpdated(genre) {
    const query = `
      query GetUpdatedAt($genre: String!) {
        updatedAt(genre: $genre)
      }
    `;

    const data = await this.query(query, { genre });
    return data.updatedAt;
  }
}

export const graphqlClient = new GraphQLClient();
