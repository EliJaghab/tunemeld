import React, { createContext, useContext } from "react";
import {
  DEFAULT_SERVICE_METADATA,
  type ServiceMetadata,
  type ServiceName,
} from "@/v2/constants";

export const ServiceMetadataContext = createContext<
  Record<ServiceName, ServiceMetadata>
>(DEFAULT_SERVICE_METADATA);

export const ServiceMetadataProvider = ({
  children,
  value = DEFAULT_SERVICE_METADATA,
}: {
  children: React.ReactNode;
  value?: Record<ServiceName, ServiceMetadata>;
}): React.ReactElement => (
  <ServiceMetadataContext.Provider value={value}>
    {children}
  </ServiceMetadataContext.Provider>
);

export const useServiceMetadata = (): Record<ServiceName, ServiceMetadata> =>
  useContext(ServiceMetadataContext);
