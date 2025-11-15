import React, { createContext, useContext } from "react";
import type { ServiceMetadata, ServiceName } from "@/v2/constants";

export const ServiceMetadataContext = createContext<Record<
  ServiceName,
  ServiceMetadata
> | null>(null);

export const ServiceMetadataProvider = ({
  children,
  value,
}: {
  children: React.ReactNode;
  value: Record<ServiceName, ServiceMetadata>;
}): React.ReactElement => (
  <ServiceMetadataContext.Provider value={value}>
    {children}
  </ServiceMetadataContext.Provider>
);

export const useServiceMetadata = (): Record<
  ServiceName,
  ServiceMetadata
> | null => useContext(ServiceMetadataContext);
