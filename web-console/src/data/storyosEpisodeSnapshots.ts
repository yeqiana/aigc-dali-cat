// 历史 Episode 证据兼容入口；多个静态子包保持原始顺序与内容。
import { EPISODE_PART_1 } from './storyosEpisodePart1';
import { EPISODE_PART_2 } from './storyosEpisodePart2';
import { EPISODE_PART_3 } from './storyosEpisodePart3';
export const REAL_EPISODES = [...EPISODE_PART_1, ...EPISODE_PART_2, ...EPISODE_PART_3];
