import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useMediaPlayerStore } from "@/v2/stores/useMediaPlayerStore";

export function useTrackUrlSync() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { setUrlUpdateCallback, syncFromUrl } = useMediaPlayerStore();

  useEffect(() => {
    const updateUrlFromStore = (params: URLSearchParams) => {
      setSearchParams(params, { replace: false });
    };

    setUrlUpdateCallback(updateUrlFromStore);

    return () => {
      setUrlUpdateCallback(null);
    };
  }, [setUrlUpdateCallback, setSearchParams]);

  useEffect(() => {
    syncFromUrl(searchParams);
  }, [searchParams, syncFromUrl]);
}
