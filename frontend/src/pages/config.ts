export function liveViewEnabled() {
  return !import.meta.env.MULTI_USER_ENABLED;
}
