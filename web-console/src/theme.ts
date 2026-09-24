/**
 * StoryOS Centralized Theme Tokens & Color System
 * 统一主题色中枢：所有颜色契约在此处单点定义
 */

export interface ThemeColors {
  bgApp: string;
  bgWorkspace: string;
  bgSurface: string;
  bgElevated: string;
  bgHover: string;
  bgSelected: string;
  borderSubtle: string;
  borderNormal: string;
  borderStrong: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textDisabled: string;
  success: string;
  warning: string;
  retry: string;
  danger: string;
  info: string;
}

export const THEME_PALETTES: Record<'dark' | 'light' | 'light-gradient', ThemeColors> = {
  dark: {
    bgApp: '#0B0D10',
    bgWorkspace: '#0F1115',
    bgSurface: '#13161B',
    bgElevated: '#171B21',
    bgHover: '#1B2027',
    bgSelected: '#20262E',
    borderSubtle: '#232830',
    borderNormal: '#2D333D',
    borderStrong: '#3A424E',
    textPrimary: '#F1F3F5',
    textSecondary: '#A7AFBA',
    textTertiary: '#737D8A',
    textDisabled: '#505864',
    success: '#3FB950',
    warning: '#D29922',
    retry: '#E3A008',
    danger: '#F85149',
    info: '#58A6FF',
  },
  light: {
    bgApp: '#F6F8FA',
    bgWorkspace: '#FFFFFF',
    bgSurface: '#FFFFFF',
    bgElevated: '#FFFFFF',
    bgHover: '#E9EEF4',
    bgSelected: '#DEE5EE',
    borderSubtle: '#E2E6EA',
    borderNormal: '#CFD6DE',
    borderStrong: '#B0B8C2',
    textPrimary: '#1A1F26',
    textSecondary: '#4A5462',
    textTertiary: '#6E7987',
    textDisabled: '#98A2B0',
    success: '#1A7F37',
    warning: '#9A6700',
    retry: '#BC4C00',
    danger: '#CF222E',
    info: '#0969DA',
  },
  'light-gradient': {
    bgApp: '#F4F7FC',
    bgWorkspace: 'rgba(255, 255, 255, 0.88)',
    bgSurface: 'rgba(255, 255, 255, 0.94)',
    bgElevated: '#FFFFFF',
    bgHover: 'rgba(235, 242, 252, 0.88)',
    bgSelected: 'rgba(223, 232, 246, 0.92)',
    borderSubtle: 'rgba(210, 222, 238, 0.85)',
    borderNormal: '#CBD5E1',
    borderStrong: '#94A3B8',
    textPrimary: '#0F172A',
    textSecondary: '#334155',
    textTertiary: '#64748B',
    textDisabled: '#94A3B8',
    success: '#16A34A',
    warning: '#D97706',
    retry: '#EA580C',
    danger: '#DC2626',
    info: '#2563EB',
  },
};
