import genresConfig from "../shared/genres.json";
import servicesConfig from "../shared/services.json";
import playlistsConfig from "../shared/playlists.json";
import constantsConfig from "../shared/constants.json";

const environment = process.env.NODE_ENV || "development";
let envConfig;

try {
  envConfig = require(`../environments/${environment}.json`);
} catch (error) {
  envConfig = require("../environments/development.json");
}

class TuneMeldConfig {
  constructor() {
    this.environment = environment;
    this.envConfig = envConfig;
    this.genres = genresConfig.genres;
    this.services = servicesConfig.services;
    this.playlists = playlistsConfig.playlists;
    this.constants = constantsConfig;
  }

  getGenres() {
    return this.genres;
  }

  getDefaultGenre() {
    return this.genres.find(genre => genre.default)?.id || "pop";
  }

  getServices() {
    return this.services;
  }

  getService(serviceId) {
    return this.services[serviceId];
  }

  getPlaylistUrl(service, genre) {
    return this.playlists[service]?.playlists[genre]?.url;
  }

  getApiBaseUrl() {
    return this.envConfig.api.django.baseUrl;
  }

  getCloudflareUrl() {
    return this.envConfig.api.cloudflare.baseUrl;
  }

  isProduction() {
    return this.environment === "production";
  }

  isDevelopment() {
    return this.environment === "development";
  }

  getTheme(isDark = false) {
    return isDark ? this.constants.ui.themes.dark : this.constants.ui.themes.light;
  }

  getCdnUrl(service) {
    return this.constants.external.cdnUrls[service];
  }

  getServiceColor(serviceId) {
    return this.services[serviceId]?.color;
  }

  getEmbedUrl(serviceId) {
    return this.services[serviceId]?.embedUrl;
  }

  getUrlPattern(serviceId) {
    return new RegExp(this.services[serviceId]?.urlPattern);
  }

  getMobileBreakpoint() {
    return this.constants.ui.mobileBreakpoint;
  }

  getDarkModeHours() {
    return this.constants.ui.darkModeHours;
  }

  getViewCountTypes() {
    return this.constants.ui.viewCountTypes;
  }

  getDefaultSort() {
    return this.constants.ui.defaultSort;
  }

  getGoogleAdsId() {
    return this.constants.external.googleAds.publisherId;
  }

  getExternalLink(linkId) {
    return this.constants.external.links[linkId];
  }
}

export const config = new TuneMeldConfig();
export default config;
