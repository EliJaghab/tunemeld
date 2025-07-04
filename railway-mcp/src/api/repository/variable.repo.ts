import { RailwayApiClient } from "@/api/api-client.js";
import { Variable, VariableUpsertInput, VariableDeleteInput, VariablesResponse } from "@/types.js";

export class VariableRepository {
  constructor(private client: RailwayApiClient) {}

  async getVariables(projectId: string, environmentId: string, serviceId?: string): Promise<Record<string, string>> {
    const data = await this.client.request<VariablesResponse>(
      `
      query variables($projectId: String!, $environmentId: String!, $serviceId: String) {
        variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
      }
    `,
      { projectId, environmentId, serviceId }
    );

    return data.variables || {};
  }

  async upsertVariable(input: VariableUpsertInput): Promise<void> {
    const { projectId, environmentId, serviceId, name, value } = input;
    await this.client.request<{ variableUpsert: boolean }>(
      `
      mutation variableUpsert(
        $projectId: String!,
        $environmentId: String!,
        $serviceId: String,
        $name: String!,
        $value: String!
      ) {
        variableUpsert(
          input: {
            projectId: $projectId,
            environmentId: $environmentId,
            serviceId: $serviceId,
            name: $name,
            value: $value
          }
        )
      }
    `,
      { projectId, environmentId, serviceId, name, value }
    );
  }

  async upsertVariables(inputs: VariableUpsertInput[]): Promise<void> {
    // Process variables in batches to avoid overwhelming the API
    const batchSize = 10;
    for (let i = 0; i < inputs.length; i += batchSize) {
      const batch = inputs.slice(i, i + batchSize);
      await Promise.all(batch.map(input => this.upsertVariable(input)));
    }
  }

  async deleteVariable(input: VariableDeleteInput): Promise<void> {
    const { projectId, environmentId, serviceId, name } = input;
    await this.client.request<{ variableDelete: boolean }>(
      `
      mutation variableDelete(
        $projectId: String!,
        $environmentId: String!,
        $serviceId: String,
        $name: String!
      ) {
        variableDelete(
          input: {
            projectId: $projectId,
            environmentId: $environmentId,
            serviceId: $serviceId,
            name: $name
          }
        )
      }
    `,
      { projectId, environmentId, serviceId, name }
    );
  }

  async listVariables(serviceId: string, environmentId: string): Promise<Variable[]> {
    const data = await this.client.request<{ variables: Variable[] }>(
      `
      query variables($serviceId: String!, $environmentId: String!) {
        variables(serviceId: $serviceId, environmentId: $environmentId)
      }
    `,
      { serviceId, environmentId }
    );

    return data.variables || [];
  }
}
