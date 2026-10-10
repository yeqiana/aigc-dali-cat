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
    bgApp: '#0c1119',
    bgWorkspace: '#111923',
    bgSurface: '#141d29',
    bgElevated: '#1a2634',
    bgHover: '#1b2a3a',
    bgSelected: '#21344b',
    borderSubtle: '#263342',
    borderNormal: '#354557',
    borderStrong: '#4a5d72',
    textPrimary: '#edf3f9',
    textSecondary: '#aebccb',
    textTertiary: '#8b9bab',
    textDisabled: '#6c7b8c',
    success: '#3FB950',
    warning: '#D29922',
    retry: '#E3A008',
    danger: '#F85149',
    info: '#72aaff',
  },
  light: {
    bgApp: '#f7f9fc',
    bgWorkspace: '#ffffff',
    bgSurface: '#ffffff',
    bgElevated: '#f5f7fa',
    bgHover: '#eef3f9',
    bgSelected: '#e9f0fb',
    borderSubtle: '#e0e7f0',
    borderNormal: '#cad5e2',
    borderStrong: '#aab8c9',
    textPrimary: '#172333',
    textSecondary: '#526278',
    textTertiary: '#65758b',
    textDisabled: '#98A2B0',
    success: '#1A7F37',
    warning: '#9A6700',
    retry: '#BC4C00',
    danger: '#CF222E',
    info: '#326fcd',
  },
  'light-gradient': {
    bgApp: '#f5f8fd',
    bgWorkspace: '#ffffff',
    bgSurface: '#ffffff',
    bgElevated: '#f3f7fc',
    bgHover: '#edf3fb',
    bgSelected: '#e7f0fc',
    borderSubtle: '#dce6f1',
    borderNormal: '#c6d4e6',
    borderStrong: '#94A3B8',
    textPrimary: '#182638',
    textSecondary: '#50617a',
    textTertiary: '#62748d',
    textDisabled: '#94A3B8',
    success: '#16A34A',
    warning: '#D97706',
    retry: '#EA580C',
    danger: '#DC2626',
    info: '#2563EB',
  },
};
