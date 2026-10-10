import type { Episode } from '../types';
export const EPISODE_DETAIL_LOADERS: Record<string, () => Promise<Episode>> = {
  "ep-09-04": () => import('./episodeDetail01').then(module => module.EPISODE_DETAIL),
  "ep-09-05": () => import('./episodeDetail02').then(module => module.EPISODE_DETAIL),
  "ep-10-01": () => import('./episodeDetail03').then(module => module.EPISODE_DETAIL),
  "ep-10-B01": () => import('./episodeDetail04').then(module => module.EPISODE_DETAIL),
  "ep-10-02": () => import('./episodeDetail05').then(module => module.EPISODE_DETAIL),
  "ep-11-01": () => import('./episodeDetail06').then(module => module.EPISODE_DETAIL),
  "ep-11-01-RE": () => import('./episodeDetail07').then(module => module.EPISODE_DETAIL),
  "ep-MR-01": () => import('./episodeDetail08').then(module => module.EPISODE_DETAIL),
  "ep-TJ-01": () => import('./episodeDetail09').then(module => module.EPISODE_DETAIL),
  "ep-JN-01": () => import('./episodeDetail10').then(module => module.EPISODE_DETAIL),
  "ep-误入桃花源": () => import('./episodeDetail11').then(module => module.EPISODE_DETAIL),
};
export function isHistoricalEpisodeIndex(ep: Episode): boolean { return (ep as Episode & {__indexOnly?: boolean}).__indexOnly === true; }
export function loadHistoricalEpisodeDetail(id: string): Promise<Episode> {
  const load = EPISODE_DETAIL_LOADERS[id];
  return load ? load() : Promise.reject(new Error('该作品没有历史详情模块'));
}
