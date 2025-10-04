import { getDjangoApiBaseUrl } from "@/config/config";
import { SERVICE_NAMES } from "@/config/constants";
import type {
  Genre,
  Track,
  Playlist,
  PlayCount,
  ServiceConfig,
  IframeConfig,
  Rank,
  ButtonLabel,
} from "@/types/index";

// Custom error types
interface GraphQLError {
  message: string;
  locations?: { line: number; column: number }[];
  path?: (string | number)[];
}

interface CustomError extends Error {
  details?: any;
  responseBody?: string;
  isNetworkError?: boolean;
  isHttpError?: boolean;
  graphqlErrors?: GraphQLError[];
  duration?: string;
  endpoint?: string;
  query?: string;
  variables?: any;
  isGraphqlError?: boolean;
  originalMessage?: string;
  isConnectionError?: boolean;
  isTimeoutError?: boolean;
  isUnexpectedError?: boolean;
}

class GraphQLClient {
  private endpoint: string;

  constructor() {
    this.endpoint = `${getDjangoApiBaseUrl()}/api/gql/`;
  }

  async query(
    query: string,
    variables: Record<string, any> = {},
  ): Promise<any> {
    const startTime = Date.now();

    // AGGRESSIVE DEBUG LOGGING
    const queryName = query.match(/query\s+(\w+)/)?.[1] || "UnknownQuery";
    console.log(
      `🔥 GRAPHQL REQUEST #${Math.random().toString(36).substr(2, 9)}:`,
      {
        queryName,
        variables,
        queryPreview: query.substring(0, 100) + "...",
        timestamp: new Date().toISOString(),
        stackTrace: new Error().stack?.split("\n").slice(1, 4),
      },
    );

    try {
      const headers = {
        "Content-Type": "application/json",
      };

      // Custom endpoint path for better debugging in Network tab
      const baseEndpoint = this.endpoint.replace("/api/gql/", "/api/");
      const customEndpoint = `${baseEndpoint}${queryName}/`;

      const response = await fetch(customEndpoint, {
        method: "POST",
        headers,
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
          headers: (() => {
            const headerObj: Record<string, string> = {};
            response.headers.forEach((value, key) => {
              headerObj[key] = value;
            });
            return headerObj;
          })(),
          query: query.trim(),
          variables,
        };

        let responseBody = null;
        try {
          responseBody = await response.text();
        } catch (e) {
          responseBody = "Unable to read response body";
        }

        console.error("GraphQL HTTP Error:", errorDetails);
        console.error("Response Body:", responseBody);

        const error = new Error(
          `GraphQL HTTP Error: ${response.status} ${response.statusText}`,
        ) as CustomError;
        error.details = errorDetails;
        error.responseBody = responseBody;
        error.isNetworkError = false;
        error.isHttpError = true;
        throw error;
      }

      const result = await response.json();

      if (result.errors) {
        console.error("GraphQL Query Error:", {
          errors: result.errors,
          query: query.trim(),
          variables,
          duration: duration + "ms",
        });

        const error = new Error(
          `GraphQL Query Error: ${result.errors
            .map((e: GraphQLError) => e.message)
            .join(", ")}`,
        ) as CustomError;
        error.graphqlErrors = result.errors;
        error.duration = duration + "ms";
        error.endpoint = this.endpoint;
        error.query = query.trim();
        error.variables = variables;
        error.isNetworkError = false;
        error.isGraphqlError = true;
        throw error;
      }

      return result.data;
    } catch (error: unknown) {
      const duration = Date.now() - startTime;
      const customError = error as CustomError;

      // If it's already our custom error, just add duration and re-throw
      if (customError.isNetworkError !== undefined) {
        customError.duration = duration + "ms";
        console.error("GraphQL query failed:", customError);
        throw customError;
      }

      let enhancedError: CustomError;
      if (
        customError.name === "TypeError" &&
        customError.message.includes("fetch")
      ) {
        enhancedError = new Error(
          `Network Connection Failed: Unable to reach GraphQL server at ${this.endpoint}`,
        ) as CustomError;
        enhancedError.originalMessage = customError.message;
        enhancedError.isNetworkError = true;
        enhancedError.isConnectionError = true;
      } else if (customError.name === "AbortError") {
        enhancedError = new Error(
          `Request Timeout: GraphQL query timed out after ${duration}ms`,
        ) as CustomError;
        enhancedError.originalMessage = customError.message;
        enhancedError.isNetworkError = true;
        enhancedError.isTimeoutError = true;
      } else {
        enhancedError = new Error(
          `Unexpected Error: ${customError.message}`,
        ) as CustomError;
        enhancedError.originalMessage = customError.message;
        enhancedError.isUnexpectedError = true;
      }

      enhancedError.duration = duration + "ms";
      enhancedError.endpoint = this.endpoint;
      enhancedError.stack = customError.stack || "";

      console.error("GraphQL query failed:", enhancedError);
      throw enhancedError;
    }
  }

  async getAvailableGenres(): Promise<{
    genres: Genre[];
    defaultGenre: string;
  }> {
    const query = `
      query GetAvailableGenres {
        genres {
          id
          name
          displayName
          iconUrl
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
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

  async getPlaylistMetadata(
    genre: string,
  ): Promise<{ serviceOrder: string[]; playlists: Playlist[] }> {
    const query = `
      query GetPlaylistMetadata($genre: String!) {
        serviceOrder
        playlistsByGenre(genre: $genre) {
          playlistName
          playlistCoverUrl
          playlistCoverDescriptionText
          playlistUrl
          genreName
          serviceName
          serviceIconUrl
          debugCacheStatus
        }
      }
    `;

    const data = await this.query(query, { genre });
    return {
      serviceOrder: data.serviceOrder,
      playlists: data.playlistsByGenre,
    };
  }

  async getPlaylistTracks(
    genre: string,
    service: string,
  ): Promise<{ playlist: Playlist }> {
    const query = `
      query GetPlaylistTracks($genre: String!, $service: String!) {
        playlist(genre: $genre, service: $service) {
          genreName
          serviceName
          tracks {
            tunemeldRank
            spotifyRank
            appleMusicRank
            soundcloudRank
            isrc
            trackName
            artistName
            fullTrackName
            fullArtistName
            albumName
            albumCoverUrl
            youtubeUrl
            spotifyUrl
            appleMusicUrl
            soundcloudUrl
            buttonLabels {
              buttonType
              context
              title
              ariaLabel
            }
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
            trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SPOTIFY}")
            trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
            trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
            trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.YOUTUBE}")
          }
        }
      }
    `;

    return await this.query(query, { genre, service });
  }

  async fetchPlaylistRanks(): Promise<{ ranks: Rank[] }> {
    const query = `
      query GetPlaylistRanks {
        ranks {
          name
          displayName
          sortField
          sortOrder
          isDefault
          dataField
        }
      }
    `;

    return await this.query(query);
  }

  async getPlayCountsForTracks(
    isrcs: string[],
  ): Promise<{ tracksPlayCounts: PlayCount[] }> {
    const query = `
      query GetPlayCounts($isrcs: [String!]!) {
        tracksPlayCounts(isrcs: $isrcs) {
          isrc
          youtubeCurrentPlayCount
          spotifyCurrentPlayCount
          totalCurrentPlayCount
          youtubeCurrentPlayCountAbbreviated
          spotifyCurrentPlayCountAbbreviated
          totalCurrentPlayCountAbbreviated
          totalWeeklyChangePercentage
          totalWeeklyChangePercentageFormatted
        }
      }
    `;

    return await this.query(query, { isrcs });
  }

  async getServiceConfigs(): Promise<ServiceConfig[]> {
    const query = `
      query GetServiceConfigs {
        serviceConfigs {
          name
          displayName
          iconUrl
          urlField
          sourceField
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
        }
      }
    `;

    const data = await this.query(query);
    return data.serviceConfigs;
  }

  async getIframeConfigs(): Promise<IframeConfig[]> {
    const query = `
      query GetIframeConfigs {
        iframeConfigs {
          serviceName
          embedBaseUrl
          embedParams
          allow
          height
          referrerPolicy
        }
      }
    `;

    const data = await this.query(query);
    return data.iframeConfigs;
  }

  async generateIframeUrl(
    serviceName: string,
    trackUrl: string,
  ): Promise<string> {
    const query = `
      query GenerateIframeUrl($serviceName: String!, $trackUrl: String!) {
        generateIframeUrl(serviceName: $serviceName, trackUrl: $trackUrl)
      }
    `;

    const data = await this.query(query, { serviceName, trackUrl });
    return data.generateIframeUrl;
  }

  async getRankButtonLabels(rankType: string): Promise<ButtonLabel[]> {
    const query = `
      query GetRankButtonLabels($rankType: String!) {
        rankButtonLabels(rankType: $rankType) {
          buttonType
          context
          title
          ariaLabel
        }
      }
    `;

    const data = await this.query(query, { rankType });
    return data.rankButtonLabels;
  }

  async getMiscButtonLabels(
    buttonType: string,
    context: string | null = null,
  ): Promise<ButtonLabel[]> {
    console.error(`🚨 INDIVIDUAL BUTTON CALL DETECTED!`, {
      buttonType,
      context,
      timestamp: new Date().toISOString(),
      stackTrace: new Error().stack?.split("\n").slice(1, 5),
    });
    const query = `
      query GetMiscButtonLabels($buttonType: String!, $context: String) {
        miscButtonLabels(buttonType: $buttonType, context: $context) {
          buttonType
          context
          title
          ariaLabel
        }
      }
    `;

    const data = await this.query(query, { buttonType, context });
    return data.miscButtonLabels;
  }
}

export const graphqlClient = new GraphQLClient();
