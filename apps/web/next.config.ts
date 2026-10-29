import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Cache Components (Next 16's experimental PPR-successor) isn't needed
   * here yet — every route is fixture-driven, not fetching real data until
   * M5 wires the API. Off for now rather than fighting its Suspense
   * requirements for no benefit. */
};

export default nextConfig;
