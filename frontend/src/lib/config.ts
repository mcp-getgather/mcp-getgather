export function liveViewEnabled() {
  return !import.meta.env.MULTI_USER_ENABLED;
}

export function activitiesEnabled() {
  return !import.meta.env.MULTI_USER_ENABLED;
}

export function replayEnabled() {
  return !import.meta.env.MULTI_USER_ENABLED;
}
