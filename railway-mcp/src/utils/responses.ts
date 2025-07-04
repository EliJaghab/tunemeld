import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export interface CommandResponse {
  content: Array<{
    type: "text";
    text: string;
  }>;
  data?: unknown;
  isError?: boolean;
}

export function createSuccessResponse(response: { text: string; data?: unknown }): CallToolResult {
  return {
    content: [
      {
        type: "text",
        text: response.text,
      },
    ],
    data: response.data,
  };
}

export function createErrorResponse(message: string): CallToolResult {
  return {
    content: [
      {
        type: "text",
        text: message,
      },
    ],
    isError: true,
  };
}

export function formatError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}
