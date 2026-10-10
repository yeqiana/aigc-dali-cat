import type { StoryRunItem } from '../types';
export function isHistoricalRunIndex(run: StoryRunItem): boolean {return (run as StoryRunItem & {__indexOnly?: boolean}).__indexOnly === true;}
const loaders: Record<string, () => Promise<StoryRunItem>> = {
  "run-09-04": () => import('./runDetail01').then(m=>m.RUN_DETAIL),
  "run-09-05": () => import('./runDetail02').then(m=>m.RUN_DETAIL),
  "run-10-01": () => import('./runDetail03').then(m=>m.RUN_DETAIL),
  "run-10-B01": () => import('./runDetail04').then(m=>m.RUN_DETAIL),
  "run-10-02": () => import('./runDetail05').then(m=>m.RUN_DETAIL),
  "run-11-01": () => import('./runDetail06').then(m=>m.RUN_DETAIL),
  "run-11-01-RE": () => import('./runDetail07').then(m=>m.RUN_DETAIL),
  "run-MR-01": () => import('./runDetail08').then(m=>m.RUN_DETAIL),
  "run-TJ-01": () => import('./runDetail09').then(m=>m.RUN_DETAIL),
  "run-JN-01": () => import('./runDetail10').then(m=>m.RUN_DETAIL),
  "run-误入桃花源": () => import('./runDetail11').then(m=>m.RUN_DETAIL),
};
export function loadHistoricalRunDetail(id: string): Promise<StoryRunItem> { const load=loaders[id];return load?load():Promise.reject(new Error('缺少此 Run 历史详情'));}
