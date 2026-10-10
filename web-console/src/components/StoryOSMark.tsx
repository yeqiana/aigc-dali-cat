import React from 'react';
// 与 favicon.svg 同源图形，避免浏览器和侧栏品牌不一致。
export const StoryOSMark: React.FC<{size?: number}> = ({size=32}) => (
  <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="StoryOS">
    <rect width="64" height="64" rx="12" fill="#111827"/>
    <path d="M42 18H28c-7 0-11 4-11 10s4 10 11 10h9c6 0 10 4 10 9s-4 9-11 9H21" fill="none" stroke="#F4F8FE" strokeWidth="7.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M46 12v13" fill="none" stroke="#78B4FF" strokeWidth="5.5" strokeLinecap="round"/>
  </svg>
);
