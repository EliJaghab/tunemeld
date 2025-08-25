import { getDjangoApiBaseUrl } from "./config.js";

class GraphQLClient {
  constructor() {
    this.endpoint = `${getDjangoApiBaseUrl()}/gql/`;
  }

  async query(query, variables = {}) {
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

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.errors) {
        throw new Error(`GraphQL error: ${result.errors.map(e => e.message).join(", ")}`);
      }

      return result.data;
    } catch (error) {
      console.error("GraphQL query failed:", error);
      throw error;
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
}

export const graphqlClient = new GraphQLClient();
