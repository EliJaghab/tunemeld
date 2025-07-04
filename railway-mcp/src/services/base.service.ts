import { RailwayApiClient, railwayClient } from "@/api/api-client.js";

export class BaseService {
  protected client: RailwayApiClient;

  constructor() {
    this.client = railwayClient;
  }
}
